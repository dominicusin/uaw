"""
UAW Event Manager
Управление событиями для event-driven автоматизации
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import asyncio
import hashlib
import json
import logging
import uuid

from uaw.core.audit import AuditLogger, AuditEventType
from uaw.core.security import SecurityManager, PermissionLevel


logger = logging.getLogger(__name__)


class EventType(Enum):
    """Типы событий"""
    # GitHub события
    GITHUB_PUSH = "github.push"
    GITHUB_PULL_REQUEST = "github.pull_request"
    GITHUB_ISSUE = "github.issue"
    GITHUB_COMMIT = "github.commit"
    GITHUB_WORKFLOW_RUN = "github.workflow_run"
    GITHUB_RELEASE = "github.release"
    GITHUB_DEPLOYMENT = "github.deployment"
    
    # Linear события
    LINEAR_ISSUE_CREATED = "linear.issue_created"
    LINEAR_ISSUE_UPDATED = "linear.issue_updated"
    LINEAR_ISSUE_STATUS_CHANGED = "linear.issue_status_changed"
    LINEAR_ISSUE_ASSIGNED = "linear.issue_assigned"
    LINEAR_PROJECT_CREATED = "linear.project_created"
    
    # Asana события
    ASANE_TASK_CREATED = "asana.task_created"
    ASANE_TASK_UPDATED = "asana.task_updated"
    ASANE_TASK_COMPLETED = "asana.task_completed"
    ASANE_PROJECT_CREATED = "asana.project_created"
    
    # Notion события
    NOTION_PAGE_CREATED = "notion.page_created"
    NOTION_PAGE_UPDATED = "notion.page_updated"
    NOTION_DATABASE_UPDATED = "notion.database_updated"
    
    # Box события
    BOX_FILE_UPLOADED = "box.file_uploaded"
    BOX_FILE_UPDATED = "box.file_updated"
    BOX_FOLDER_CREATED = "box.folder_created"
    
    # Calendar события
    CALENDAR_EVENT_CREATED = "calendar.event_created"
    CALENDAR_EVENT_UPDATED = "calendar.event_updated"
    CALENDAR_EVENT_DELETED = "calendar.event_deleted"
    CALENDAR_INVITATION_ACCEPTED = "calendar.invitation_accepted"
    CALENDAR_INVITATION_DECLINED = "calendar.invitation_declined"
    
    # Vercel события
    VERCEL_DEPLOYMENT_CREATED = "vercel.deployment_created"
    VERCEL_DEPLOYMENT_COMPLETED = "vercel.deployment_completed"
    VERCEL_DEPLOYMENT_FAILED = "vercel.deployment_failed"
    
    # Netlify события
    NETLIFY_DEPLOY_STARTED = "netlify.deploy_started"
    NETLIFY_DEPLOY_COMPLETED = "netlify.deploy_completed"
    NETLIFY_DEPLOY_FAILED = "netlify.deploy_failed"
    
    # Wix события
    WIX_SITE_UPDATED = "wix.site_updated"
    WIX_PAGE_CREATED = "wix.page_created"
    WIX_ORDER_CREATED = "wix.order_created"
    WIX_CMS_UPDATED = "wix.cms_updated"
    
    # Teams события
    TEAMS_MESSAGE_SENT = "teams.message_sent"
    TEAMS_MEETING_CREATED = "teams.meeting_created"
    TEAMS_MEETING_UPDATED = "teams.meeting_updated"
    
    # Внутренние события
    INTERNAL_WORKFLOW_STARTED = "internal.workflow_started"
    INTERNAL_WORKFLOW_COMPLETED = "internal.workflow_completed"
    INTERNAL_WORKFLOW_FAILED = "internal.workflow_failed"
    INTERNAL_SCHEDULED_TASK = "internal.scheduled_task"
    INTERNAL_HEALTH_CHECK = "internal.health_check"
    
    # Общие события
    MANUAL_TRIGGER = "manual.trigger"
    SCHEDULED_TRIGGER = "scheduled.trigger"
    WEBHOOK_TRIGGER = "webhook.trigger"


class EventSource(Enum):
    """Источники событий"""
    GITHUB = "github"
    LINEAR = "linear"
    ASANE = "asana"
    NOTION = "notion"
    BOX = "box"
    GOOGLE_CALENDAR = "google_calendar"
    OUTLOOK_CALENDAR = "outlook_calendar"
    VERCEL = "vercel"
    NETLIFY = "netlify"
    WIX = "wix"
    TEAMS = "teams"
    SLACK = "slack"
    INTERNAL = "internal"
    WEBHOOK = "webhook"
    SCHEDULER = "scheduler"


@dataclass
class Event:
    """Событие для обработки"""
    event_id: str
    event_type: EventType
    source: EventSource
    timestamp: datetime
    payload: Dict[str, Any]
    raw_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    processing_attempts: int = 0
    error: Optional[str] = None
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"event:{uuid.uuid4()}"
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
            
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source": self.source.value,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "raw_data": self.raw_data,
            "metadata": self.metadata,
            "processed": self.processed,
            "processing_attempts": self.processing_attempts,
            "error": self.error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        return cls(
            event_id=data.get("event_id", ""),
            event_type=EventType(data["event_type"]),
            source=EventSource(data["source"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            payload=data.get("payload", {}),
            raw_data=data.get("raw_data"),
            metadata=data.get("metadata", {}),
            processed=data.get("processed", False),
            processing_attempts=data.get("processing_attempts", 0),
            error=data.get("error"),
        )
    
    def get_event_key(self) -> str:
        """Получение уникального ключа события для дедубликации"""
        # Используем hash от основных полей
        key_data = f"{self.event_type.value}:{self.source.value}:{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def mark_processed(self, success: bool = True, error: Optional[str] = None) -> None:
        """Отметка события как обработанного"""
        self.processed = True
        if not success:
            self.processing_attempts += 1
            self.error = error


class EventHandler:
    """Обработчик событий"""
    
    def __init__(
        self,
        handler_id: str,
        event_type: EventType,
        source: EventSource,
        callback: Callable[[Event], Any],
        filter_conditions: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        max_retries: int = 3,
    ):
        self.handler_id = handler_id
        self.event_type = event_type
        self.source = source
        self.callback = callback
        self.filter_conditions = filter_conditions or {}
        self.priority = priority
        self.max_retries = max_retries
        
    def matches(self, event: Event) -> bool:
        """Проверка, подходит ли событие для этого обработчика"""
        # Проверка типа события
        if self.event_type != event.event_type:
            return False
        
        # Проверка источника
        if self.source != event.source:
            return False
            
        # Проверка условий фильтрации
        for key, expected_value in self.filter_conditions.items():
            # Проверяем в payload
            if key in event.payload:
                actual_value = event.payload[key]
                if actual_value != expected_value:
                    return False
            # Проверяем в metadata
            elif key in event.metadata:
                actual_value = event.metadata[key]
                if actual_value != expected_value:
                    return False
            else:
                return False
                
        return True
    
    async def handle(self, event: Event) -> bool:
        """
        Обработка события
        
        Args:
            event: Событие для обработки
            
        Returns:
            bool: True если обработка успешна
        """
        try:
            # Вызов callback
            result = self.callback(event)
            
            # Если callback асинхронный
            if asyncio.iscoroutine(result):
                await result
                
            event.mark_processed(success=True)
            return True
            
        except Exception as e:
            event.mark_processed(success=False, error=str(e))
            logger.error(f"Error handling event {event.event_id}: {e}")
            return False


class EventManager:
    """
    Менеджер событий
    
    Управляет:
    - Регистрацией обработчиков
    - Приёмом событий
    - Дедубликацией
    - Очередью обработки
    - Ретраями
    """
    
    def __init__(
        self,
        audit_logger: Optional[AuditLogger] = None,
        security_manager: Optional[SecurityManager] = None,
    ):
        self.audit_logger = audit_logger or AuditLogger()
        self.security_manager = security_manager or SecurityManager()
        
        # Обработчики событий
        self.handlers: List[EventHandler] = []
        
        # Очередь событий
        self.event_queue: asyncio.Queue[Event] = asyncio.Queue()
        
        # History событий (для дедубликации)
        self.processed_events: Dict[str, datetime] = {}
        self.event_history_ttl = 3600  # 1 час
        
        # Активные обработки
        self.active_processing: Dict[str, bool] = {}
        
        # Статистика
        self.stats: Dict[str, int] = {
            "events_received": 0,
            "events_processed": 0,
            "events_failed": 0,
            "events_duplicated": 0,
        }
        
        # Флаг работы
        self.running = False
        self.processor_task: Optional[asyncio.Task] = None
        
    def register_handler(
        self,
        event_type: EventType,
        source: EventSource,
        callback: Callable[[Event], Any],
        filter_conditions: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        max_retries: int = 3,
    ) -> str:
        """
        Регистрация обработчика событий
        
        Args:
            event_type: Тип события
            source: Источник события
            callback: Функция обработки
            filter_conditions: Условия фильтрации
            priority: Приоритет
            max_retries: Максимальное число попыток
            
        Returns:
            str: ID обработчика
        """
        handler_id = f"handler:{uuid.uuid4()}"
        handler = EventHandler(
            handler_id=handler_id,
            event_type=event_type,
            source=source,
            callback=callback,
            filter_conditions=filter_conditions,
            priority=priority,
            max_retries=max_retries,
        )
        self.handlers.append(handler)
        
        # Сортировка по приоритету
        self.handlers.sort(key=lambda h: h.priority, reverse=True)
        
        logger.info(f"Registered handler {handler_id} for {event_type.value} from {source.value}")
        return handler_id
        
    def unregister_handler(self, handler_id: str) -> bool:
        """Удаление обработчика"""
        for i, handler in enumerate(self.handlers):
            if handler.handler_id == handler_id:
                del self.handlers[i]
                logger.info(f"Unregistered handler {handler_id}")
                return True
        return False
        
    def get_handlers_for_event(self, event: Event) -> List[EventHandler]:
        """Получение обработчиков для события"""
        return [h for h in self.handlers if h.matches(event)]
        
    async def emit_event(
        self,
        event: Event,
        source: Optional[EventSource] = None,
    ) -> str:
        """
        Излучение события (внутреннее)
        
        Args:
            event: Событие
            source: Источник (опционально)
            
        Returns:
            str: event_id
        """
        if not event.event_id:
            event.event_id = f"event:{uuid.uuid4()}"
        if not event.timestamp:
            event.timestamp = datetime.utcnow()
            
        # Логирование
        logger.info(f"Emitting event {event.event_type.value} from {event.source.value}")
        await self.audit_logger.log_event(
            self.audit_logger.create_event(
                event_type=AuditEventType.EVENT_EMITTED,
                resource_type="event",
                resource_id=event.event_id,
                action=event.event_type.value,
                status="emitted",
                details={"source": event.source.value},
            )
        )
        
        # Добавление в очередь
        await self.event_queue.put(event)
        self.stats["events_received"] += 1
        
        return event.event_id
        
    async def receive_event(
        self,
        event_type: EventType,
        source: EventSource,
        payload: Dict[str, Any],
        raw_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Приём события из внешнего источника
        
        Args:
            event_type: Тип события
            source: Источник
            payload: Полезная нагрузка
            raw_data: Исходные данные
            metadata: Метаданные
            
        Returns:
            str: event_id
        """
        event = Event(
            event_id="",
            event_type=event_type,
            source=source,
            timestamp=datetime.utcnow(),
            payload=payload,
            raw_data=raw_data,
            metadata=metadata or {},
        )
        
        return await self.emit_event(event)
        
    async def process_event(self, event: Event) -> bool:
        """
        Обработка события
        
        Args:
            event: Событие
            
        Returns:
            bool: True если обработка успешна
        """
        event_id = event.event_id
        
        # Проверка дедубликации
        event_key = event.get_event_key()
        if event_key in self.processed_events:
            self.stats["events_duplicated"] += 1
            logger.warning(f"Duplicate event detected: {event_id}")
            return True
            
        # Проверка разрешений
        if not await self._check_permissions(event):
            logger.warning(f"Event {event_id} blocked by security policy")
            return False
            
        # Получение обработчиков
        handlers = self.get_handlers_for_event(event)
        
        if not handlers:
            logger.warning(f"No handlers for event {event_id} ({event.event_type.value})")
            return False
            
        # Обработка каждым обработчиком
        success = True
        for handler in handlers:
            try:
                result = await handler.handle(event)
                if not result:
                    success = False
                    
            except Exception as e:
                logger.error(f"Handler {handler.handler_id} failed for event {event_id}: {e}")
                success = False
                
        # Обновление статистики
        if success:
            self.stats["events_processed"] += 1
        else:
            self.stats["events_failed"] += 1
            
        # Сохранение в историю
        self.processed_events[event_key] = datetime.utcnow()
        
        # Логирование
        await self.audit_logger.log_event(
            self.audit_logger.create_event(
                event_type=AuditEventType.EVENT_PROCESSED,
                resource_type="event",
                resource_id=event_id,
                action=event.event_type.value,
                status="processed" if success else "failed",
                details={"handlers": len(handlers)},
            )
        )
        
        return success
        
    async def _check_permissions(self, event: Event) -> bool:
        """Проверка разрешений для события"""
        # Проверяем разрешения для источника события
        permission = await self.security_manager.check_permission(
            user_id="system",
            action=f"receive_event_{event.source.value}",
            integration=event.source.value,
        )
        return permission
        
    async def _cleanup_event_history(self) -> None:
        """Очистка истории событий"""
        now = datetime.utcnow()
        to_remove = [
            key for key, timestamp in self.processed_events.items()
            if (now - timestamp).total_seconds() > self.event_history_ttl
        ]
        for key in to_remove:
            del self.processed_events[key]
            
    async def start(self) -> None:
        """Запуск обработки событий"""
        if self.running:
            return
            
        self.running = True
        self.processor_task = asyncio.create_task(self._process_events_loop())
        logger.info("Event manager started")
        
    async def stop(self) -> None:
        """Остановка обработки событий"""
        self.running = False
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        logger.info("Event manager stopped")
        
    async def _process_events_loop(self) -> None:
        """Цикл обработки событий"""
        while self.running:
            try:
                # Ожидание события
                event = await self.event_queue.get()
                
                # Обработка
                await self.process_event(event)
                
                # Очистка истории
                await self._cleanup_event_history()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                
    def get_stats(self) -> Dict[str, int]:
        """Получение статистики"""
        return self.stats.copy()
        
    def reset_stats(self) -> None:
        """Сброс статистики"""
        self.stats = {
            "events_received": 0,
            "events_processed": 0,
            "events_failed": 0,
            "events_duplicated": 0,
        }
