"""
UAW Integration Configuration
Конфигурация интеграций
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging


logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    """Статусы интеграций"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PARTIAL = "partial"
    READ_ONLY = "read_only"
    UNAUTHORISED = "unauthorised"
    UNAVAILABLE = "unavailable"


class AuthenticationType(Enum):
    """Типы аутентификации"""
    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    OAUTH1 = "oauth1"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    JWT = "jwt"


@dataclass
class IntegrationSettings:
    """Настройки интеграции"""
    integration_id: str
    name: str
    service: str
    
    # Аутентификация
    auth_type: AuthenticationType = AuthenticationType.NONE
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Подключение
    base_url: str = ""
    status: IntegrationStatus = IntegrationStatus.DISCONNECTED
    
    # Rate limits
    rate_limit: Optional[int] = None
    rate_limit_period: int = 60  # секунды
    
    # Настройки
    timeout: int = 30  # секунды
    retry_count: int = 3
    retry_delay: int = 10  # секунды
    
    # Метаданные
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Создание
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "integration_id": self.integration_id,
            "name": self.name,
            "service": self.service,
            "auth_type": self.auth_type.value,
            "base_url": self.base_url,
            "status": self.status.value,
            "rate_limit": self.rate_limit,
            "rate_limit_period": self.rate_limit_period,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntegrationSettings":
        return cls(
            integration_id=data.get("integration_id", ""),
            name=data.get("name", ""),
            service=data.get("service", ""),
            auth_type=AuthenticationType(data.get("auth_type", "none")),
            api_key=data.get("api_key"),
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token"),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            username=data.get("username"),
            password=data.get("password"),
            base_url=data.get("base_url", ""),
            status=IntegrationStatus(data.get("status", "disconnected")),
            rate_limit=data.get("rate_limit"),
            rate_limit_period=data.get("rate_limit_period", 60),
            timeout=data.get("timeout", 30),
            retry_count=data.get("retry_count", 3),
            retry_delay=data.get("retry_delay", 10),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
    
    def is_authenticated(self) -> bool:
        """Проверка, аутентифицирована ли интеграция"""
        if self.auth_type == AuthenticationType.NONE:
            return True
        elif self.auth_type == AuthenticationType.API_KEY:
            return self.api_key is not None
        elif self.auth_type == AuthenticationType.OAUTH2:
            return self.access_token is not None
        elif self.auth_type == AuthenticationType.BEARER_TOKEN:
            return self.access_token is not None
        elif self.auth_type == AuthenticationType.BASIC_AUTH:
            return self.username is not None and self.password is not None
        return False
    
    def is_connected(self) -> bool:
        """Проверка, подключена ли интеграция"""
        return self.status == IntegrationStatus.CONNECTED


@dataclass
class IntegrationConfig:
    """Конфигурация всех интеграций"""
    integrations: Dict[str, IntegrationSettings] = field(default_factory=dict)
    default_settings: IntegrationSettings = field(default_factory=lambda: IntegrationSettings(
        integration_id="default",
        name="Default",
        service="default",
    ))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "integrations": {k: v.to_dict() for k, v in self.integrations.items()},
            "default_settings": self.default_settings.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntegrationConfig":
        integrations = {}
        for key, value in data.get("integrations", {}).items():
            integrations[key] = IntegrationSettings.from_dict(value)
        
        default_settings = IntegrationSettings.from_dict(data.get("default_settings", {}))
        return cls(integrations=integrations, default_settings=default_settings)
    
    def add_integration(self, settings: IntegrationSettings) -> None:
        """Добавление интеграции"""
        self.integrations[settings.integration_id] = settings
        logger.info(f"Added integration: {settings.name}")
        
    def remove_integration(self, integration_id: str) -> bool:
        """Удаление интеграции"""
        if integration_id in self.integrations:
            del self.integrations[integration_id]
            logger.info(f"Removed integration: {integration_id}")
            return True
        return False
    
    def get_integration(self, integration_id: str) -> Optional[IntegrationSettings]:
        """Получение интеграции"""
        return self.integrations.get(integration_id)
    
    def get_integration_by_service(self, service: str) -> Optional[IntegrationSettings]:
        """Получение интеграции по сервису"""
        for settings in self.integrations.values():
            if settings.service == service:
                return settings
        return None
    
    def list_integrations(self) -> List[IntegrationSettings]:
        """Получение списка всех интеграций"""
        return list(self.integrations.values())
    
    def list_connected_integrations(self) -> List[IntegrationSettings]:
        """Получение списка подключенных интеграций"""
        return [s for s in self.integrations.values() if s.is_connected()]
    
    def list_authenticated_integrations(self) -> List[IntegrationSettings]:
        """Получение списка аутентифицированных интеграций"""
        return [s for s in self.integrations.values() if s.is_authenticated()]


# Стандартные конфигурации для известных интеграций
STANDARD_INTEGRATION_CONFIGS = {
    "github": {
        "name": "GitHub",
        "service": "github",
        "auth_type": "bearer_token",
        "base_url": "https://api.github.com",
        "rate_limit": 5000,
        "rate_limit_period": 3600,
        "timeout": 30,
        "retry_count": 3,
        "retry_delay": 10,
    },
    "asana": {
        "name": "Asana",
        "service": "asana",
        "auth_type": "api_key",
        "base_url": "https://app.asana.com/api/1.0",
        "rate_limit": 100,
        "rate_limit_period": 60,
        "timeout": 30,
        "retry_count": 3,
        "retry_delay": 10,
    },
    "linear": {
        "name": "Linear",
        "service": "linear",
        "auth_type": "api_key",
        "base_url": "https://api.linear.app",
        "rate_limit": 100,
        "rate_limit_period": 60,
        "timeout": 30,
        "retry_count": 3,
        "retry_delay": 10,
    },
    "google_calendar": {
        "name": "Google Calendar",
        "service": "google_calendar",
        "auth_type": "oauth2",
        "base_url": "https://www.googleapis.com/calendar/v3",
        "rate_limit": 1000000,
        "rate_limit_period": 86400,
        "timeout": 30,
        "retry_count": 3,
        "retry_delay": 10,
    },
    "vercel": {
        "name": "Vercel",
        "service": "vercel",
        "auth_type": "bearer_token",
        "base_url": "https://api.vercel.com",
        "rate_limit": 60,
        "rate_limit_period": 60,
        "timeout": 30,
        "retry_count": 3,
        "retry_delay": 10,
    },
    "teams": {
        "name": "Microsoft Teams",
        "service": "teams",
        "auth_type": "bearer_token",
        "base_url": "https://graph.microsoft.com",
        "rate_limit": 10000,
        "rate_limit_period": 10,
        "timeout": 30,
        "retry_count": 3,
        "retry_delay": 10,
    },
}


def create_standard_config() -> IntegrationConfig:
    """Создание стандартной конфигурации"""
    config = IntegrationConfig()
    
    for integration_id, settings_data in STANDARD_INTEGRATION_CONFIGS.items():
        settings = IntegrationSettings(
            integration_id=f"integration:{integration_id}",
            name=settings_data["name"],
            service=settings_data["service"],
            auth_type=AuthenticationType(settings_data["auth_type"]),
            base_url=settings_data["base_url"],
            rate_limit=settings_data["rate_limit"],
            rate_limit_period=settings_data["rate_limit_period"],
            timeout=settings_data["timeout"],
            retry_count=settings_data["retry_count"],
            retry_delay=settings_data["retry_delay"],
        )
        config.add_integration(settings)
        
    return config
