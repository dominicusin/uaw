"""
UAW Trigger System
Система триггеров для автоматизации
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import asyncio
import croniter
import logging
import uuid

from uaw.automation.event_manager import EventManager, Event, EventType, EventSource


logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Типы триггеров"""
    WEBHOOK = "webhook"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    EVENT = "event"
    CONDITION = "condition"
    POLLING = "polling"


class TriggerStatus(Enum):
    """Статусы триггера"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    FAILED = "failed"


@dataclass
class TriggerCondition:
    """Условие триггера"""
    condition_id: str
    field: str
    operator: str  # eq, neq, gt, gte, lt, lte, contains, in, not_in
    value: Any
    
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Оценка условия"""
        actual_value = data.get(self.field)
        
        if self.operator == "eq":
            return actual_value == self.value
        elif self.operator == "neq":
            return actual_value != self.value
        elif self.operator == "gt":
            return actual_value > self.value
        elif self.operator == "gte":
            return actual_value >= self.value
        elif self.operator == "lt":
            return actual_value < self.value
        elif self.operator == "lte":
            return actual_value <= self.value
        elif self.operator == "contains":
            return self.value in actual_value if isinstance(actual_value, (str, list, dict)) else False
        elif self.operator == "in":
            return actual_value in self.value if isinstance(self.value, (list, tuple, set)) else False
        elif self.operator == "not_in":
            return actual_value not in self.value if isinstance(self.value, (list, tuple, set)) else False
        else:
            return False


@dataclass
class TriggerAction:
    """Действие триггера"""
    action_id: str
    action_type: str  # workflow, script, notification, webhook
    target: str  # workflow_id, script_name, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    retry_count: int = 3


@dataclass
class Trigger:
    """Триггер"""
    trigger_id: str
    name: str
    trigger_type: TriggerType
    status: TriggerStatus = TriggerStatus.ACTIVE
    
    # Для scheduled триггеров
    schedule: Optional[str] = None  # cron expression
    timezone: str = "UTC"
    
    # Для webhook триггеров
    webhook_id: Optional[str] = None
    
    # Для event триггеров
    event_type: Optional[EventType] = None
    event_source: Optional[EventSource] = None
    
    # Условия
    conditions: List[TriggerCondition] = field(default_factory=list)
    
    # Действия
    actions: List[TriggerAction] = field(default_factory=list)
    
    # Метод фильтрации
    filter_expression: Optional[str] = None
    
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
            "status": self.status.value,
            "schedule": self.schedule,
            "timezone": self.timezone,
            "webhook_id": self.webhook_id,
            "event_type": self.event_type.value if self.event_type else None,
            "event_source": self.event_source.value if self.event_source else None,
            "conditions": [c.to_dict() for c in self.conditions] if self.conditions else [],
            "actions": [a.to_dict() for a in self.actions] if self.actions else [],
            "filter_expression": self.filter_expression,
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
    
    def matches_event(self, event: Event) -> bool:
        """Проверка, подходит ли событие для триггера"""
        # Проверка типа события
        if self.event_type and self.event_type != event.event_type:
            return False
        
        # Проверка источника
        if self.event_source and self.event_source != event.source:
            return False
        
        # Проверка условий
        for condition in self.conditions:
            if not condition.evaluate(event.payload):
                return False
        
        return True
    
    def get_next_execution_time(self) -> Optional[datetime]:
        """Получение времени следующего выполнения для scheduled триггера"""
        if not self.schedule or self.trigger_type != TriggerType.SCHEDULED:
            return None
        
        now = datetime.utcnow()
        cron = croniter.croniter(self.schedule, now)
        next_time = cron.get_next(datetime)
        return next_time


class TriggerManager:
    """Менеджер триггеров"""
    
    def __init__(
        self,
        event_manager: Optional[EventManager] = None,
    ):
        self.event_manager = event_manager or EventManager()
        
        # Триггеры
        self.triggers: Dict[str, Trigger] = {}
        
        # Активные выполнения
        self.active_executions: Dict[str, int] = {}
        
        # Задачи для scheduled триггеров
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}
        
        # Статистика
        self.stats: Dict[str, int] = {
            "triggers_fired": 0,
            "triggers_failed": 0,
            "actions_executed": 0,
            "actions_failed": 0,
        }
        
        # Флаг работы
        self.running = False
        
    def register_trigger(self, trigger: Trigger) -> str:
        """Регистрация триггера"""
        if trigger.trigger_id in self.triggers:
            raise ValueError(f"Trigger {trigger.trigger_id} already exists")
        
        self.triggers[trigger.trigger_id] = trigger
        
        # Если это scheduled триггер, запускаем планировщик
        if trigger.trigger_type == TriggerType.SCHEDULED and trigger.is_enabled:
            self._schedule_trigger(trigger)
        
        logger.info(f"Registered trigger {trigger.trigger_id}: {trigger.name}")
        return trigger.trigger_id
        
    def unregister_trigger(self, trigger_id: str) -> bool:
        """Удаление триггера"""
        if trigger_id not in self.triggers:
            return False
        
        trigger = self.triggers[trigger_id]
        
        # Останавливаем scheduled задачу
        if trigger.trigger_type == TriggerType.SCHEDULED:
            self._cancel_scheduled_trigger(trigger)
        
        del self.triggers[trigger_id]
        logger.info(f"Unregistered trigger {trigger_id}")
        return True
        
    def get_trigger(self, trigger_id: str) -> Optional[Trigger]:
        """Получение триггера"""
        return self.triggers.get(trigger_id)
        
    def list_triggers(self, trigger_type: Optional[TriggerType] = None) -> List[Trigger]:
        """Получение списка триггеров"""
        if trigger_type:
            return [t for t in self.triggers.values() if t.trigger_type == trigger_type]
        return list(self.triggers.values())
        
    async def fire_trigger(self, trigger_id: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Ручной запуск триггера
        
        Args:
            trigger_id: ID триггера
            data: Данные для передачи
            
        Returns:
            bool: True если запуск успешен
        """
        trigger = self.get_trigger(trigger_id)
        if not trigger or not trigger.is_enabled:
            return False
        
        # Проверка максимального числа одновременно выполняемых
        if self.active_executions.get(trigger_id, 0) >= trigger.max_concurrent_executions:
            logger.warning(f"Trigger {trigger_id} max concurrent executions reached")
            return False
        
        # Выполнение действий
        success = True
        for action in trigger.actions:
            result = await self._execute_action(trigger, action, data or {})
            if not result:
                success = False
                
        # Обновление статистики
        trigger.executions_count += 1
        trigger.last_execution = datetime.utcnow()
        
        if success:
            trigger.last_success = datetime.utcnow()
            self.stats["triggers_fired"] += 1
        else:
            trigger.last_failure = datetime.utcnow()
            self.stats["triggers_failed"] += 1
            
        return success
        
    async def _execute_action(
        self,
        trigger: Trigger,
        action: TriggerAction,
        data: Dict[str, Any],
    ) -> bool:
        """Выполнение действия триггера"""
        try:
            if action.action_type == "workflow":
                # Запуск workflow
                workflow_id = action.target
                # В реальной реализации здесь будет запуск workflow
                logger.info(f"Triggering workflow {workflow_id}")
                self.stats["actions_executed"] += 1
                return True
                
            elif action.action_type == "script":
                # Выполнение скрипта
                script_name = action.target
                logger.info(f"Executing script {script_name}")
                self.stats["actions_executed"] += 1
                return True
                
            elif action.action_type == "notification":
                # Отправка уведомления
                notification_target = action.target
                logger.info(f"Sending notification to {notification_target}")
                self.stats["actions_executed"] += 1
                return True
                
            elif action.action_type == "webhook":
                # Вызов webhook
                webhook_id = action.target
                logger.info(f"Calling webhook {webhook_id}")
                self.stats["actions_executed"] += 1
                return True
                
            else:
                logger.warning(f"Unknown action type: {action.action_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing action {action.action_id}: {e}")
            self.stats["actions_failed"] += 1
            return False
            
    def _schedule_trigger(self, trigger: Trigger) -> None:
        """Планирование триггера"""
        if trigger.trigger_type != TriggerType.SCHEDULED:
            return
        
        async def run_scheduled_trigger():
            while self.running and trigger.is_enabled:
                next_time = trigger.get_next_execution_time()
                if not next_time:
                    break
                
                # Ожидание
                wait_seconds = (next_time - datetime.utcnow()).total_seconds()
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                
                # Выполнение
                if trigger.is_enabled:
                    asyncio.create_task(self.fire_trigger(trigger.trigger_id))
                    
        task = asyncio.create_task(run_scheduled_trigger())
        self.scheduled_tasks[trigger.trigger_id] = task
        
    def _cancel_scheduled_trigger(self, trigger: Trigger) -> None:
        """Отмена планирования триггера"""
        if trigger.trigger_id in self.scheduled_tasks:
            task = self.scheduled_tasks[trigger.trigger_id]
            task.cancel()
            del self.scheduled_tasks[trigger.trigger_id]
            
    async def start(self) -> None:
        """Запуск менеджера"""
        if self.running:
            return
        
        self.running = True
        
        # Планирование всех scheduled триггеров
        for trigger in self.triggers.values():
            if trigger.trigger_type == TriggerType.SCHEDULED and trigger.is_enabled:
                self._schedule_trigger(trigger)
        
        logger.info("Trigger manager started")
        
    async def stop(self) -> None:
        """Остановка менеджера"""
        self.running = False
        
        # Отмена всех scheduled задач
        for task in self.scheduled_tasks.values():
            task.cancel()
        self.scheduled_tasks.clear()
        
        logger.info("Trigger manager stopped")
        
    def get_stats(self) -> Dict[str, int]:
        """Получение статистики"""
        return self.stats.copy()
        
    def reset_stats(self) -> None:
        """Сброс статистики"""
        self.stats = {
            "triggers_fired": 0,
            "triggers_failed": 0,
            "actions_executed": 0,
            "actions_failed": 0,
        }
