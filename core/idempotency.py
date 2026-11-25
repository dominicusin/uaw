"""Idempotency keys with lease-based recovery, backed by SQLite/WAL."""
import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


class IdempotencyInProgress(RuntimeError):
    """Another caller owns this key and its lease has not expired."""


class IdempotencyFailure(RuntimeError):
    """A previous execution of this key failed; its error is replayed."""


@dataclass
class IdempotencyRecord:
    key: str
    status: str
    result: Any
    error: Optional[str]
    created_at: str
    lease_until: str


class IdempotencyStore:
    """Run a write operation at most once per key.

    A key is reserved in a committed transaction before the operation starts,
    with a lease. A crashed worker's lease expires and a later call takes over.
    """

    def __init__(self, state_dir=None, lease_seconds: int = 300):
        if state_dir is None:
            state_dir = Path.home() / ".local" / "state" / "uaw" / "idempotency"
        self.db_path = Path(state_dir) / "idempotency.sqlite3"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lease_seconds = lease_seconds
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=30)
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=FULL")
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS idempotency (
                       key TEXT PRIMARY KEY,
                       status TEXT NOT NULL,
                       result TEXT,
                       error TEXT,
                       created_at TEXT NOT NULL,
                       lease_until TEXT NOT NULL
                   )"""
            )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.commit()
            self._conn.close()

    def get(self, key: str) -> Optional[IdempotencyRecord]:
        row = self._conn.execute(
            "SELECT key,status,result,error,created_at,lease_until FROM idempotency WHERE key=?",
            (key,),
        ).fetchone()
        if not row:
            return None
        return IdempotencyRecord(
            key=row[0], status=row[1],
            result=json.loads(row[2]) if row[2] is not None else None,
            error=row[3], created_at=row[4], lease_until=row[5],
        )

    def run(self, key: str, operation: Callable[[], T]) -> T:
        now = datetime.now(timezone.utc)
        lease_until = (now + timedelta(seconds=self.lease_seconds)).isoformat()
        with self._lock:
            with self._conn:
                row = self.get(key)
                if row is None:
                    self._conn.execute(
                        """INSERT INTO idempotency(key,status,result,error,created_at,lease_until)
                           VALUES (?, 'in_progress', NULL, NULL, ?, ?)""",
                        (key, now.isoformat(), lease_until),
                    )
                    acquired = True
                elif row.status == "done":
                    return row.result
                elif row.status == "failed":
                    raise IdempotencyFailure(row.error or "previous execution failed")
                elif datetime.fromisoformat(row.lease_until) < now:
                    self._conn.execute(
                        "UPDATE idempotency SET lease_until=? WHERE key=?",
                        (lease_until, key),
                    )
                    acquired = True
                else:
                    raise IdempotencyInProgress(key)
            if not acquired:
                raise IdempotencyInProgress(key)
            try:
                value = operation()
            except Exception as exc:
                with self._conn:
                    self._conn.execute(
                        "UPDATE idempotency SET status='failed', error=? WHERE key=?",
                        (str(exc), key),
                    )
                raise
            with self._conn:
                self._conn.execute(
                    "UPDATE idempotency SET status='done', result=?, error=NULL WHERE key=?",
                    (json.dumps(value, ensure_ascii=False), key),
                )
            return value
