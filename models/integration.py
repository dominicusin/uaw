"""
Integration Model for UAW
Модель подключения к внешнему сервису
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

from .base import BaseModel, EntityType, UAWIdentifier


class IntegrationStatus(Enum):
    """Status of an integration"""
    CONNECTED = "connected"
    PARTIAL = "partial"
    READ_ONLY = "read_only"
    UNAUTHORISED = "unauthorised"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class IntegrationType(Enum):
    """Type of integration"""
    MCP = "mcp"
    REST = "rest"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    SDK = "sdk"


class AuthenticationMethod(Enum):
    """Authentication method"""
    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    JWT = "jwt"
    SESSION = "session"


@dataclass
class IntegrationCapability:
    """Integration capability"""
    name: str
    description: Optional[str] = None
    category: str = "other"  # read, write, admin, webhook
    supported: bool = True
    permissions_required: List[str] = field(default_factory=list)
    rate_limit: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "supported": self.supported,
            "permissions_required": self.permissions_required,
            "rate_limit": self.rate_limit
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntegrationCapability":
        return cls(
            name=data.get("name", ""),
            description=data.get("description"),
            category=data.get("category", "other"),
            supported=data.get("supported", True),
            permissions_required=data.get("permissions_required", []),
            rate_limit=data.get("rate_limit")
        )


@dataclass
class IntegrationRateLimit:
    """Integration rate limit"""
    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    requests_per_day: Optional[int] = None
    burst_limit: Optional[int] = None
    retry_after_seconds: int = 60
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "requests_per_minute": self.requests_per_minute,
            "requests_per_hour": self.requests_per_hour,
            "requests_per_day": self.requests_per_day,
            "burst_limit": self.burst_limit,
            "retry_after_seconds": self.retry_after_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntegrationRateLimit":
        return cls(
            requests_per_minute=data.get("requests_per_minute"),
            requests_per_hour=data.get("requests_per_hour"),
            requests_per_day=data.get("requests_per_day"),
            burst_limit=data.get("burst_limit"),
            retry_after_seconds=data.get("retry_after_seconds", 60)
        )


@dataclass
class Integration(BaseModel):
    """
    Integration model representing a connection to an external service.
    
    Attributes:
        uaw_id: Unique UAW identifier
        name: Integration name
        service: Name of the external service
        integration_type: Type of integration
        status: Current integration status
        authentication_method: Authentication method used
        base_url: Base URL for the service
        api_version: API version
        is_authenticated: Whether authentication is complete
        auth_token: Authentication token (should be encrypted)
        auth_data: Additional authentication data
        capabilities: List of supported capabilities
        rate_limits: Rate limit information
        webhook_url: URL for webhooks if supported
        webhook_secret: Secret for webhook verification
        last_connected_at: When integration was last connected
        last_error: Last error message
        last_error_at: When last error occurred
        retry_count: Number of connection retries
        external_ids: IDs in external systems (for tracking)
        custom_fields: Custom integration fields
    """
    
    entity_type: ClassVar[EntityType] = EntityType.INTEGRATION
    
    service: str
    integration_type: IntegrationType = IntegrationType.MCP
    status: IntegrationStatus = IntegrationStatus.UNAVAILABLE
    authentication_method: AuthenticationMethod = AuthenticationMethod.NONE
    
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    is_authenticated: bool = False
    auth_token: Optional[str] = None
    auth_data: Dict[str, Any] = field(default_factory=dict)
    
    capabilities: Dict[str, IntegrationCapability] = field(default_factory=dict)
    rate_limits: IntegrationRateLimit = field(default_factory=IntegrationRateLimit)
    
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    last_connected_at: Optional[str] = None
    last_error: Optional[str] = None
    last_error_at: Optional[str] = None
    retry_count: int = 0
    
    # External system IDs (for tracking integrations of integrations)
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.capabilities, list):
            self.capabilities = {c.name: c for c in self.capabilities}
        if isinstance(self.rate_limits, dict):
            self.rate_limits = IntegrationRateLimit.from_dict(self.rate_limits)
    
    def add_capability(self, capability: IntegrationCapability) -> None:
        """Add a capability"""
        self.capabilities[capability.name] = capability
    
    def remove_capability(self, name: str) -> bool:
        """Remove a capability"""
        if name in self.capabilities:
            del self.capabilities[name]
            return True
        return False
    
    def has_capability(self, name: str) -> bool:
        """Check if integration has a specific capability"""
        cap = self.capabilities.get(name)
        return cap is not None and cap.supported
    
    def get_capability(self, name: str) -> Optional[IntegrationCapability]:
        """Get a capability by name"""
        return self.capabilities.get(name)
    
    def add_external_id(self, system: str, external_id: str) -> None:
        """Add an external system ID"""
        self.external_ids[system] = external_id
    
    def get_external_id(self, system: str) -> Optional[str]:
        """Get external ID for a system"""
        return self.external_ids.get(system)
    
    def set_auth_token(self, token: str) -> None:
        """Set authentication token"""
        self.auth_token = token
        self.is_authenticated = token is not None
        self.last_connected_at = datetime.now(timezone.utc).isoformat()
    
    def set_auth_data(self, key: str, value: Any) -> None:
        """Set authentication data"""
        self.auth_data[key] = value
    
    def clear_auth(self) -> None:
        """Clear authentication"""
        self.auth_token = None
        self.auth_data = {}
        self.is_authenticated = False
    
    def set_status(self, status: IntegrationStatus) -> None:
        """Set integration status"""
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_error(self, error: str) -> None:
        """Set last error"""
        self.last_error = error
        self.last_error_at = datetime.now(timezone.utc).isoformat()
        self.retry_count += 1
    
    def clear_error(self) -> None:
        """Clear last error"""
        self.last_error = None
        self.last_error_at = None
        self.retry_count = 0
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field"""
        self.custom_fields[key] = value
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field"""
        return self.custom_fields.get(key, default)
    
    def is_connected(self) -> bool:
        """Check if integration is connected"""
        return self.status == IntegrationStatus.CONNECTED
    
    def is_available(self) -> bool:
        """Check if integration is available"""
        return self.status in [
            IntegrationStatus.CONNECTED,
            IntegrationStatus.PARTIAL,
            IntegrationStatus.READ_ONLY
        ]
    
    def requires_auth(self) -> bool:
        """Check if integration requires authentication"""
        return self.authentication_method != AuthenticationMethod.NONE and not self.is_authenticated
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        result.update({
            "service": self.service,
            "integration_type": self.integration_type.value,
            "status": self.status.value,
            "authentication_method": self.authentication_method.value,
            "base_url": self.base_url,
            "api_version": self.api_version,
            "is_authenticated": self.is_authenticated,
            "auth_token": "***REDACTED**" if self.auth_token else None,
            "auth_data": {k: "***REDACTED***" for k in self.auth_data.keys()} if self.auth_data else {},
            "capabilities": {k: v.to_dict() for k, v in self.capabilities.items()},
            "rate_limits": self.rate_limits.to_dict() if self.rate_limits else None,
            "webhook_url": self.webhook_url,
            "webhook_secret": "***REDACTED**" if self.webhook_secret else None,
            "last_connected_at": self.last_connected_at,
            "last_error": self.last_error,
            "last_error_at": self.last_error_at,
            "retry_count": self.retry_count,
            "external_ids": self.external_ids,
            "custom_fields": self.custom_fields
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Integration":
        """Create from dictionary"""
        uaw_id = data.get("uaw_id")
        if isinstance(uaw_id, str):
            uaw_id = UAWIdentifier.from_string(uaw_id)
        
        # Parse capabilities
        capabilities = {}
        for name, cap_data in data.get("capabilities", {}).items():
            capabilities[name] = IntegrationCapability.from_dict(cap_data)
        
        # Parse rate limits
        rate_limits = None
        if data.get("rate_limits"):
            rate_limits = IntegrationRateLimit.from_dict(data["rate_limits"])
        
        return cls(
            uaw_id=uaw_id,
            name=data.get("name", ""),
            description=data.get("description"),
            service=data.get("service", ""),
            integration_type=IntegrationType(data.get("integration_type", "mcp")),
            status=IntegrationStatus(data.get("status", "unavailable")),
            authentication_method=AuthenticationMethod(data.get("authentication_method", "none")),
            base_url=data.get("base_url"),
            api_version=data.get("api_version"),
            is_authenticated=data.get("is_authenticated", False),
            auth_token=data.get("auth_token"),
            auth_data=data.get("auth_data", {}),
            capabilities=capabilities,
            rate_limits=rate_limits or IntegrationRateLimit(),
            webhook_url=data.get("webhook_url"),
            webhook_secret=data.get("webhook_secret"),
            last_connected_at=data.get("last_connected_at"),
            last_error=data.get("last_error"),
            last_error_at=data.get("last_error_at"),
            retry_count=data.get("retry_count", 0),
            external_ids=data.get("external_ids", {}),
            custom_fields=data.get("custom_fields", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            is_active=data.get("is_active", True)
        )


@dataclass
class IntegrationBuilder:
    """Builder for creating Integration instances"""
    
    name: str
    service: str
    integration_type: IntegrationType = IntegrationType.MCP
    
    def with_description(self, description: str) -> "IntegrationBuilder":
        """Set description"""
        self._description = description
        return self
    
    def with_authentication(self, method: AuthenticationMethod) -> "IntegrationBuilder":
        """Set authentication method"""
        self._authentication_method = method
        return self
    
    def with_base_url(self, base_url: str) -> "IntegrationBuilder":
        """Set base URL"""
        self._base_url = base_url
        return self
    
    def with_api_version(self, version: str) -> "IntegrationBuilder":
        """Set API version"""
        self._api_version = version
        return self
    
    def with_capability(
        self,
        name: str,
        description: Optional[str] = None,
        category: str = "other",
        supported: bool = True
    ) -> "IntegrationBuilder":
        """Add capability"""
        self._capabilities = getattr(self, "_capabilities", [])
        self._capabilities.append(IntegrationCapability(
            name=name,
            description=description,
            category=category,
            supported=supported
        ))
        return self
    
    def with_external_id(self, system: str, external_id: str) -> "IntegrationBuilder":
        """Add external ID"""
        self._external_ids = getattr(self, "_external_ids", {})
        self._external_ids[system] = external_id
        return self
    
    def build(self) -> Integration:
        """Build Integration instance"""
        capabilities = {}
        for cap in getattr(self, "_capabilities", []):
            capabilities[cap.name] = cap
        
        return Integration(
            uaw_id=Integration.generate_id(),
            name=self.name,
            description=getattr(self, "_description", None),
            service=self.service,
            integration_type=self.integration_type,
            authentication_method=getattr(self, "_authentication_method", AuthenticationMethod.NONE),
            base_url=getattr(self, "_base_url", None),
            api_version=getattr(self, "_api_version", None),
            capabilities=capabilities,
            external_ids=getattr(self, "_external_ids", {})
        )
