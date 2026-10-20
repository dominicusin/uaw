"""
UAW Automation Engine
Движок автоматизации для Unified Agentic Workspace
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import asyncio
import logging
import uuid

from uaw.automation.event_manager import EventManager, Event, EventType, EventSource
from uaw.automation.trigger import TriggerManager, Trigger, TriggerType
from uaw.automation.webhook_server import WebhookServer

from uaw.core.state_manager import StateManager
from uaw.core.audit import AuditLogger, AuditEventType
from uaw.core.security import SecurityManager, PermissionLevel


logger = logging.getLogger(__name__)


class AutomationStatus(Enum):
    """Статусы автоматизации"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"


class AutomationRuleStatus(Enum):
    """Статусы правил автоматизации"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    TESTING = "testing"


@dataclass
class AutomationRule:
    """Правило автоматизации"""
    rule_id: str
    name: str
    description: str
    
    # Триггер
    trigger: Trigger
    
    # Условия (дополнительные)
    conditions: List[Any] = field(default_factory=list)
    
    # Действия
    actions: List[Any] = field(default_factory=list)
    
    # Настройки
    is_enabled: bool = True
    priority: int = 0
    max_executions: Optional[int] = None
    execution_timeout: int = 300
    
    # Статистика
    executions_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    # Создание
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger.to_dict() if self.trigger else None,
            "conditions": self.conditions,
            "actions": self.actions,
            "is_enabled": self.is_enabled,
            "priority": self.priority,
            "max_executions": self.max_executions,
            "execution_timeout": self.execution_timeout,
            "executions_count": self.executions_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Automation:
    """Автоматизация"""
    automation_id: str
    name: str
    description: str
    
    # Правила
    rules: List[AutomationRule] = field(default_factory=list)
    
    # Триггеры
    triggers: List[Trigger] = field(default_factory=list)
    
    # Настройки
    is_enabled: bool = True
    status: AutomationStatus = AutomationStatus.ACTIVE
    
    # Планирование
    schedule: Optional[str] = None
    timezone: str = "UTC"
    
    # Ограничения
    max_concurrent_executions: int = 1
    rate_limit: Optional[int] = None  # запросов в минуту
    
    # Статистика
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    
    # Создание
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "automation_id": self.automation_id,
            "name": self.name,
            "description": self.description,
            "rules": [r.to_dict() for r in self.rules],
            "triggers": [t.to_dict() for t in self.triggers],
            "is_enabled": self.is_enabled,
            "status": self.status.value,
            "schedule": self.schedule,
            "timezone": self.timezone,
            "max_concurrent_executions": self.max_concurrent_executions,
            "rate_limit": self.rate_limit,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class AutomationEngine:
    """
    Движок автоматизации
    
    Объединяет:
    - EventManager (управление событиями)
    - TriggerManager (управление триггерами)
    - WebhookServer (приём webhook)
    - StateManager (сохранение состояния)
    """
    
    def __init__(
        self,
        event_manager: Optional[EventManager] = None,
        trigger_manager: Optional[TriggerManager] = None,
        webhook_server: Optional[WebhookServer] = None,
        state_manager: Optional[StateManager] = None,
        audit_logger: Optional[AuditLogger] = None,
        security_manager: Optional[SecurityManager] = None,
    ):
        self.event_manager = event_manager or EventManager()
        self.trigger_manager = trigger_manager or TriggerManager()
        self.webhook_server = webhook_server or WebhookServer()
        self.state_manager = state_manager or StateManager()
        self.audit_logger = audit_logger or AuditLogger()
        self.security_manager = security_manager or SecurityManager()
        
        # Автоматизации
        self.automations: Dict[str, Automation] = {}
        
        # Активные выполнения
        self.active_executions: Dict[str, asyncio.Task] = {}
        
        # Статистика
        self.stats: Dict[str, int] = {
            "automations_created": 0,
            "automations_deleted": 0,
            "rules_executed": 0,
            "rules_failed": 0,
            "events_processed": 0,
            "events_failed": 0,
        }
        
        # Флаг работы
        self.running = False
        
    async def initialize(self) -> None:
        """Инициализация движка"""
        # Запуск компонентов
        await self.event_manager.start()
        await self.trigger_manager.start()
        await self.webhook_server.start()
        
        # Регистрация обработчиков по умолчанию
        self._register_default_handlers()
        
        logger.info("Automation engine initialized")
        
    async def shutdown(self) -> None:
        """Завершение работы движка"""
        # Остановка компонентов
        await self.event_manager.stop()
        await self.trigger_manager.stop()
        await self.webhook_server.stop()
        
        # Отмена активных выполнений
        for task in self.active_executions.values():
            task.cancel()
        self.active_executions.clear()
        
        self.running = False
        logger.info("Automation engine shutdown")
        
    def _register_default_handlers(self) -> None:
        """Регистрация обработчиков по умолчанию"""
        # Обработчик GitHub push
        self.event_manager.register_handler(
            event_type=EventType.GITHUB_PUSH,
            source=EventSource.GITHUB,
            callback=self._handle_github_push,
            filter_conditions={"ref": "refs/heads/main"},
        )
        
        # Обработчик GitHub pull request
        self.event_manager.register_handler(
            event_type=EventType.GITHUB_PULL_REQUEST,
            source=EventSource.GITHUB,
            callback=self._handle_github_pull_request,
        )
        
        # Обработчик GitHub issue
        self.event_manager.register_handler(
            event_type=EventType.GITHUB_ISSUE,
            source=EventSource.GITHUB,
            callback=self._handle_github_issue,
        )
        
        # Обработчик deployment
        self.event_manager.register_handler(
            event_type=EventType.VERCEL_DEPLOYMENT_COMPLETED,
            source=EventSource.VERCEL,
            callback=self._handle_deployment_completed,
        )
        
        # Обработчик workflow
        self.event_manager.register_handler(
            event_type=EventType.INTERNAL_WORKFLOW_COMPLETED,
            source=EventSource.INTERNAL,
            callback=self._handle_workflow_completed,
        )
        
    async def _handle_github_push(self, event: Event) -> None:
        """Обработка GitHub push события"""
        logger.info(f"Handling GitHub push event: {event.payload.get('repository', {}).get('full_name')}")
        
        # В реальной реализации здесь будет логика обработки
        # Например, запуск CI/CD pipeline
        
        # Логирование в аудит
        await self.audit_logger.log_event(
            self.audit_logger.create_event(
                event_type=AuditEventType.AUTOMATION_TRIGGERED,
                resource_type="automation",
                action="github_push_handler",
                status="processed",
                details={"repository": event.payload.get("repository", {}).get("full_name")},
            )
        )
        
    async def _handle_github_pull_request(self, event: Event) -> None:
        """Обработка GitHub pull request события"""
        action = event.payload.get("action")
        pr = event.payload.get("pull_request", {})
        
        logger.info(f"Handling GitHub PR event: {action} - {pr.get('title')}")
        
        # Логирование
        await self.audit_logger.log_event(
            self.audit_logger.create_event(
                event_type=AuditEventType.AUTOMATION_TRIGGERED,
                resource_type="automation",
                action="github_pr_handler",
                status="processed",
                details={"action": action, "pr_title": pr.get("title")},
            )
        )
        
    async def _handle_github_issue(self, event: Event) -> None:
        """Обработка GitHub issue события"""
        action = event.payload.get("action")
        issue = event.payload.get("issue", {})
        
        logger.info(f"Handling GitHub issue event: {action} - {issue.get('title')}")
        
        # Логирование
        await self.audit_logger.log_event(
            self.audit_logger.create_event(
                event_type=AuditEventType.AUTOMATION_TRIGGERED,
                resource_type="automation",
                action="github_issue_handler",
                status="processed",
                details={"action": action, "issue_title": issue.get("title")},
            )
        )
        
    async def _handle_deployment_completed(self, event: Event) -> None:
        """Обработка события завершения deployment"""
        deployment_id = event.payload.get("id")
        status = event.payload.get("status")
        
        logger.info(f"Handling deployment completed: {deployment_id} - {status}")
        
        # В реальной реализации: проверка health checks, уведомление команды
        
        # Логирование
        await self.audit_logger.log_event(
            self.audit_logger.create_event(
                event_type=AuditEventType.AUTOMATION_TRIGGERED,
                resource_type="automation",
                action="deployment_handler",
                status="processed",
                details={"deployment_id": deployment_id, "status": status},
            )
        )
        
    async def _handle_workflow_completed(self, event: Event) -> None:
        """Обработка события завершения workflow"""
        workflow_id = event.payload.get("workflow_id")
        status = event.payload.get("status")
        
        logger.info(f"Handling workflow completed: {workflow_id} - {status}")
        
        # Логирование
        await self.audit_logger.log_event(
            self.audit_logger.create_event(
                event_type=AuditEventType.AUTOMATION_TRIGGERED,
                resource_type="automation",
                action="workflow_handler",
                status="processed",
                details={"workflow_id": workflow_id, "status": status},
            )
        )
        
    async def create_automation(
        self,
        name: str,
        description: str,
        rules: Optional[List[AutomationRule]] = None,
        triggers: Optional[List[Trigger]] = None,
        schedule: Optional[str] = None,
        is_enabled: bool = True,
    ) -> str:
        """
        Создание автоматизации
        
        Args:
            name: Название
            description: Описание
            rules: Правила автоматизации
            triggers: Триггеры
            schedule: Расписание (cron)
            is_enabled: Включена
            
        Returns:
            str: ID автоматизации
        """
        automation_id = f"automation:{uuid.uuid4()}"
        
        automation = Automation(
            automation_id=automation_id,
            name=name,
            description=description,
            rules=rules or [],
            triggers=triggers or [],
            is_enabled=is_enabled,
            schedule=schedule,
        )
        
        self.automations[automation_id] = automation
        
        # Регистрация триггеров
        for trigger in automation.triggers:
            self.trigger_manager.register_trigger(trigger)
        
        self.stats["automations_created"] += 1
        logger.info(f"Created automation {automation_id}: {name}")
        
        return automation_id
        
    def get_automation(self, automation_id: str) -> Optional[Automation]:
        """Получение автоматизации"""
        return self.automations.get(automation_id)
        
    def list_automations(self) -> List[Automation]:
        """Получение списка автоматизаций"""
        return list(self.automations.values())
        
    def update_automation(
        self,
        automation_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        status: Optional[AutomationStatus] = None,
    ) -> bool:
        """Обновление автоматизации"""
        automation = self.get_automation(automation_id)
        if not automation:
            return False
        
        if name is not None:
            automation.name = name
        if description is not None:
            automation.description = description
        if is_enabled is not None:
            automation.is_enabled = is_enabled
        if status is not None:
            automation.status = status
            
        automation.updated_at = datetime.utcnow()
        return True
        
    def delete_automation(self, automation_id: str) -> bool:
        """Удаление автоматизации"""
        if automation_id not in self.automations:
            return False
        
        automation = self.automations[automation_id]
        
        # Удаление триггеров
        for trigger in automation.triggers:
            self.trigger_manager.unregister_trigger(trigger.trigger_id)
        
        del self.automations[automation_id]
        self.stats["automations_deleted"] += 1
        logger.info(f"Deleted automation {automation_id}")
        return True
        
    async def enable_automation(self, automation_id: str) -> bool:
        """Включение автоматизации"""
        automation = self.get_automation(automation_id)
        if not automation:
            return False
        
        automation.is_enabled = True
        automation.status = AutomationStatus.ACTIVE
        
        # Регистрация триггеров
        for trigger in automation.triggers:
            self.trigger_manager.register_trigger(trigger)
        
        logger.info(f"Enabled automation {automation_id}")
        return True
        
    async def disable_automation(self, automation_id: str) -> bool:
        """Отключение автоматизации"""
        automation = self.get_automation(automation_id)
        if not automation:
            return False
        
        automation.is_enabled = False
        automation.status = AutomationStatus.INACTIVE
        
        # Удаление триггеров
        for trigger in automation.triggers:
            self.trigger_manager.unregister_trigger(trigger.trigger_id)
        
        logger.info(f"Disabled automation {automation_id}")
        return True
        
    async def trigger_automation(
        self,
        automation_id: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Ручной запуск автоматизации
        
        Args:
            automation_id: ID автоматизации
            data: Данные для передачи
            
        Returns:
            bool: True если запуск успешен
        """
        automation = self.get_automation(automation_id)
        if not automation or not automation.is_enabled:
            return False
        
        # Проверка максимального числа одновременно выполняемых
        if automation.max_concurrent_executions > 0:
            active_count = len([
                t for t in self.active_executions.values()
                if not t.done()
            ])
            if active_count >= automation.max_concurrent_executions:
                logger.warning(f"Automation {automation_id} max concurrent executions reached")
                return False
        
        # Выполнение правил
        success = True
        for rule in automation.rules:
            if not rule.is_enabled:
                continue
            
            result = await self._execute_rule(rule, data or {})
            if not result:
                success = False
                
        # Обновление статистики
        automation.total_executions += 1
        if success:
            automation.successful_executions += 1
            automation.status = AutomationStatus.ACTIVE
        else:
            automation.failed_executions += 1
            automation.status = AutomationStatus.FAILED
            
        return success
        
    async def _execute_rule(
        self,
        rule: AutomationRule,
        data: Dict[str, Any],
    ) -> bool:
        """Выполнение правила автоматизации"""
        try:
            # Выполнение триггера
            trigger_result = await self.trigger_manager.fire_trigger(
                rule.trigger.trigger_id,
                data,
            )
            
            if not trigger_result:
                return False
            
            # Проверка условий
            for condition in rule.conditions:
                if not self._evaluate_condition(condition, data):
                    return False
            
            # Выполнение действий
            for action in rule.actions:
                if not await self._execute_action(action, data):
                    return False
            
            self.stats["rules_executed"] += 1
            rule.executions_count += 1
            rule.success_count += 1
            return True
            
        except Exception as e:
            logger.error(f"Error executing rule {rule.rule_id}: {e}")
            self.stats["rules_failed"] += 1
            rule.executions_count += 1
            rule.failure_count += 1
            return False
            
    def _evaluate_condition(self, condition: Any, data: Dict[str, Any]) -> bool:
        """Оценка условия"""
        # В реальной реализации здесь будет оценка условия
        return True
        
    async def _execute_action(self, action: Any, data: Dict[str, Any]) -> bool:
        """Выполнение действия"""
        # В реальной реализации здесь будет выполнение действия
        return True
        
    async def start(self) -> None:
        """Запуск движка"""
        if self.running:
            return
        
        self.running = True
        await self.initialize()
        logger.info("Automation engine started")
        
    async def stop(self) -> None:
        """Остановка движка"""
        if not self.running:
            return
        
        await self.shutdown()
        self.running = False
        logger.info("Automation engine stopped")
        
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики"""
        return {
            **self.stats,
            "event_manager": self.event_manager.get_stats(),
            "trigger_manager": self.trigger_manager.get_stats(),
            "webhook_server": self.webhook_server.get_stats(),
        }
        
    def reset_stats(self) -> None:
        """Сброс статистики"""
        self.stats = {
            "automations_created": 0,
            "automations_deleted": 0,
            "rules_executed": 0,
            "rules_failed": 0,
            "events_processed": 0,
            "events_failed": 0,
        }
        self.event_manager.reset_stats()
        self.trigger_manager.reset_stats()
        self.webhook_server.reset_stats()
