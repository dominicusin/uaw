"""
UAW Security Configuration
Конфигурация безопасности
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import hashlib
import secrets
import logging


logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Уровни разрешений"""
    L0_READ_ONLY = "L0_READ_ONLY"
    L1_PREPARE = "L1_PREPARE"
    L2_SUPERVISED = "L2_SUPERVISED"
    L3_POLICY_BASED = "L3_POLICY_BASED"
    L4_RESTRICTED = "L4_RESTRICTED"


class ActionCategory(Enum):
    """Категории действий"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    CRITICAL = "critical"


@dataclass
class PermissionConfig:
    """Конфигурация разрешений"""
    user_id: str
    username: str
    
    # Уровень доступа по умолчанию
    default_level: PermissionLevel = PermissionLevel.L0_READ_ONLY
    
    # Разрешения для интеграций
    integration_permissions: Dict[str, PermissionLevel] = field(default_factory=dict)
    
    # Разрешения для действий
    action_permissions: Dict[str, PermissionLevel] = field(default_factory=dict)
    
    # Разрешения для ресурсов
    resource_permissions: Dict[str, PermissionLevel] = field(default_factory=dict)
    
    # Роли
    roles: List[str] = field(default_factory=list)
    
    # Группы
    groups: List[str] = field(default_factory=list)
    
    # Временные разрешения
    temporary_permissions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Создание
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "default_level": self.default_level.value,
            "integration_permissions": {k: v.value for k, v in self.integration_permissions.items()},
            "action_permissions": {k: v.value for k, v in self.action_permissions.items()},
            "resource_permissions": {k: v.value for k, v in self.resource_permissions.items()},
            "roles": self.roles,
            "groups": self.groups,
            "temporary_permissions": self.temporary_permissions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PermissionConfig":
        integration_permissions = {}
        for k, v in data.get("integration_permissions", {}).items():
            integration_permissions[k] = PermissionLevel(v)
            
        action_permissions = {}
        for k, v in data.get("action_permissions", {}).items():
            action_permissions[k] = PermissionLevel(v)
            
        resource_permissions = {}
        for k, v in data.get("resource_permissions", {}).items():
            resource_permissions[k] = PermissionLevel(v)
            
        return cls(
            user_id=data.get("user_id", ""),
            username=data.get("username", ""),
            default_level=PermissionLevel(data.get("default_level", "L0_READ_ONLY")),
            integration_permissions=integration_permissions,
            action_permissions=action_permissions,
            resource_permissions=resource_permissions,
            roles=data.get("roles", []),
            groups=data.get("groups", []),
            temporary_permissions=data.get("temporary_permissions", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
    
    def get_permission_level(
        self,
        integration: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
    ) -> PermissionLevel:
        """
        Получение уровня разрешения
        
        Args:
            integration: Интеграция
            action: Действие
            resource: Ресурс
            
        Returns:
            PermissionLevel: Уровень разрешения
        """
        # Проверка временных разрешений
        if resource and resource in self.temporary_permissions:
            temp_perm = self.temporary_permissions[resource]
            if temp_perm.get("expires_at"):
                expires_at = datetime.fromisoformat(temp_perm["expires_at"])
                if expires_at > datetime.utcnow():
                    return PermissionLevel(temp_perm["level"])
                    
        # Проверка по ресурсу
        if resource and resource in self.resource_permissions:
            return self.resource_permissions[resource]
            
        # Проверка по действию
        if action and action in self.action_permissions:
            return self.action_permissions[action]
            
        # Проверка по интеграции
        if integration and integration in self.integration_permissions:
            return self.integration_permissions[integration]
            
        # Уровень по умолчанию
        return self.default_level
    
    def has_permission(
        self,
        required_level: PermissionLevel,
        integration: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
    ) -> bool:
        """
        Проверка наличия разрешения
        
        Args:
            required_level: Требуемый уровень
            integration: Интеграция
            action: Действие
            resource: Ресурс
            
        Returns:
            bool: True если разрешение есть
        """
        user_level = self.get_permission_level(integration, action, resource)
        
        # Сравнение уровней
        level_order = {
            PermissionLevel.L0_READ_ONLY: 0,
            PermissionLevel.L1_PREPARE: 1,
            PermissionLevel.L2_SUPERVISED: 2,
            PermissionLevel.L3_POLICY_BASED: 3,
            PermissionLevel.L4_RESTRICTED: 4,
        }
        
        return level_order[user_level] >= level_order[required_level]
    
    def add_permission(
        self,
        target: str,
        level: PermissionLevel,
        target_type: str = "action",
    ) -> None:
        """
        Добавление разрешения
        
        Args:
            target: Цель (интеграция, действие или ресурс)
            level: Уровень разрешения
            target_type: Тип цели (integration, action, resource)
        """
        if target_type == "integration":
            self.integration_permissions[target] = level
        elif target_type == "action":
            self.action_permissions[target] = level
        elif target_type == "resource":
            self.resource_permissions[target] = level
            
        self.updated_at = datetime.utcnow()
        logger.info(f"Added permission: {target_type}={target}, level={level.value}")
    
    def remove_permission(
        self,
        target: str,
        target_type: str = "action",
    ) -> bool:
        """
        Удаление разрешения
        
        Args:
            target: Цель
            target_type: Тип цели
            
        Returns:
            bool: True если разрешение было удалено
        """
        if target_type == "integration" and target in self.integration_permissions:
            del self.integration_permissions[target]
        elif target_type == "action" and target in self.action_permissions:
            del self.action_permissions[target]
        elif target_type == "resource" and target in self.resource_permissions:
            del self.resource_permissions[target]
        else:
            return False
            
        self.updated_at = datetime.utcnow()
        logger.info(f"Removed permission: {target_type}={target}")
        return True


@dataclass
class SecurityConfig:
    """Конфигурация безопасности"""
    
    # Общие настройки
    enabled: bool = True
    debug_mode: bool = False
    
    # Уровни доступа по умолчанию
    default_user_level: PermissionLevel = PermissionLevel.L0_READ_ONLY
    default_integration_level: PermissionLevel = PermissionLevel.L0_READ_ONLY
    
    # Настройки аутентификации
    session_timeout: int = 3600  # секунды
    token_expiration: int = 86400  # секунды
    refresh_token_expiration: int = 2592000  # 30 дней
    
    # Настройки токенов
    token_algorithm: str = "HS256"
    token_secret: Optional[str] = None
    
    # Разрешенные действия для уровней
    level_permissions: Dict[str, List[str]] = field(default_factory=dict)
    
    # Запрещенные действия
    blocked_actions: Set[str] = field(default_factory=set)
    
    # Разрешенные интеграции
    allowed_integrations: Set[str] = field(default_factory=set)
    
    # Запрещенные интеграции
    blocked_integrations: Set[str] = field(default_factory=set)
    
    # Настройки аудита
    audit_enabled: bool = True
    audit_retention_days: int = 90
    audit_max_events: int = 10000
    
    # Настройки rate limiting
    rate_limit_enabled: bool = True
    rate_limit_window: int = 60  # секунды
    rate_limit_max_requests: int = 100
    
    # Создание
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        # Генерация секрета если не указан
        if self.token_secret is None:
            self.token_secret = secrets.token_hex(32)
            
        # Стандартные разрешения для уровней
        if not self.level_permissions:
            self.level_permissions = {
                "L0_READ_ONLY": [
                    "list_*",
                    "get_*",
                    "search_*",
                    "read_*",
                ],
                "L1_PREPARE": [
                    "create_draft_*",
                    "prepare_*",
                    "plan_*",
                ],
                "L2_SUPERVISED": [
                    "create_*",
                    "update_*",
                    "delete_*",
                    "send_*",
                ],
                "L3_POLICY_BASED": [
                    "deploy_*",
                    "run_*",
                    "execute_*",
                ],
                "L4_RESTRICTED": [
                    "delete_production_*",
                    "modify_secrets_*",
                    "change_permissions_*",
                ],
            }
            
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "debug_mode": self.debug_mode,
            "default_user_level": self.default_user_level.value,
            "default_integration_level": self.default_integration_level.value,
            "session_timeout": self.session_timeout,
            "token_expiration": self.token_expiration,
            "refresh_token_expiration": self.refresh_token_expiration,
            "token_algorithm": self.token_algorithm,
            "level_permissions": self.level_permissions,
            "blocked_actions": list(self.blocked_actions),
            "allowed_integrations": list(self.allowed_integrations),
            "blocked_integrations": list(self.blocked_integrations),
            "audit_enabled": self.audit_enabled,
            "audit_retention_days": self.audit_retention_days,
            "audit_max_events": self.audit_max_events,
            "rate_limit_enabled": self.rate_limit_enabled,
            "rate_limit_window": self.rate_limit_window,
            "rate_limit_max_requests": self.rate_limit_max_requests,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityConfig":
        return cls(
            enabled=data.get("enabled", True),
            debug_mode=data.get("debug_mode", False),
            default_user_level=PermissionLevel(data.get("default_user_level", "L0_READ_ONLY")),
            default_integration_level=PermissionLevel(data.get("default_integration_level", "L0_READ_ONLY")),
            session_timeout=data.get("session_timeout", 3600),
            token_expiration=data.get("token_expiration", 86400),
            refresh_token_expiration=data.get("refresh_token_expiration", 2592000),
            token_algorithm=data.get("token_algorithm", "HS256"),
            token_secret=data.get("token_secret"),
            level_permissions=data.get("level_permissions", {}),
            blocked_actions=set(data.get("blocked_actions", [])),
            allowed_integrations=set(data.get("allowed_integrations", [])),
            blocked_integrations=set(data.get("blocked_integrations", [])),
            audit_enabled=data.get("audit_enabled", True),
            audit_retention_days=data.get("audit_retention_days", 90),
            audit_max_events=data.get("audit_max_events", 10000),
            rate_limit_enabled=data.get("rate_limit_enabled", True),
            rate_limit_window=data.get("rate_limit_window", 60),
            rate_limit_max_requests=data.get("rate_limit_max_requests", 100),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
    
    def generate_session_token(self, user_id: str) -> str:
        """Генерация сессионного токена"""
        import time
        timestamp = str(int(time.time()))
        random_str = secrets.token_hex(16)
        data = f"{user_id}:{timestamp}:{random_str}"
        
        if self.token_secret:
            import hmac
            signature = hmac.new(
                self.token_secret.encode(),
                data.encode(),
                getattr(hashlib, self.token_algorithm.lower())
            ).hexdigest()
            return f"{data}:{signature}"
        else:
            return data
    
    def validate_session_token(self, token: str) -> Optional[str]:
        """
        Валидация сессионного токена
        
        Args:
            token: Токен для валидации
            
        Returns:
            Optional[str]: user_id если токен валиден, иначе None
        """
        if self.token_secret is None:
            return None
            
        try:
            parts = token.rsplit(":", 1)
            if len(parts) != 2:
                return None
                
            data, signature = parts
            
            import hmac
            expected_signature = hmac.new(
                self.token_secret.encode(),
                data.encode(),
                getattr(hashlib, self.token_algorithm.lower())
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
                
            # Извлечение user_id
            user_id = data.split(":")[0]
            return user_id
            
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return None
    
    def is_action_blocked(self, action: str) -> bool:
        """Проверка, заблокировано ли действие"""
        return action in self.blocked_actions
    
    def is_integration_blocked(self, integration: str) -> bool:
        """Проверка, заблокирована ли интеграция"""
        return integration in self.blocked_integrations
    
    def is_integration_allowed(self, integration: str) -> bool:
        """Проверка, разрешена ли интеграция"""
        if self.allowed_integrations:
            return integration in self.allowed_integrations
        return not self.is_integration_blocked(integration)
    
    def get_permissions_for_level(self, level: str) -> List[str]:
        """Получение списка разрешений для уровня"""
        return self.level_permissions.get(level, [])
    
    def can_perform_action(
        self,
        user_level: PermissionLevel,
        action: str,
        integration: Optional[str] = None,
    ) -> bool:
        """
        Проверка, может ли пользователь выполнить действие
        
        Args:
            user_level: Уровень доступа пользователя
            action: Действие
            integration: Интеграция
            
        Returns:
            bool: True если действие разрешено
        """
        # Проверка заблокированных действий
        if self.is_action_blocked(action):
            return False
            
        # Проверка заблокированных интеграций
        if integration and self.is_integration_blocked(integration):
            return False
            
        # Проверка разрешений уровня
        permissions = self.get_permissions_for_level(user_level.value)
        
        # Проверка точного соответствия
        if action in permissions:
            return True
            
        # Проверка с wildcard
        for permission in permissions:
            if permission.endswith("_*"):
                prefix = permission[:-2]
                if action.startswith(prefix + "_"):
                    return True
                    
        return False
