"""
Project Model for UAW
Модель проекта
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

from .base import BaseModel, EntityType, UAWIdentifier


class ProjectStatus(Enum):
    """Status of a project"""
    PLANNED = "planned"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ProjectVisibility(Enum):
    """Visibility of a project"""
    PUBLIC = "public"
    PRIVATE = "private"
    SECRET = "secret"


@dataclass
class Project(BaseModel):
    """
    Project model representing a project with identifiers across systems.
    
    Attributes:
        uaw_id: Unique UAW identifier
        name: Project name
        description: Project description
        status: Current project status
        visibility: Project visibility
        organization_id: Organization this project belongs to
        team_id: Primary team for this project
        members: List of member UAW IDs
        start_date: Project start date
        end_date: Project end date
        due_date: Project due date
        external_ids: IDs in external systems (github, asana, etc.)
        settings: Project settings
        custom_fields: Custom project fields
    """
    
    entity_type: ClassVar[EntityType] = EntityType.PROJECT
    
    status: ProjectStatus = ProjectStatus.PLANNED
    visibility: ProjectVisibility = ProjectVisibility.PRIVATE
    
    organization_id: Optional[str] = None
    team_id: Optional[str] = None
    members: List[str] = field(default_factory=list)
    
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    due_date: Optional[str] = None
    
    # External system IDs
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    # Settings and custom fields
    settings: Dict[str, Any] = field(default_factory=dict)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.members, str):
            self.members = [self.members]
    
    def add_member(self, person_id: str) -> None:
        """Add a member to the project"""
        if person_id not in self.members:
            self.members.append(person_id)
    
    def remove_member(self, person_id: str) -> bool:
        """Remove a member from the project"""
        if person_id in self.members:
            self.members.remove(person_id)
            return True
        return False
    
    def has_member(self, person_id: str) -> bool:
        """Check if project has a specific member"""
        return person_id in self.members
    
    def add_external_id(self, system: str, external_id: str) -> None:
        """Add an external system ID"""
        self.external_ids[system] = external_id
    
    def get_external_id(self, system: str) -> Optional[str]:
        """Get external ID for a system"""
        return self.external_ids.get(system)
    
    def set_status(self, status: ProjectStatus) -> None:
        """Set project status"""
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a project setting"""
        self.settings[key] = value
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a project setting"""
        return self.settings.get(key, default)
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field"""
        self.custom_fields[key] = value
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field"""
        return self.custom_fields.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        result.update({
            "status": self.status.value,
            "visibility": self.visibility.value,
            "organization_id": self.organization_id,
            "team_id": self.team_id,
            "members": self.members,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "due_date": self.due_date,
            "external_ids": self.external_ids,
            "settings": self.settings,
            "custom_fields": self.custom_fields
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """Create from dictionary"""
        uaw_id = data.get("uaw_id")
        if isinstance(uaw_id, str):
            uaw_id = UAWIdentifier.from_string(uaw_id)
        
        return cls(
            uaw_id=uaw_id,
            name=data.get("name", ""),
            description=data.get("description"),
            status=ProjectStatus(data.get("status", "planned")),
            visibility=ProjectVisibility(data.get("visibility", "private")),
            organization_id=data.get("organization_id"),
            team_id=data.get("team_id"),
            members=data.get("members", []),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            due_date=data.get("due_date"),
            external_ids=data.get("external_ids", {}),
            settings=data.get("settings", {}),
            custom_fields=data.get("custom_fields", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            is_active=data.get("is_active", True)
        )
    
    def get_github_repository(self) -> Optional[str]:
        """Get GitHub repository name if available"""
        return self.external_ids.get("github")
    
    def get_asana_project_id(self) -> Optional[str]:
        """Get Asana project GID if available"""
        return self.external_ids.get("asana")
    
    def get_linear_project_id(self) -> Optional[str]:
        """Get Linear project ID if available"""
        return self.external_ids.get("linear")
    
    def is_active(self) -> bool:
        """Check if project is active"""
        return self.status in [ProjectStatus.ACTIVE, ProjectStatus.PLANNED]
    
    def is_completed(self) -> bool:
        """Check if project is completed"""
        return self.status in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED, ProjectStatus.ARCHIVED]


@dataclass
class ProjectBuilder:
    """Builder for creating Project instances"""
    
    name: str
    
    def with_description(self, description: str) -> "ProjectBuilder":
        """Set description"""
        self._description = description
        return self
    
    def with_status(self, status: ProjectStatus) -> "ProjectBuilder":
        """Set status"""
        self._status = status
        return self
    
    def with_visibility(self, visibility: ProjectVisibility) -> "ProjectBuilder":
        """Set visibility"""
        self._visibility = visibility
        return self
    
    def with_team(self, team_id: str) -> "ProjectBuilder":
        """Set primary team"""
        self._team_id = team_id
        return self
    
    def with_member(self, person_id: str) -> "ProjectBuilder":
        """Add member"""
        self._members = getattr(self, "_members", [])
        if person_id not in self._members:
            self._members.append(person_id)
        return self
    
    def with_external_id(self, system: str, external_id: str) -> "ProjectBuilder":
        """Add external ID"""
        self._external_ids = getattr(self, "_external_ids", {})
        self._external_ids[system] = external_id
        return self
    
    def with_dates(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> "ProjectBuilder":
        """Set dates"""
        self._start_date = start_date
        self._end_date = end_date
        self._due_date = due_date
        return self
    
    def build(self) -> Project:
        """Build Project instance"""
        return Project(
            uaw_id=Project.generate_id(),
            name=self.name,
            description=getattr(self, "_description", None),
            status=getattr(self, "_status", ProjectStatus.PLANNED),
            visibility=getattr(self, "_visibility", ProjectVisibility.PRIVATE),
            team_id=getattr(self, "_team_id", None),
            members=getattr(self, "_members", []),
            external_ids=getattr(self, "_external_ids", {}),
            start_date=getattr(self, "_start_date", None),
            end_date=getattr(self, "_end_date", None),
            due_date=getattr(self, "_due_date", None)
        )
