"""
Base models for UAW
Базовые модели для всех сущностей
"""

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, ClassVar
from enum import Enum
import hashlib


class EntityType(Enum):
    """Types of entities in the system"""
    PERSON = "person"
    TEAM = "team"
    PROJECT = "project"
    TASK = "task"
    ISSUE = "issue"
    REPOSITORY = "repository"
    DEPLOYMENT = "deployment"
    DOCUMENT = "document"
    EVENT = "event"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"
    APPROVAL = "approval"
    AUDIT_EVENT = "audit_event"


@dataclass
class UAWIdentifier:
    """
    Unique identifier for UAW entities.
    Provides consistent ID generation and validation.
    """
    entity_type: EntityType
    entity_id: str
    
    @classmethod
    def generate(cls, entity_type: EntityType) -> "UAWIdentifier":
        """Generate a new UAW identifier"""
        entity_id = f"{entity_type.value}_{uuid.uuid4().hex[:16]}"
        return cls(entity_type=entity_type, entity_id=entity_id)
    
    @classmethod
    def from_string(cls, identifier: str) -> "UAWIdentifier":
        """Parse identifier from string"""
        parts = identifier.split("_", 1)
        if len(parts) == 2:
            try:
                entity_type = EntityType(parts[0])
                return cls(entity_type=entity_type, entity_id=identifier)
            except ValueError:
                pass
        raise ValueError(f"Invalid UAW identifier: {identifier}")
    
    def __str__(self) -> str:
        return self.entity_id
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "entity_type": self.entity_type.value,
            "entity_id": self.entity_id
        }


@dataclass
class BaseModel:
    """
    Base model for all UAW entities.
    Provides common functionality for all data models.
    """
    
    # Class-level metadata
    entity_type: ClassVar[EntityType] = EntityType.PERSON
    
    # Instance attributes
    uaw_id: UAWIdentifier
    name: str
    description: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    is_active: bool = True
    
    def __post_init__(self):
        """Initialize after creation"""
        if isinstance(self.uaw_id, str):
            self.uaw_id = UAWIdentifier.from_string(self.uaw_id)
    
    @classmethod
    def generate_id(cls) -> UAWIdentifier:
        """Generate a new ID for this entity type"""
        return UAWIdentifier.generate(cls.entity_type)
    
    def update(self, **kwargs):
        """Update model attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "uaw_id": str(self.uaw_id),
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "metadata": self.metadata,
            "tags": self.tags,
            "is_active": self.is_active
        }
        # Add entity type
        result["entity_type"] = self.entity_type.value
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """Create from dictionary"""
        # This should be overridden by subclasses
        raise NotImplementedError("from_dict must be implemented by subclasses")
    
    def get_hash(self) -> str:
        """Get a hash of the model for change detection"""
        data = self.to_dict()
        # Remove volatile fields
        data.pop("updated_at", None)
        data.pop("updated_by", None)
        
        import json
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def __eq__(self, other):
        """Check equality based on ID"""
        if not isinstance(other, BaseModel):
            return False
        return str(self.uaw_id) == str(other.uaw_id)
    
    def __hash__(self):
        """Hash based on ID"""
        return hash(str(self.uaw_id))
