"""
UAW Webhook Server
Сервер для приёма webhook событий
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from http import HTTPStatus
from typing import Any, Callable, Dict, List, Optional, Tuple
import asyncio
import hashlib
import hmac
import json
import logging
import uuid

from uaw.automation.event_manager import EventManager, Event, EventType, EventSource


logger = logging.getLogger(__name__)


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
class WebhookConfig:
    """Конфигурация webhook"""
    webhook_id: str
    provider: WebhookProvider
    endpoint: str
    secret: Optional[str] = None
    events: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "webhook_id": self.webhook_id,
            "provider": self.provider.value,
            "endpoint": self.endpoint,
            "secret": self.secret,
            "events": self.events,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookConfig":
        return cls(
            webhook_id=data.get("webhook_id", ""),
            provider=WebhookProvider(data["provider"]),
            endpoint=data["endpoint"],
            secret=data.get("secret"),
            events=data.get("events", []),
            is_active=data.get("is_active", True),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )


class WebhookHandler:
    """Обработчик webhook запросов"""
    
    def __init__(
        self,
        provider: WebhookProvider,
        secret: Optional[str] = None,
    ):
        self.provider = provider
        self.secret = secret
        
    def verify_signature(
        self,
        payload: bytes,
        signature: Optional[str],
        signature_header: str = "X-Hub-Signature-256",
    ) -> bool:
        """
        Проверка подписи webhook
        
        Args:
            payload: Тело запроса
            signature: Подпись из заголовка
            signature_header: Имя заголовка с подписью
            
        Returns:
            bool: True если подпись верна
        """
        if not self.secret or not signature:
            return True  # Если нет секрета, пропускаем проверку
            
        # GitHub использует sha256
        if self.provider == WebhookProvider.GITHUB:
            expected_signature = f"sha256={hmac.new(
                self.secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()}"
            return hmac.compare_digest(expected_signature, signature)
            
        # Vercel использует sha1
        elif self.provider == WebhookProvider.VERCEL:
            expected_signature = hmac.new(
                self.secret.encode(),
                payload,
                hashlib.sha1
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
            
        # Netlify использует sha256
        elif self.provider == WebhookProvider.NETLIFY:
            expected_signature = hmac.new(
                self.secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
            
        # Для остальных - общая проверка
        else:
            expected_signature = hmac.new(
                self.secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
            
    def parse_payload(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Tuple[EventType, EventSource, Dict[str, Any]]:
        """
        Парсинг payload webhook
        
        Args:
            payload: Тело запроса
            headers: Заголовки
            
        Returns:
            Tuple[EventType, EventSource, payload]
        """
        # Определение типа события и источника
        if self.provider == WebhookProvider.GITHUB:
            event_type = headers.get("X-GitHub-Event", "push")
            event_source = EventSource.GITHUB
            
            # Маппинг GitHub событий
            event_type_mapping = {
                "push": EventType.GITHUB_PUSH,
                "pull_request": EventType.GITHUB_PULL_REQUEST,
                "issues": EventType.GITHUB_ISSUE,
                "commit_comment": EventType.GITHUB_COMMIT,
                "workflow_run": EventType.GITHUB_WORKFLOW_RUN,
                "release": EventType.GITHUB_RELEASE,
                "deployment": EventType.GITHUB_DEPLOYMENT,
            }
            
            return (
                event_type_mapping.get(event_type, EventType.WEBHOOK_TRIGGER),
                event_source,
                payload,
            )
            
        elif self.provider == WebhookProvider.LINEAR:
            event_type = payload.get("type", "issue_created")
            event_source = EventSource.LINEAR
            
            event_type_mapping = {
                "IssueCreated": EventType.LINEAR_ISSUE_CREATED,
                "IssueUpdated": EventType.LINEAR_ISSUE_UPDATED,
                "IssueStatusChanged": EventType.LINEAR_ISSUE_STATUS_CHANGED,
                "IssueAssigned": EventType.LINEAR_ISSUE_ASSIGNED,
                "ProjectCreated": EventType.LINEAR_PROJECT_CREATED,
            }
            
            return (
                event_type_mapping.get(event_type, EventType.WEBHOOK_TRIGGER),
                event_source,
                payload,
            )
            
        elif self.provider == WebhookProvider.ASANE:
            event_type = payload.get("type", "task_created")
            event_source = EventSource.ASANE
            
            event_type_mapping = {
                "task_created": EventType.ASANE_TASK_CREATED,
                "task_updated": EventType.ASANE_TASK_UPDATED,
                "task_completed": EventType.ASANE_TASK_COMPLETED,
                "project_created": EventType.ASANE_PROJECT_CREATED,
            }
            
            return (
                event_type_mapping.get(event_type, EventType.WEBHOOK_TRIGGER),
                event_source,
                payload,
            )
            
        elif self.provider == WebhookProvider.VERCEL:
            event_type = payload.get("type", "deployment_created")
            event_source = EventSource.VERCEL
            
            event_type_mapping = {
                "deployment.created": EventType.VERCEL_DEPLOYMENT_CREATED,
                "deployment.ready": EventType.VERCEL_DEPLOYMENT_COMPLETED,
                "deployment.errored": EventType.VERCEL_DEPLOYMENT_FAILED,
            }
            
            return (
                event_type_mapping.get(event_type, EventType.WEBHOOK_TRIGGER),
                event_source,
                payload,
            )
            
        elif self.provider == WebhookProvider.NETLIFY:
            event_type = payload.get("event", "deploy_started")
            event_source = EventSource.NETLIFY
            
            event_type_mapping = {
                "deploy/started": EventType.NETLIFY_DEPLOY_STARTED,
                "deploy/success": EventType.NETLIFY_DEPLOY_COMPLETED,
                "deploy/failed": EventType.NETLIFY_DEPLOY_FAILED,
            }
            
            return (
                event_type_mapping.get(event_type, EventType.WEBHOOK_TRIGGER),
                event_source,
                payload,
            )
            
        else:
            # Общий случай
            return (
                EventType.WEBHOOK_TRIGGER,
                EventSource.WEBHOOK,
                payload,
            )


@dataclass
class WebhookResponse:
    """Ответ webhook"""
    status: HTTPStatus
    body: Dict[str, Any]
    headers: Dict[str, str] = field(default_factory=dict)


class WebhookServer:
    """
    Сервер для приёма webhook событий
    
    Обрабатывает:
    - Проверку подписи
    - Парсинг payload
    - Преобразование в Event
    - Передача в EventManager
    """
    
    def __init__(
        self,
        event_manager: Optional[EventManager] = None,
        host: str = "0.0.0.0",
        port: int = 8080,
    ):
        self.event_manager = event_manager or EventManager()
        self.host = host
        self.port = port
        
        # Конфигурации webhook
        self.webhook_configs: Dict[str, WebhookConfig] = {}
        
        # Обработчики по провайдерам
        self.handlers: Dict[WebhookProvider, WebhookHandler] = {}
        
        # Статистика
        self.stats: Dict[str, int] = {
            "requests_received": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "signature_failures": 0,
        }
        
        # Флаг работы
        self.running = False
        self.server: Optional[Any] = None
        
    def register_webhook(
        self,
        provider: WebhookProvider,
        endpoint: str,
        secret: Optional[str] = None,
        events: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Регистрация webhook конфигурации
        
        Args:
            provider: Провайдер
            endpoint: URL endpoint
            secret: Секрет для проверки подписи
            events: Список событий
            metadata: Метаданные
            
        Returns:
            str: ID webhook
        """
        webhook_id = f"webhook:{uuid.uuid4()}"
        config = WebhookConfig(
            webhook_id=webhook_id,
            provider=provider,
            endpoint=endpoint,
            secret=secret,
            events=events or [],
            metadata=metadata or {},
        )
        self.webhook_configs[webhook_id] = config
        
        # Создание обработчика
        self.handlers[provider] = WebhookHandler(provider, secret)
        
        logger.info(f"Registered webhook {webhook_id} for {provider.value}")
        return webhook_id
        
    def unregister_webhook(self, webhook_id: str) -> bool:
        """Удаление webhook конфигурации"""
        if webhook_id in self.webhook_configs:
            config = self.webhook_configs[webhook_id]
            del self.webhook_configs[webhook_id]
            if config.provider in self.handlers:
                del self.handlers[config.provider]
            logger.info(f"Unregistered webhook {webhook_id}")
            return True
        return False
        
    def get_webhook_config(self, webhook_id: str) -> Optional[WebhookConfig]:
        """Получение конфигурации webhook"""
        return self.webhook_configs.get(webhook_id)
        
    def get_webhook_by_provider(self, provider: WebhookProvider) -> Optional[WebhookConfig]:
        """Получение конфигурации по провайдеру"""
        for config in self.webhook_configs.values():
            if config.provider == provider:
                return config
        return None
        
    async def handle_webhook_request(
        self,
        provider: WebhookProvider,
        payload: bytes,
        headers: Dict[str, str],
    ) -> WebhookResponse:
        """
        Обработка webhook запроса
        
        Args:
            provider: Провайдер
            payload: Тело запроса
            headers: Заголовки
            
        Returns:
            WebhookResponse
        """
        self.stats["requests_received"] += 1
        
        # Получение конфигурации
        config = self.get_webhook_by_provider(provider)
        if not config:
            logger.warning(f"No webhook config for provider {provider.value}")
            return WebhookResponse(
                status=HTTPStatus.NOT_FOUND,
                body={"error": "Webhook not configured"},
            )
            
        # Проверка подписи
        handler = self.handlers.get(provider)
        if handler:
            signature = headers.get("X-Hub-Signature-256") or headers.get("X-Hub-Signature")
            if not handler.verify_signature(payload, signature):
                self.stats["signature_failures"] += 1
                logger.warning(f"Signature verification failed for {provider.value}")
                return WebhookResponse(
                    status=HTTPStatus.FORBIDDEN,
                    body={"error": "Invalid signature"},
                )
                
        # Парсинг payload
        try:
            payload_dict = json.loads(payload)
        except json.JSONDecodeError:
            return WebhookResponse(
                status=HTTPStatus.BAD_REQUEST,
                body={"error": "Invalid JSON"},
            )
            
        # Определение типа события
        event_type, event_source, parsed_payload = handler.parse_payload(
            payload_dict, headers
        )
        
        # Создание события
        event = Event(
            event_id="",
            event_type=event_type,
            source=event_source,
            timestamp=datetime.utcnow(),
            payload=parsed_payload,
            raw_data={"headers": headers, "payload": payload_dict},
            metadata={"webhook_id": config.webhook_id},
        )
        
        # Эмиссия события
        try:
            await self.event_manager.emit_event(event)
            self.stats["requests_successful"] += 1
            return WebhookResponse(
                status=HTTPStatus.OK,
                body={"status": "accepted", "event_id": event.event_id},
            )
        except Exception as e:
            self.stats["requests_failed"] += 1
            logger.error(f"Failed to emit event: {e}")
            return WebhookResponse(
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                body={"error": str(e)},
            )
            
    async def start(self) -> None:
        """Запуск сервера"""
        if self.running:
            return
            
        self.running = True
        logger.info(f"Webhook server starting on {self.host}:{self.port}")
        
        # В реальной реализации здесь будет HTTP сервер
        # Для демонстрации просто логируем
        logger.info("Webhook server ready (mock mode)")
        
    async def stop(self) -> None:
        """Остановка сервера"""
        self.running = False
        logger.info("Webhook server stopped")
        
    def get_stats(self) -> Dict[str, int]:
        """Получение статистики"""
        return self.stats.copy()
        
    def reset_stats(self) -> None:
        """Сброс статистики"""
        self.stats = {
            "requests_received": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "signature_failures": 0,
        }
