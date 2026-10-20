"""
State Manager for UAW
Управление состоянием системы и сохранение данных между сессиями
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class StateType(Enum):
    """Types of state data"""
    WORKFLOW = "workflow"
    RESOURCE_MAPPING = "resource_mapping"
    EXECUTION_CONTEXT = "execution_context"
    USER_PREFERENCES = "user_preferences"
    AUDIT_LOG = "audit_log"


@dataclass
class StateEntry:
    """Single state entry"""
    key: str
    value: Any
    state_type: StateType
    created_at: str
    updated_at: str
    ttl: Optional[int] = None  # Time to live in seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "state_type": self.state_type.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "ttl": self.ttl
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateEntry":
        return cls(
            key=data["key"],
            value=data["value"],
            state_type=StateType(data["state_type"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            ttl=data.get("ttl")
        )


class StateManager:
    """
    Manages persistent state for UAW system.
    Supports saving and loading state between sessions.
    """
    
    def __init__(self, state_dir: Union[str, Path]):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory state cache
        self._cache: Dict[str, StateEntry] = {}
        
        # Load existing state
        self._load_state()
    
    def _load_state(self):
        """Load state from disk"""
        state_file = self.state_dir / "state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    for entry_data in state_data.get("entries", []):
                        entry = StateEntry.from_dict(entry_data)
                        self._cache[entry.key] = entry
            except Exception as e:
                print(f"Warning: Failed to load state: {e}")
    
    def _save_state(self):
        """Save state to disk"""
        state_file = self.state_dir / "state.json"
        try:
            state_data = {
                "entries": [entry.to_dict() for entry in self._cache.values()],
                "saved_at": datetime.now(timezone.utc).isoformat()
            }
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save state: {e}")
    
    def set(
        self,
        key: str,
        value: Any,
        state_type: StateType = StateType.WORKFLOW,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set a state value.
        
        Args:
            key: Unique key for the state entry
            value: Value to store
            state_type: Type of state data
            ttl: Time to live in seconds (optional)
        """
        now = datetime.now(timezone.utc).isoformat()
        
        entry = StateEntry(
            key=key,
            value=value,
            state_type=state_type,
            created_at=now,
            updated_at=now,
            ttl=ttl
        )
        
        self._cache[key] = entry
        self._save_state()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a state value.
        
        Args:
            key: Key to retrieve
            
        Returns:
            Stored value or None if not found
        """
        entry = self._cache.get(key)
        if entry:
            # Check TTL
            if entry.ttl:
                created = datetime.fromisoformat(entry.created_at)
                elapsed = (datetime.now(timezone.utc) - created).total_seconds()
                if elapsed > entry.ttl:
                    del self._cache[key]
                    self._save_state()
                    return None
            return entry.value
        return None
    
    def get_entry(self, key: str) -> Optional[StateEntry]:
        """Get complete state entry"""
        entry = self._cache.get(key)
        if entry:
            if entry.ttl:
                created = datetime.fromisoformat(entry.created_at)
                elapsed = (datetime.now(timezone.utc) - created).total_seconds()
                if elapsed > entry.ttl:
                    del self._cache[key]
                    self._save_state()
                    return None
            return entry
        return None
    
    def delete(self, key: str) -> bool:
        """
        Delete a state entry.
        
        Args:
            key: Key to delete
            
        Returns:
            True if deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            self._save_state()
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if state entry exists"""
        return key in self._cache
    
    def list_entries(
        self,
        state_type: Optional[StateType] = None
    ) -> List[StateEntry]:
        """List all state entries, optionally filtered by type"""
        if state_type:
            return [
                entry for entry in self._cache.values()
                if entry.state_type == state_type
            ]
        return list(self._cache.values())
    
    def clear(self, state_type: Optional[StateType] = None) -> int:
        """
        Clear state entries.
        
        Args:
            state_type: Optional type filter
            
        Returns:
            Number of entries cleared
        """
        if state_type:
            keys_to_delete = [
                key for key, entry in self._cache.items()
                if entry.state_type == state_type
            ]
        else:
            keys_to_delete = list(self._cache.keys())
        
        for key in keys_to_delete:
            del self._cache[key]
        
        self._save_state()
        return len(keys_to_delete)
    
    def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get state for a specific workflow"""
        return self.get(workflow_id)
    
    def save_workflow_state(
        self,
        workflow_id: str,
        state: Dict[str, Any]
    ) -> None:
        """Save state for a workflow"""
        self.set(
            workflow_id,
            state,
            StateType.WORKFLOW,
            ttl=86400  # 24 hours
        )
    
    def get_resource_mapping(self, mapping_id: str) -> Optional[Dict[str, Any]]:
        """Get a resource mapping"""
        return self.get(f"mapping_{mapping_id}")
    
    def save_resource_mapping(
        self,
        mapping_id: str,
        mapping: Dict[str, Any]
    ) -> None:
        """Save a resource mapping"""
        self.set(
            f"mapping_{mapping_id}",
            mapping,
            StateType.RESOURCE_MAPPING
        )
    
    def cleanup_expired(self) -> int:
        """Remove expired state entries"""
        expired_keys = []
        now = datetime.now(timezone.utc)
        
        for key, entry in self._cache.items():
            if entry.ttl:
                created = datetime.fromisoformat(entry.created_at)
                elapsed = (now - created).total_seconds()
                if elapsed > entry.ttl:
                    expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            self._save_state()
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get state statistics"""
        return {
            "total_entries": len(self._cache),
            "by_type": {
                state_type.value: len([
                    entry for entry in self._cache.values()
                    if entry.state_type == state_type
                ]) for state_type in StateType
            }
        }
