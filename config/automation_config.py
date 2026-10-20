"""
UAW Automation Configuration
Конфигурация автоматизации
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import logging


logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Типы триггеров"""
    WEBHOOK = "webhook"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    EVENT = "event"
    POLLING = "polling"


class WebhookProvider(Enum):
    """Провайдеры webhook"""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    LINEAR = "linear"
    ASANE = "asana"
    NOTION = "notion"
    BOX = "box"
    GOOGLE_CALENDAR = "google_calendar"
    OUTLOOK_CALENDAR = "outlook_calendar"
    VERCEL = "vercel"
    NETLIFY = "netlify"
    WIX = "wix"
    SLACK = "slack"
    TEAMS = "teams"
    GENERIC = "generic"


@dataclass
class TriggerConfig:
    """Конфигурация триггера"""
    trigger_id: str
    name: str
    trigger_type: TriggerType
    
    # Для webhook триггеров
    webhook_provider: Optional[WebhookProvider] = None
    webhook_endpoint: str = ""
    webhook_secret: Optional[str] = None
    webhook_events: List[str] = field(default_factory=list)
    
    # Для scheduled триггеров
    schedule: Optional[str] = None  # cron expression
    timezone: str = "UTC"
    
    # Для event триггеров
    event_type: Optional[str] = None
    event_source: Optional[str] = None
    
    # Условия
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Действия
    actions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Настройки
    is_enabled: bool = True
    priority: int = 0
    max_concurrent_executions: int = 1
    
    # Статистика
    executions_count: int = 0
    last_execution: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    
    # Создание
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "name": self.name,
            "trigger_type": self.trigger_type.value,
            "webhook_provider": self.webhook_provider.value if self.webhook_provider else None,
            "webhook_endpoint": self.webhook_endpoint,
            "webhook_events": self.webhook_events,
            "schedule": self.schedule,
            "timezone": self.timezone,
            "event_type": self.event_type,
            "event_source": self.event_source,
            "conditions": self.conditions,
            "actions": self.actions,
            "is_enabled": self.is_enabled,
            "priority": self.priority,
            "max_concurrent_executions": self.max_concurrent_executions,
            "executions_count": self.executions_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriggerConfig":
        return cls(
            trigger_id=data.get("trigger_id", ""),
            name=data.get("name", ""),
            trigger_type=TriggerType(data.get("trigger_type", "manual")),
            webhook_provider=WebhookProvider(data["webhook_provider"]) if data.get("webhook_provider") else None,
            webhook_endpoint=data.get("webhook_endpoint", ""),
            webhook_secret=data.get("webhook_secret"),
            webhook_events=data.get("webhook_events", []),
            schedule=data.get("schedule"),
            timezone=data.get("timezone", "UTC"),
            event_type=data.get("event_type"),
            event_source=data.get("event_source"),
            conditions=data.get("conditions", {}),
            actions=data.get("actions", []),
            is_enabled=data.get("is_enabled", True),
            priority=data.get("priority", 0),
            max_concurrent_executions=data.get("max_concurrent_executions", 1),
            executions_count=data.get("executions_count", 0),
            last_execution=datetime.fromisoformat(data["last_execution"]) if data.get("last_execution") else None,
            last_success=datetime.fromisoformat(data["last_success"]) if data.get("last_success") else None,
            last_failure=datetime.fromisoformat(data["last_failure"]) if data.get("last_failure") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class WebhookConfig:
    """Конфигурация webhook"""
    webhook_id: str
    name: str
    provider: WebhookProvider
    endpoint: str
    
    # Аутентификация
    secret: Optional[str] = None
    auth_token: Optional[str] = None
    
    # События
    events: List[str] = field(default_factory=list)
    
    # Настройки
    is_active: bool = True
    verify_signature: bool = True
    
    # Статистика
    requests_received: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    
    # Создание
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "webhook_id": self.webhook_id,
            "name": self.name,
            "provider": self.provider.value,
            "endpoint": self.endpoint,
            "events": self.events,
            "is_active": self.is_active,
            "verify_signature": self.verify_signature,
            "requests_received": self.requests_received,
            "requests_successful": self.requests_successful,
            "requests_failed": self.requests_failed,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookConfig":
        return cls(
            webhook_id=data.get("webhook_id", ""),
            name=data.get("name", ""),
            provider=WebhookProvider(data["provider"]),
            endpoint=data.get("endpoint", ""),
            secret=data.get("secret"),
            auth_token=data.get("auth_token"),
            events=data.get("events", []),
            is_active=data.get("is_active", True),
            verify_signature=data.get("verify_signature", True),
            requests_received=data.get("requests_received", 0),
            requests_successful=data.get("requests_successful", 0),
            requests_failed=data.get("requests_failed", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class AutomationConfig:
    """Конфигурация автоматизации"""
    
    # Общие настройки
    enabled: bool = True
    debug_mode: bool = False
    
    # Триггеры
    triggers: Dict[str, TriggerConfig] = field(default_factory=dict)
    
    # Webhook
    webhooks: Dict[str, WebhookConfig] = field(default_factory=dict)
    
    # Настройки выполнения
    max_concurrent_workflows: int = 10
    max_queue_size: int = 100
    default_timeout: int = 300  # секунды
    default_retry_count: int = 3
    default_retry_delay: int = 10  # секунды
    
    # Настройки планировщика
    scheduler_enabled: bool = True
    scheduler_interval: int = 60  # секунды
    
    # Настройки дедубликации
    deduplication_enabled: bool = True
    deduplication_window: int = 3600  # секунды
    
    # Настройки логирования
    log_level: str = "INFO"
    log_format: str = "json"
    log_retention_days: int = 30
    
    # Создание
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "debug_mode": self.debug_mode,
            "triggers": {k: v.to_dict() for k, v in self.triggers.items()},
            "webhooks": {k: v.to_dict() for k, v in self.webhooks.items()},
            "max_concurrent_workflows": self.max_concurrent_workflows,
            "max_queue_size": self.max_queue_size,
            "default_timeout": self.default_timeout,
            "default_retry_count": self.default_retry_count,
            "default_retry_delay": self.default_retry_delay,
            "scheduler_enabled": self.scheduler_enabled,
            "scheduler_interval": self.scheduler_interval,
            "deduplication_enabled": self.deduplication_enabled,
            "deduplication_window": self.deduplication_window,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "log_retention_days": self.log_retention_days,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutomationConfig":
        triggers = {}
        for k, v in data.get("triggers", {}).items():
            triggers[k] = TriggerConfig.from_dict(v)
            
        webhooks = {}
        for k, v in data.get("webhooks", {}).items():
            webhooks[k] = WebhookConfig.from_dict(v)
            
        return cls(
            enabled=data.get("enabled", True),
            debug_mode=data.get("debug_mode", False),
            triggers=triggers,
            webhooks=webhooks,
            max_concurrent_workflows=data.get("max_concurrent_workflows", 10),
            max_queue_size=data.get("max_queue_size", 100),
            default_timeout=data.get("default_timeout", 300),
            default_retry_count=data.get("default_retry_count", 3),
            default_retry_delay=data.get("default_retry_delay", 10),
            scheduler_enabled=data.get("scheduler_enabled", True),
            scheduler_interval=data.get("scheduler_interval", 60),
            deduplication_enabled=data.get("deduplication_enabled", True),
            deduplication_window=data.get("deduplication_window", 3600),
            log_level=data.get("log_level", "INFO"),
            log_format=data.get("log_format", "json"),
            log_retention_days=data.get("log_retention_days", 30),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
    
    def add_trigger(self, trigger: TriggerConfig) -> None:
        """Добавление триггера"""
        self.triggers[trigger.trigger_id] = trigger
        self.updated_at = datetime.utcnow()
        logger.info(f"Added trigger: {trigger.name}")
        
    def remove_trigger(self, trigger_id: str) -> bool:
        """Удаление триггера"""
        if trigger_id in self.triggers:
            del self.triggers[trigger_id]
            self.updated_at = datetime.utcnow()
            logger.info(f"Removed trigger: {trigger_id}")
            return True
        return False
    
    def get_trigger(self, trigger_id: str) -> Optional[TriggerConfig]:
        """Получение триггера"""
        return self.triggers.get(trigger_id)
    
    def list_triggers(self) -> List[TriggerConfig]:
        """Получение списка всех триггеров"""
        return list(self.triggers.values())
    
    def add_webhook(self, webhook: WebhookConfig) -> None:
        """Добавление webhook"""
        self.webhooks[webhook.webhook_id] = webhook
        self.updated_at = datetime.utcnow()
        logger.info(f"Added webhook: {webhook.name}")
        
    def remove_webhook(self, webhook_id: str) -> bool:
        """Удаление webhook"""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            self.updated_at = datetime.utcnow()
            logger.info(f"Removed webhook: {webhook_id}")
            return True
        return False
    
    def get_webhook(self, webhook_id: str) -> Optional[WebhookConfig]:
        """Получение webhook"""
        return self.webhooks.get(webhook_id)
    
    def list_webhooks(self) -> List[WebhookConfig]:
        """Получение списка всех webhook"""
        return list(self.webhooks.values())
    
    def get_webhook_by_provider(self, provider: WebhookProvider) -> Optional[WebhookConfig]:
        """Получение webhook по провайдеру"""
        for webhook in self.webhooks.values():
            if webhook.provider == provider:
                return webhook
        return None


# Стандартные конфигурации триггеров
STANDARD_TRIGGER_CONFIGS = [
    {
        "trigger_id": "trigger:github-push-main",
        "name": "GitHub Push to Main",
        "trigger_type": "webhook",
        "webhook_provider": "github",
        "webhook_endpoint": "/webhooks/github",
        "webhook_events": ["push"],
        "conditions": {"ref": "refs/heads/main"},
        "actions": [
            {"action_type": "workflow", "target": "workflow:deploy-staging"}
        ],
        "is_enabled": True,
        "priority": 10,
    },
    {
        "trigger_id": "trigger:github-pr-opened",
        "name": "GitHub PR Opened",
        "trigger_type": "webhook",
        "webhook_provider": "github",
        "webhook_endpoint": "/webhooks/github",
        "webhook_events": ["pull_request"],
        "conditions": {"action": "opened"},
        "actions": [
            {"action_type": "workflow", "target": "workflow:review-pr"}
        ],
        "is_enabled": True,
        "priority": 5,
    },
    {
        "trigger_id": "trigger:daily-check",
        "name": "Daily Health Check",
        "trigger_type": "scheduled",
        "schedule": "0 9 * * *",
        "timezone": "UTC",
        "actions": [
            {"action_type": "workflow", "target": "workflow:health-check"}
        ],
        "is_enabled": True,
        "priority": 1,
    },
    {
        "trigger_id": "trigger:weekly-report",
        "name": "Weekly Report",
        "trigger_type": "scheduled",
        "schedule": "0 17 * * 1",  # Каждый понедельник в 17:00
        "timezone": "UTC",
        "actions": [
            {"action_type": "workflow", "target": "workflow:generate-report"}
        ],
        "is_enabled": True,
        "priority": 1,
    },
]


def create_standard_automation_config() -> AutomationConfig:
    """Создание стандартной конфигурации автоматизации"""
    config = AutomationConfig()
    
    for trigger_data in STANDARD_TRIGGER_CONFIGS:
        trigger = TriggerConfig(
            trigger_id=trigger_data["trigger_id"],
            name=trigger_data["name"],
            trigger_type=TriggerType(trigger_data["trigger_type"]),
            webhook_provider=WebhookProvider(trigger_data["webhook_provider"]) if trigger_data.get("webhook_provider") else None,
            webhook_endpoint=trigger_data.get("webhook_endpoint", ""),
            webhook_events=trigger_data.get("webhook_events", []),
            schedule=trigger_data.get("schedule"),
            timezone=trigger_data.get("timezone", "UTC"),
            conditions=trigger_data.get("conditions", {}),
            actions=trigger_data.get("actions", []),
            is_enabled=trigger_data.get("is_enabled", True),
            priority=trigger_data.get("priority", 0),
        )
        config.add_trigger(trigger)
        
    return config
