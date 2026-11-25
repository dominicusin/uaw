"""
State Manager for UAW — transactional SQLite/WAL persistence.

The previous implementation rewrote a JSON file on every mutation, without a
transaction, lock or crash recovery. This version keeps the same public API and
adds: WAL journal, synchronous=FULL, per-operation commits, a re-entrant lock,
legacy state.json migration and a compatibility layer for WorkflowState.
"""

import json
import os
import sqlite3
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class StateType(Enum):
    WORKFLOW = "workflow"
    RESOURCE_MAPPING = "resource_mapping"
    EXECUTION_CONTEXT = "execution_context"
    USER_PREFERENCES = "user_preferences"
    AUDIT_LOG = "audit_log"


@dataclass
class StateEntry:
    key: str
    value: Any
    state_type: StateType
    created_at: str
    updated_at: str
    ttl: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "state_type": self.state_type.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateEntry":
        return cls(
            key=data["key"],
            value=data["value"],
            state_type=StateType(data["state_type"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            ttl=data.get("ttl"),
        )


@dataclass
class WorkflowState:
    """Compatibility shape used by the original test suite and callers."""

    workflow_id: str
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    pending_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = field(default_factory=lambda: datetime.utcnow())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        data = dict(data)
        for k in ("created_at", "updated_at"):
            v = data.get(k)
            if isinstance(v, str):
                data[k] = datetime.fromisoformat(v)
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in allowed})


class StateManager:
    """Persistent state with atomic writes and crash recovery."""

    def __init__(self, state_dir: Optional[Union[str, Path]] = None):
        if state_dir is None:
            state_dir = os.getenv(
                "UAW_STATE_DIR", str(Path.home() / ".local" / "state" / "uaw")
            )
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.state_dir / "state.sqlite3"
        self._lock = threading.RLock()
        self._cache: Dict[str, StateEntry] = {}
        self._conn = sqlite3.connect(
            str(self.db_path), check_same_thread=False, timeout=30
        )
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=FULL")
            self._conn.execute("PRAGMA busy_timeout=30000")
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS state (
                       key TEXT PRIMARY KEY,
                       value TEXT NOT NULL,
                       state_type TEXT NOT NULL,
                       created_at TEXT NOT NULL,
                       updated_at TEXT NOT NULL,
                       ttl INTEGER
                   )"""
            )
            self._conn.commit()
            self._migrate_legacy()
            self._load_state()

    # ------------------------------------------------------------------ storage
    def _migrate_legacy(self) -> None:
        legacy = self.state_dir / "state.json"
        if not legacy.exists():
            return
        count = self._conn.execute("SELECT COUNT(*) FROM state").fetchone()[0]
        if count:
            return
        try:
            with open(legacy, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            with self._conn:
                for item in data.get("entries", []):
                    self._insert(StateEntry.from_dict(item))
        except Exception as exc:  # legacy file is kept; never destroyed
            print(f"Warning: legacy state migration failed: {exc}")

    def _insert(self, entry: StateEntry) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO state
               (key, value, state_type, created_at, updated_at, ttl)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                entry.key,
                json.dumps(entry.value, ensure_ascii=False),
                entry.state_type.value,
                entry.created_at,
                entry.updated_at,
                entry.ttl,
            ),
        )

    def _load_state(self) -> None:
        with self._lock:
            rows = self._conn.execute(
                "SELECT key, value, state_type, created_at, updated_at, ttl FROM state"
            ).fetchall()
            for key, value, stype, created, updated, ttl in rows:
                self._cache[key] = StateEntry(
                    key=key,
                    value=json.loads(value),
                    state_type=StateType(stype),
                    created_at=created,
                    updated_at=updated,
                    ttl=ttl,
                )

    def _save_state(self) -> None:
        """Kept for API compatibility. Writes the cache as one transaction."""
        with self._lock:
            with self._conn:
                for entry in self._cache.values():
                    self._insert(entry)

    def close(self) -> None:
        with self._lock:
            self._conn.commit()
            self._conn.close()

    # ---------------------------------------------------------------------- API
    def set(self, key: str, value: Any,
            state_type: StateType = StateType.WORKFLOW,
            ttl: Optional[int] = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        entry = StateEntry(key, value, state_type, now, now, ttl)
        with self._lock:
            with self._conn:
                self._insert(entry)
            self._cache[key] = entry

    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry and entry.ttl:
            created = datetime.fromisoformat(entry.created_at)
            if (datetime.now(timezone.utc) - created).total_seconds() > entry.ttl:
                self.delete(key)
                return None
        return entry.value if entry else None

    def get_entry(self, key: str) -> Optional[StateEntry]:
        entry = self._cache.get(key)
        if entry and entry.ttl:
            created = datetime.fromisoformat(entry.created_at)
            if (datetime.now(timezone.utc) - created).total_seconds() > entry.ttl:
                self.delete(key)
                return None
        return entry

    def delete(self, key: str) -> bool:
        with self._lock:
            if key not in self._cache:
                return False
            with self._conn:
                self._conn.execute("DELETE FROM state WHERE key = ?", (key,))
            del self._cache[key]
            return True

    def exists(self, key: str) -> bool:
        return key in self._cache

    def list_entries(self, state_type: Optional[StateType] = None) -> List[StateEntry]:
        entries = list(self._cache.values())
        return [e for e in entries if e.state_type == state_type] if state_type else entries

    def clear(self, state_type: Optional[StateType] = None) -> int:
        keys = [e.key for e in self.list_entries(state_type)]
        with self._lock:
            with self._conn:
                if state_type:
                    self._conn.execute(
                        "DELETE FROM state WHERE state_type = ?", (state_type.value,)
                    )
                else:
                    self._conn.execute("DELETE FROM state")
            for key in keys:
                self._cache.pop(key, None)
        return len(keys)

    def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        return self.get(workflow_id)

    def save_workflow_state(self, workflow_id: str, state: Dict[str, Any]) -> None:
        self.set(workflow_id, state, StateType.WORKFLOW, ttl=86400)

    def get_resource_mapping(self, mapping_id: str) -> Optional[Dict[str, Any]]:
        return self.get(f"mapping_{mapping_id}")

    def save_resource_mapping(self, mapping_id: str, mapping: Dict[str, Any]) -> None:
        self.set(f"mapping_{mapping_id}", mapping, StateType.RESOURCE_MAPPING)

    def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        expired = []
        for key, entry in self._cache.items():
            if entry.ttl:
                created = datetime.fromisoformat(entry.created_at)
                if (now - created).total_seconds() > entry.ttl:
                    expired.append(key)
        for key in expired:
            self.delete(key)
        return len(expired)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_entries": len(self._cache),
            "by_type": {
                st.value: sum(1 for e in self._cache.values() if e.state_type == st)
                for st in StateType
            },
            "backend": "sqlite-wal",
        }

    # --------------------------------------------------- WorkflowState compat API
    def save_state(self, workflow_id: str, state: WorkflowState) -> None:
        self.set(f"workflow:{workflow_id}", state.to_dict(), StateType.WORKFLOW)

    def get_state(self, workflow_id: str) -> Optional[WorkflowState]:
        raw = self.get(f"workflow:{workflow_id}")
        return WorkflowState.from_dict(raw) if raw else None

    def delete_state(self, workflow_id: str) -> bool:
        return self.delete(f"workflow:{workflow_id}")

    def list_states(self) -> List[WorkflowState]:
        out = []
        for entry in self.list_entries(StateType.WORKFLOW):
            if isinstance(entry.key, str) and entry.key.startswith("workflow:"):
                out.append(WorkflowState.from_dict(entry.value))
        return out

    def cleanup_expired_states(self, ttl_days: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(days=ttl_days)
        stale = [
            e.key for e in self.list_entries(StateType.WORKFLOW)
            if isinstance(e.key, str) and e.key.startswith("workflow:")
            and datetime.fromisoformat(e.updated_at.replace("Z", "+00:00")) < cutoff
        ]
        for key in stale:
            self.delete(key)
        return len(stale)
