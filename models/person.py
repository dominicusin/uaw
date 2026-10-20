"""
Person Model for UAW
Модель пользователя/исполнителя
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from .base import BaseModel, EntityType, UAWIdentifier


@dataclass
class Person(BaseModel):
    """
    Person model representing a user, employee, or team member.
    
    Attributes:
        uaw_id: Unique UAW identifier
        name: Full name
        email: Primary email address
        username: Username in various systems
        avatar_url: URL to profile picture
        is_bot: Whether this is a bot/account
        time_zone: User's timezone
        locale: User's locale
        external_ids: IDs in external systems (github, asana, etc.)
        teams: Team memberships
        roles: User roles
        permissions: Permission levels
        preferences: User preferences
    """
    
    entity_type: ClassVar[EntityType] = EntityType.PERSON
    
    email: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    is_bot: bool = False
    time_zone: Optional[str] = "UTC"
    locale: Optional[str] = "en-US"
    
    # External system IDs
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    # Team memberships
    teams: List[str] = field(default_factory=list)
    
    # Roles and permissions
    roles: List[str] = field(default_factory=list)
    permissions: Dict[str, Any] = field(default_factory=dict)
    
    # Preferences
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.teams, str):
            self.teams = [self.teams]
        if isinstance(self.roles, str):
            self.roles = [self.roles]
    
    def add_external_id(self, system: str, external_id: str) -> None:
        """Add an external system ID"""
        self.external_ids[system] = external_id
    
    def get_external_id(self, system: str) -> Optional[str]:
        """Get external ID for a system"""
        return self.external_ids.get(system)
    
    def add_team(self, team_id: str) -> None:
        """Add team membership"""
        if team_id not in self.teams:
            self.teams.append(team_id)
    
    def remove_team(self, team_id: str) -> bool:
        """Remove team membership"""
        if team_id in self.teams:
            self.teams.remove(team_id)
            return True
        return False
    
    def add_role(self, role: str) -> None:
        """Add a role"""
        if role not in self.roles:
            self.roles.append(role)
    
    def remove_role(self, role: str) -> bool:
        """Remove a role"""
        if role in self.roles:
            self.roles.remove(role)
            return True
        return False
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.roles
    
    def set_permission(self, resource: str, level: str) -> None:
        """Set permission level for a resource"""
        self.permissions[resource] = level
    
    def get_permission(self, resource: str) -> Optional[str]:
        """Get permission level for a resource"""
        return self.permissions.get(resource)
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference"""
        self.preferences[key] = value
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        return self.preferences.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        result.update({
            "email": self.email,
            "username": self.username,
            "avatar_url": self.avatar_url,
            "is_bot": self.is_bot,
            "time_zone": self.time_zone,
            "locale": self.locale,
            "external_ids": self.external_ids,
            "teams": self.teams,
            "roles": self.roles,
            "permissions": self.permissions,
            "preferences": self.preferences
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Person":
        """Create from dictionary"""
        uaw_id = data.get("uaw_id")
        if isinstance(uaw_id, str):
            uaw_id = UAWIdentifier.from_string(uaw_id)
        
        return cls(
            uaw_id=uaw_id,
            name=data.get("name", ""),
            description=data.get("description"),
            email=data.get("email"),
            username=data.get("username"),
            avatar_url=data.get("avatar_url"),
            is_bot=data.get("is_bot", False),
            time_zone=data.get("time_zone", "UTC"),
            locale=data.get("locale", "en-US"),
            external_ids=data.get("external_ids", {}),
            teams=data.get("teams", []),
            roles=data.get("roles", []),
            permissions=data.get("permissions", {}),
            preferences=data.get("preferences", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            is_active=data.get("is_active", True)
        )
    
    def get_github_username(self) -> Optional[str]:
        """Get GitHub username if available"""
        return self.external_ids.get("github") or self.username
    
    def get_asana_id(self) -> Optional[str]:
        """Get Asana user GID if available"""
        return self.external_ids.get("asana")
    
    def get_slack_id(self) -> Optional[str]:
        """Get Slack user ID if available"""
        return self.external_ids.get("slack")
    
    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return "admin" in self.roles or self.has_role("administrator")
    
    def is_bot_user(self) -> bool:
        """Check if this is a bot user"""
        return self.is_bot


@dataclass
class PersonBuilder:
    """Builder for creating Person instances"""
    
    name: str
    email: Optional[str] = None
    username: Optional[str] = None
    is_bot: bool = False
    
    def with_external_id(self, system: str, external_id: str) -> "PersonBuilder":
        """Add external ID"""
        self._external_ids = getattr(self, "_external_ids", {})
        self._external_ids[system] = external_id
        return self
    
    def with_team(self, team_id: str) -> "PersonBuilder":
        """Add team membership"""
        self._teams = getattr(self, "_teams", [])
        if team_id not in self._teams:
            self._teams.append(team_id)
        return self
    
    def with_role(self, role: str) -> "PersonBuilder":
        """Add role"""
        self._roles = getattr(self, "_roles", [])
        if role not in self._roles:
            self._roles.append(role)
        return self
    
    def build(self) -> Person:
        """Build Person instance"""
        return Person(
            uaw_id=Person.generate_id(),
            name=self.name,
            email=self.email,
            username=self.username,
            is_bot=self.is_bot,
            external_ids=getattr(self, "_external_ids", {}),
            teams=getattr(self, "_teams", []),
            roles=getattr(self, "_roles", [])
        )
