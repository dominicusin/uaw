"""
Team Model for UAW
Модель команды
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from .base import BaseModel, EntityType, UAWIdentifier


@dataclass
class Team(BaseModel):
    """
    Team model representing a group of people working together.
    
    Attributes:
        uaw_id: Unique UAW identifier
        name: Team name
        description: Team description
        organization_id: Organization this team belongs to
        members: List of member UAW IDs
        lead_id: UAW ID of team lead
        external_ids: IDs in external systems
        settings: Team settings
        visibility: Team visibility (public, private, secret)
    """
    
    entity_type: ClassVar[EntityType] = EntityType.TEAM
    
    organization_id: Optional[str] = None
    members: List[str] = field(default_factory=list)
    lead_id: Optional[str] = None
    
    # External system IDs
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    # Settings
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Visibility
    visibility: str = "private"  # public, private, secret
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.members, str):
            self.members = [self.members]
    
    def add_member(self, person_id: str) -> None:
        """Add a member to the team"""
        if person_id not in self.members:
            self.members.append(person_id)
    
    def remove_member(self, person_id: str) -> bool:
        """Remove a member from the team"""
        if person_id in self.members:
            self.members.remove(person_id)
            if self.lead_id == person_id:
                self.lead_id = None
            return True
        return False
    
    def set_lead(self, person_id: str) -> bool:
        """Set team lead"""
        if person_id in self.members:
            self.lead_id = person_id
            return True
        return False
    
    def has_member(self, person_id: str) -> bool:
        """Check if team has a specific member"""
        return person_id in self.members
    
    def add_external_id(self, system: str, external_id: str) -> None:
        """Add an external system ID"""
        self.external_ids[system] = external_id
    
    def get_external_id(self, system: str) -> Optional[str]:
        """Get external ID for a system"""
        return self.external_ids.get(system)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a team setting"""
        self.settings[key] = value
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a team setting"""
        return self.settings.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        result.update({
            "organization_id": self.organization_id,
            "members": self.members,
            "lead_id": self.lead_id,
            "external_ids": self.external_ids,
            "settings": self.settings,
            "visibility": self.visibility
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Team":
        """Create from dictionary"""
        uaw_id = data.get("uaw_id")
        if isinstance(uaw_id, str):
            uaw_id = UAWIdentifier.from_string(uaw_id)
        
        return cls(
            uaw_id=uaw_id,
            name=data.get("name", ""),
            description=data.get("description"),
            organization_id=data.get("organization_id"),
            members=data.get("members", []),
            lead_id=data.get("lead_id"),
            external_ids=data.get("external_ids", {}),
            settings=data.get("settings", {}),
            visibility=data.get("visibility", "private"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            is_active=data.get("is_active", True)
        )
    
    def get_github_team_name(self) -> Optional[str]:
        """Get GitHub team name if available"""
        return self.external_ids.get("github")
    
    def get_asana_team_id(self) -> Optional[str]:
        """Get Asana team GID if available"""
        return self.external_ids.get("asana")
    
    def get_slack_channel_id(self) -> Optional[str]:
        """Get Slack channel ID if available"""
        return self.external_ids.get("slack")
    
    def member_count(self) -> int:
        """Get number of members"""
        return len(self.members)


@dataclass
class TeamBuilder:
    """Builder for creating Team instances"""
    
    name: str
    organization_id: Optional[str] = None
    visibility: str = "private"
    
    def with_description(self, description: str) -> "TeamBuilder":
        """Set description"""
        self._description = description
        return self
    
    def with_lead(self, lead_id: str) -> "TeamBuilder":
        """Set team lead"""
        self._lead_id = lead_id
        return self
    
    def with_member(self, person_id: str) -> "TeamBuilder":
        """Add member"""
        self._members = getattr(self, "_members", [])
        if person_id not in self._members:
            self._members.append(person_id)
        return self
    
    def with_external_id(self, system: str, external_id: str) -> "TeamBuilder":
        """Add external ID"""
        self._external_ids = getattr(self, "_external_ids", {})
        self._external_ids[system] = external_id
        return self
    
    def build(self) -> Team:
        """Build Team instance"""
        return Team(
            uaw_id=Team.generate_id(),
            name=self.name,
            description=getattr(self, "_description", None),
            organization_id=self.organization_id,
            lead_id=getattr(self, "_lead_id", None),
            members=getattr(self, "_members", []),
            external_ids=getattr(self, "_external_ids", {}),
            visibility=self.visibility
        )
