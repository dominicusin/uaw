"""
Base Integration for UAW
Базовый класс для всех интеграций
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union
import json


class IntegrationStatus(Enum):
    """Status of an integration connection"""
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
    WEBHOOK = "webhook"
    SDK = "sdk"


@dataclass
class IntegrationConfig:
    """Configuration for an integration"""
    name: str
    display_name: str
    description: str
    integration_type: IntegrationType = IntegrationType.MCP
    base_url: Optional[str] = None
    api_version: str = "v1"
    timeout: int = 30  # seconds
    max_retries: int = 3
    rate_limit: Optional[int] = None  # requests per minute
    
    # Authentication
    auth_method: str = "oauth2"
    requires_auth: bool = True
    
    # Capabilities
    supports_read: bool = True
    supports_write: bool = True
    supports_webhooks: bool = False
    supports_search: bool = True
    
    # Pagination
    max_page_size: int = 100
    
    # Metadata
    icon_url: Optional[str] = None
    documentation_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "integration_type": self.integration_type.value,
            "base_url": self.base_url,
            "api_version": self.api_version,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "rate_limit": self.rate_limit,
            "auth_method": self.auth_method,
            "requires_auth": self.requires_auth,
            "supports_read": self.supports_read,
            "supports_write": self.supports_write,
            "supports_webhooks": self.supports_webhooks,
            "supports_search": self.supports_search,
            "max_page_size": self.max_page_size,
            "icon_url": self.icon_url,
            "documentation_url": self.documentation_url
        }


@dataclass
class IntegrationResult:
    """Result of an integration operation"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "status_code": self.status_code,
            "headers": self.headers,
            "metadata": self.metadata
        }


@dataclass
class IntegrationCapability:
    """Capability of an integration"""
    name: str
    description: str
    operation: str  # read, write, delete, etc.
    parameters: List[str] = field(default_factory=list)
    returns: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "operation": self.operation,
            "parameters": self.parameters,
            "returns": self.returns
        }


class BaseIntegration(ABC):
    """
    Base class for all integrations.
    Provides common functionality and interface.
    """
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.status = IntegrationStatus.UNAVAILABLE
        self.last_error: Optional[str] = None
        self.last_checked: Optional[str] = None
        self.capabilities: List[IntegrationCapability] = []
        self._initialized = False
        
        # Rate limiting
        self._last_request_time: Optional[datetime] = None
        self._request_count = 0
    
    @property
    def name(self) -> str:
        """Integration name"""
        return self.config.name
    
    @property
    def display_name(self) -> str:
        """Display name"""
        return self.config.display_name
    
    @property
    def description(self) -> str:
        """Description"""
        return self.config.description
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the integration.
        Check connection and authentication.
        
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    async def check_status(self) -> IntegrationStatus:
        """
        Check the current status of the integration.
        
        Returns:
            Current status
        """
        pass
    
    @abstractmethod
    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> IntegrationResult:
        """
        Execute an action on the integration.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            
        Returns:
            IntegrationResult with success status and data
        """
        pass
    
    def is_available(self) -> bool:
        """Check if integration is available"""
        return self.status in [
            IntegrationStatus.CONNECTED,
            IntegrationStatus.PARTIAL,
            IntegrationStatus.READ_ONLY
        ]
    
    def can_read(self) -> bool:
        """Check if read operations are supported"""
        return self.config.supports_read and self.is_available()
    
    def can_write(self) -> bool:
        """Check if write operations are supported"""
        return self.config.supports_write and self.status == IntegrationStatus.CONNECTED
    
    def can_delete(self) -> bool:
        """Check if delete operations are supported"""
        return self.config.supports_write and self.status == IntegrationStatus.CONNECTED
    
    def can_search(self) -> bool:
        """Check if search operations are supported"""
        return self.config.supports_search and self.is_available()
    
    def get_capabilities(self) -> List[IntegrationCapability]:
        """Get list of capabilities"""
        return self.capabilities
    
    def has_capability(self, capability_name: str) -> bool:
        """Check if integration has a specific capability"""
        return any(cap.name == capability_name for cap in self.capabilities)
    
    async def check_rate_limit(self) -> bool:
        """
        Check if we're hitting rate limits.
        
        Returns:
            True if we can make another request
        """
        if not self.config.rate_limit:
            return True
        
        now = datetime.now(timezone.utc)
        
        # Reset count if it's been more than a minute
        if self._last_request_time:
            elapsed = (now - self._last_request_time).total_seconds()
            if elapsed > 60:
                self._request_count = 0
                self._last_request_time = now
        else:
            self._last_request_time = now
        
        # Check if we've hit the limit
        if self._request_count >= self.config.rate_limit:
            return False
        
        self._request_count += 1
        return True
    
    async def wait_for_rate_limit(self) -> None:
        """Wait until rate limit resets"""
        if not self.config.rate_limit:
            return
        
        now = datetime.now(timezone.utc)
        if self._last_request_time:
            elapsed = (now - self._last_request_time).total_seconds()
            if elapsed < 60:
                wait_time = 60 - elapsed
                await asyncio.sleep(wait_time)
                self._request_count = 0
                self._last_request_time = datetime.now(timezone.utc)
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get detailed status information"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "status": self.status.value,
            "last_error": self.last_error,
            "last_checked": self.last_checked,
            "capabilities": [cap.to_dict() for cap in self.capabilities],
            "config": self.config.to_dict()
        }
    
    def add_capability(self, capability: IntegrationCapability) -> None:
        """Add a capability to the integration"""
        self.capabilities.append(capability)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} status={self.status.value}>"


class IntegrationError(Exception):
    """Error raised by integrations"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data


class IntegrationTimeoutError(IntegrationError):
    """Timeout error for integrations"""
    pass


class IntegrationAuthError(IntegrationError):
    """Authentication error for integrations"""
    pass


class IntegrationRateLimitError(IntegrationError):
    """Rate limit error for integrations"""
    pass
