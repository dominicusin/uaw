"""
Base Adapter for UAW
Базовый класс для всех адаптеров
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import aiohttp
import json


class AdapterStatus(Enum):
    """Status of an adapter"""
    AVAILABLE = "available"
    CONFIGURED = "configured"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class AuthMethod(Enum):
    """Authentication methods"""
    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"


@dataclass
class AdapterConfig:
    """Configuration for an adapter"""
    name: str
    display_name: str
    description: str
    base_url: str
    api_version: str = "v1"
    timeout: int = 30
    max_retries: int = 3
    rate_limit: Optional[int] = None
    
    # Authentication
    auth_method: AuthMethod = AuthMethod.NONE
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Headers
    default_headers: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    icon_url: Optional[str] = None
    documentation_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "base_url": self.base_url,
            "api_version": self.api_version,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "rate_limit": self.rate_limit,
            "auth_method": self.auth_method.value,
            "default_headers": self.default_headers,
            "icon_url": self.icon_url,
            "documentation_url": self.documentation_url
        }
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for requests"""
        headers = self.default_headers.copy()
        
        if self.auth_method == AuthMethod.API_KEY and self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self.auth_method == AuthMethod.BEARER_TOKEN and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        elif self.auth_method == AuthMethod.BASIC_AUTH and self.username and self.password:
            import base64
            credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            headers["Authorization"] = f"Basic {credentials}"
        elif self.auth_method == AuthMethod.OAUTH2 and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        
        return headers


@dataclass
class AdapterResult:
    """Result of an adapter operation"""
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
class AdapterCapability:
    """Capability of an adapter"""
    name: str
    description: str
    method: str  # GET, POST, PUT, DELETE, etc.
    endpoint: str
    parameters: List[str] = field(default_factory=list)
    returns: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "method": self.method,
            "endpoint": self.endpoint,
            "parameters": self.parameters,
            "returns": self.returns
        }


class BaseAdapter(ABC):
    """
    Base class for all adapters.
    Adapters provide REST API access to services that don't have MCP connectors.
    """
    
    def __init__(self, config: AdapterConfig):
        self.config = config
        self.status = AdapterStatus.UNAVAILABLE
        self.last_error: Optional[str] = None
        self.last_checked: Optional[str] = None
        self.capabilities: List[AdapterCapability] = []
        self._session: Optional[aiohttp.ClientSession] = None
        self._initialized = False
    
    @property
    def name(self) -> str:
        """Adapter name"""
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
        Initialize the adapter.
        Check configuration and connection.
        
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    async def check_status(self) -> AdapterStatus:
        """
        Check the current status of the adapter.
        
        Returns:
            Current status
        """
        pass
    
    @abstractmethod
    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """
        Execute an action on the adapter.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            
        Returns:
            AdapterResult with success status and data
        """
        pass
    
    def is_available(self) -> bool:
        """Check if adapter is available"""
        return self.status in [AdapterStatus.AVAILABLE, AdapterStatus.CONFIGURED]
    
    def get_capabilities(self) -> List[AdapterCapability]:
        """Get list of capabilities"""
        return self.capabilities
    
    def has_capability(self, capability_name: str) -> bool:
        """Check if adapter has a specific capability"""
        return any(cap.name == capability_name for cap in self.capabilities)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> AdapterResult:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            params: Query parameters
            data: Form data
            json_data: JSON data
            headers: Additional headers
            
        Returns:
            AdapterResult
        """
        # Create session if needed
        if not self._session:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        
        # Build URL
        url = f"{self.config.base_url}/{self.config.api_version}/{endpoint}"
        
        # Get headers
        request_headers = self.config.get_headers()
        if headers:
            request_headers.update(headers)
        
        try:
            # Make request
            async with self._session.request(
                method,
                url,
                params=params,
                data=data,
                json=json_data,
                headers=request_headers
            ) as response:
                # Read response
                try:
                    response_data = await response.json()
                except Exception:
                    response_data = await response.text()
                
                # Check for success
                if 200 <= response.status < 300:
                    return AdapterResult(
                        success=True,
                        data=response_data,
                        status_code=response.status,
                        headers=dict(response.headers)
                    )
                else:
                    error_msg = response_data if isinstance(response_data, str) else json.dumps(response_data)
                    return AdapterResult(
                        success=False,
                        error=error_msg,
                        status_code=response.status,
                        headers=dict(response.headers),
                        data=response_data
                    )
                    
        except aiohttp.ClientError as e:
            return AdapterResult(
                success=False,
                error=str(e),
                metadata={"type": "connection_error"}
            )
        except asyncio.TimeoutError:
            return AdapterResult(
                success=False,
                error="Request timeout",
                metadata={"type": "timeout"}
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e),
                metadata={"type": "unknown_error"}
            )
    
    async def close(self):
        """Close the adapter and clean up resources"""
        if self._session:
            await self._session.close()
            self._session = None
    
    def add_capability(self, capability: AdapterCapability) -> None:
        """Add a capability to the adapter"""
        self.capabilities.append(capability)
    
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
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} status={self.status.value}>"


class AdapterError(Exception):
    """Error raised by adapters"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data


class AdapterAuthError(AdapterError):
    """Authentication error for adapters"""
    pass


class AdapterRateLimitError(AdapterError):
    """Rate limit error for adapters"""
    pass


class AdapterTimeoutError(AdapterError):
    """Timeout error for adapters"""
    pass
