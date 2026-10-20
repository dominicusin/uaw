"""
UAW Scenario: Notification Workflow

Сценарий отправки уведомлений
"Сообщи команде в Teams о завершении задачи"
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
import logging

from uaw.core.uaw_core import UAWCore
from uaw.core.state_manager import StateManager
from uaw.core.resource_mapping import ResourceMapper
from uaw.core.security import SecurityManager, PermissionLevel
from uaw.core.audit import AuditLogger, AuditEventType

from uaw.models.workflow import (
    Workflow, WorkflowStep, WorkflowStepType, WorkflowStatus,
    WorkflowTrigger, WorkflowCondition, ExecutionMode,
)
from uaw.models.task import Task, TaskStatus
from uaw.models.person import Person
from uaw.models.team import Team

from uaw.adapters.teams_adapter import MicrosoftTeamsAdapter
from uaw.adapters.slack_adapter import SlackAdapter

from uaw.orchestrator.workflow_engine import WorkflowEngine


logger = logging.getLogger(__name__)


# Определение workflow для уведомлений
NOTIFICATION_WORKFLOW_DEFINITION = {
    "workflow_id": "workflow:notification",
    "name": "Notification Workflow",
    "description": "Отправка уведомлений в командные каналы",
    "version": "1.0.0",
    "steps": [
        {
            "step_id": "step:parse-request",
            "name": "Парсинг запроса",
            "step_type": "action",
            "action": "parse_natural_language",
            "description": "Анализ запроса на уведомление",
            "dependencies": [],
            "timeout_seconds": 30,
            "retry_count": 0,
            "permission_level": "L0_READ_ONLY",
        },
        {
            "step_id": "step:validate-parameters",
            "name": "Проверка параметров",
            "step_type": "condition",
            "action": "validate_parameters",
            "description": "Проверка наличия всех необходимых параметров",
            "dependencies": ["step:parse-request"],
            "timeout_seconds": 30,
            "retry_count": 0,
            "permission_level": "L0_READ_ONLY",
            "conditions": [
                {
                    "type": "required_field",
                    "field": "message",
                    "expected": True,
                    "action_on_failure": "request_clarification"
                },
                {
                    "type": "required_field",
                    "field": "channel",
                    "expected": True,
                    "action_on_failure": "use_default"
                }
            ]
        },
        {
            "step_id": "step:find-team",
            "name": "Поиск команды",
            "step_type": "action",
            "action": "find_team",
            "description": "Поиск команды по названию",
            "dependencies": ["step:validate-parameters"],
            "timeout_seconds": 60,
            "retry_count": 2,
            "permission_level": "L0_READ_ONLY",
        },
        {
            "step_id": "step:find-channel",
            "name": "Поиск канала",
            "step_type": "action",
            "action": "find_channel",
            "description": "Поиск канала в команде",
            "dependencies": ["step:find-team"],
            "timeout_seconds": 60,
            "retry_count": 2,
            "permission_level": "L0_READ_ONLY",
        },
        {
            "step_id": "step:format-message",
            "name": "Форматирование сообщения",
            "step_type": "action",
            "action": "format_message",
            "description": "Форматирование сообщения с учетом контекста",
            "dependencies": ["step:validate-parameters"],
            "timeout_seconds": 30,
            "retry_count": 0,
            "permission_level": "L0_READ_ONLY",
        },
        {
            "step_id": "step:send-teams-notification",
            "name": "Отправка в Microsoft Teams",
            "step_type": "action",
            "action": "send_message",
            "description": "Отправка уведомления в Microsoft Teams",
            "adapter": "teams",
            "parameters": {
                "team_id": "{{team_id}}",
                "channel_id": "{{channel_id}}",
                "message": "{{formatted_message}}"
            },
            "dependencies": ["step:find-channel", "step:format-message"],
            "timeout_seconds": 60,
            "retry_count": 2,
            "permission_level": "L2_SUPERVISED",
            "fallback": {
                "adapter": "slack",
                "action": "send_message",
                "parameters": {
                    "channel": "{{channel_id}}",
                    "text": "{{formatted_message}}"
                }
            }
        },
        {
            "step_id": "step:verify-delivery",
            "name": "Проверка доставки",
            "step_type": "condition",
            "action": "verify_message_delivery",
            "description": "Проверка, что сообщение дошло до получателя",
            "dependencies": ["step:send-teams-notification"],
            "timeout_seconds": 30,
            "retry_count": 2,
            "permission_level": "L0_READ_ONLY",
            "conditions": [
                {
                    "type": "delivery_check",
                    "field": "message_id",
                    "expected": True,
                    "action_on_failure": "retry"
                }
            ]
        },
        {
            "step_id": "step:log-notification",
            "name": "Логирование уведомления",
            "step_type": "action",
            "action": "log_notification",
            "description": "Сохранение информации об уведомлении в журнал",
            "dependencies": ["step:verify-delivery"],
            "timeout_seconds": 30,
            "retry_count": 0,
            "permission_level": "L0_READ_ONLY",
        },
        {
            "step_id": "step:generate-report",
            "name": "Формирование отчёта",
            "step_type": "action",
            "action": "generate_report",
            "description": "Сбор информации и формирование итогового отчёта",
            "dependencies": ["step:log-notification"],
            "timeout_seconds": 30,
            "retry_count": 0,
            "permission_level": "L0_READ_ONLY",
        }
    ]
}


class NotificationType(Enum):
    """Типы уведомлений"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    TASK_COMPLETED = "task_completed"
    TASK_ASSIGNED = "task_assigned"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DEPLOYMENT_FAILED = "deployment_failed"
    PR_CREATED = "pr_created"
    PR_MERGED = "pr_merged"


@dataclass
class NotificationResult:
    """Результат отправки уведомления"""
    notification_id: str
    message_id: str
    channel_id: str
    team_id: Optional[str] = None
    notification_type: NotificationType = NotificationType.INFO
    title: str = ""
    message: str = ""
    recipients: List[str] = field(default_factory=list)
    delivered: bool = False
    delivery_time: Optional[datetime] = None
    error: Optional[str] = None
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "notification_id": self.notification_id,
            "message_id": self.message_id,
            "channel_id": self.channel_id,
            "team_id": self.team_id,
            "notification_type": self.notification_type.value,
            "title": self.title,
            "message": self.message,
            "recipients": self.recipients,
            "delivered": self.delivered,
            "delivery_time": self.delivery_time.isoformat() if self.delivery_time else None,
            "error": self.error,
            "external_ids": self.external_ids,
        }


class NotificationWorkflow:
    """Workflow для отправки уведомлений"""
    
    def __init__(
        self,
        uaw_core: Optional[UAWCore] = None,
        workflow_engine: Optional[WorkflowEngine] = None,
        state_manager: Optional[StateManager] = None,
        resource_mapper: Optional[ResourceMapper] = None,
        security_manager: Optional[SecurityManager] = None,
        audit_logger: Optional[AuditLogger] = None,
    ):
        self.uaw_core = uaw_core or UAWCore()
        self.workflow_engine = workflow_engine or WorkflowEngine()
        self.state_manager = state_manager or StateManager()
        self.resource_mapper = resource_mapper or ResourceMapper()
        self.security_manager = security_manager or SecurityManager()
        self.audit_logger = audit_logger or AuditLogger()
        
        self.adapters: Dict[str, Any] = {
            "teams": MicrosoftTeamsAdapter(),
            "slack": SlackAdapter(),
        }
        
    def create_workflow(
        self,
        message: str,
        channel: str,
        notification_type: NotificationType = NotificationType.INFO,
        title: str = "",
        recipients: Optional[List[str]] = None,
        team: Optional[str] = None,
    ) -> Workflow:
        """Создание workflow для уведомления"""
        workflow_id = f"workflow:notification:{uuid.uuid4()}"
        
        steps = []
        for step_config in NOTIFICATION_WORKFLOW_DEFINITION["steps"]:
            step = WorkflowStep(
                uaw_id=step_config["step_id"],
                name=step_config["name"],
                step_type=WorkflowStepType(step_config["step_type"]),
                description=step_config["description"],
                adapter=step_config.get("adapter"),
                action=step_config["action"],
                parameters=self._resolve_parameters(step_config.get("parameters", {}), {
                    "message": message,
                    "channel": channel,
                    "team": team or "",
                    "team_id": "TBD",
                    "channel_id": "TBD",
                    "formatted_message": self._format_message(message, notification_type, title),
                    "notification_type": notification_type.value,
                    "title": title,
                    "recipients": recipients or [],
                }),
                dependencies=step_config.get("dependencies", []),
                timeout_seconds=step_config.get("timeout_seconds", 30),
                retry_count=step_config.get("retry_count", 0),
                permission_level=PermissionLevel(step_config.get("permission_level", "L2_SUPERVISED")),
                conditions=[
                    WorkflowCondition(**c) for c in step_config.get("conditions", [])
                ],
                fallback=step_config.get("fallback"),
            )
            steps.append(step)
        
        return Workflow(
            uaw_id=workflow_id,
            name=NOTIFICATION_WORKFLOW_DEFINITION["name"],
            description=NOTIFICATION_WORKFLOW_DEFINITION["description"],
            version=NOTIFICATION_WORKFLOW_DEFINITION["version"],
            status=WorkflowStatus.PENDING,
            steps=steps,
            triggers=[
                WorkflowTrigger(
                    trigger_id=f"trigger:{workflow_id}",
                    trigger_type="manual",
                    description="Ручной запуск уведомления"
                ),
                WorkflowTrigger(
                    trigger_id=f"trigger:{workflow_id}:event",
                    trigger_type="event",
                    description="Запуск по событию (завершение задачи, deployment и т.д.)"
                )
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    
    def _resolve_parameters(self, template: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Подстановка параметров"""
        resolved = {}
        for key, value in template.items():
            if isinstance(value, str) and "{{" in value and "}}" in value:
                resolved_key = value
                for var_name, var_value in context.items():
                    resolved_key = resolved_key.replace("{{" + var_name + "}}", str(var_value))
                resolved[key] = resolved_key
            else:
                resolved[key] = value
        return resolved
    
    def _format_message(
        self,
        message: str,
        notification_type: NotificationType,
        title: str = "",
    ) -> str:
        """Форматирование сообщения"""
        emoji_map = {
            NotificationType.INFO: "ℹ️",
            NotificationType.SUCCESS: "✅",
            NotificationType.WARNING: "⚠️",
            NotificationType.ERROR: "❌",
            NotificationType.TASK_COMPLETED: "✅",
            NotificationType.TASK_ASSIGNED: "👤",
            NotificationType.DEPLOYMENT_COMPLETED: "🚀",
            NotificationType.DEPLOYMENT_FAILED: "💥",
            NotificationType.PR_CREATED: "📝",
            NotificationType.PR_MERGED: "🎉",
        }
        
        emoji = emoji_map.get(notification_type, "ℹ️")
        
        if title:
            return f"{emoji} **{title}**\n\n{message}"
        return f"{emoji} {message}"
    
    async def execute(
        self,
        workflow: Workflow,
        context: Optional[Dict[str, Any]] = None,
    ) -> NotificationResult:
        """Выполнение workflow уведомления"""
        context = context or {}
        result = NotificationResult(
            notification_id="",
            message_id="",
            channel_id="",
            team_id="",
            notification_type=NotificationType.INFO,
            title="",
            message="",
            delivered=False,
        )
        
        # Выполнение через WorkflowEngine
        executed_workflow = await self.workflow_engine.execute_workflow(
            workflow, 
            mode=ExecutionMode.SMART,
            context=context
        )
        
        # Извлечение результатов
        for step in executed_workflow.steps:
            if step.uaw_id == "step:send-teams-notification" and step.result:
                result.notification_id = step.result.get("notification_id", "")
                result.message_id = step.result.get("message_id", "")
                result.channel_id = step.result.get("channel_id", "")
                result.team_id = step.result.get("team_id", "")
                result.title = step.result.get("title", "")
                result.message = step.result.get("message", "")
                result.recipients = step.result.get("recipients", [])
                result.delivered = step.result.get("delivered", False)
                result.delivery_time = datetime.fromisoformat(step.result.get("delivery_time")) if step.result.get("delivery_time") else None
                result.external_ids = step.result.get("external_ids", {})
                
            if step.uaw_id == "step:verify-delivery" and step.result:
                result.delivered = step.result.get("delivered", False)
                
        return result


async def send_notification(
    message: str,
    channel: str,
    notification_type: NotificationType = NotificationType.INFO,
    title: str = "",
    recipients: Optional[List[str]] = None,
    team: Optional[str] = None,
) -> NotificationResult:
    """
    Удобная функция для отправки уведомления
    
    Args:
        message: Текст сообщения
        channel: Канал для отправки
        notification_type: Тип уведомления
        title: Заголовок сообщения
        recipients: Список получателей
        team: Команда
        
    Returns:
        NotificationResult с информацией об уведомлении
    """
    workflow = NotificationWorkflow()
    workflow_obj = workflow.create_workflow(
        message=message,
        channel=channel,
        notification_type=notification_type,
        title=title,
        recipients=recipients,
        team=team,
    )
    
    return await workflow.execute(
        workflow_obj,
        context={
            "message": message,
            "channel": channel,
            "notification_type": notification_type.value,
            "title": title,
            "recipients": recipients or [],
            "team": team or "",
        }
    )


# Удобные функции для стандартных уведомлений

async def notify_task_completed(
    task_id: str,
    task_title: str,
    assignee: str,
    channel: str,
    team: Optional[str] = None,
) -> NotificationResult:
    """Уведомление о завершении задачи"""
    message = f"Задача **'{task_title}'** (ID: {task_id}) завершена\n\nИсполнитель: {assignee}"
    return await send_notification(
        message=message,
        channel=channel,
        notification_type=NotificationType.TASK_COMPLETED,
        title="Задача завершена",
        team=team,
    )


async def notify_task_assigned(
    task_id: str,
    task_title: str,
    assignee: str,
    channel: str,
    team: Optional[str] = None,
) -> NotificationResult:
    """Уведомление о назначении задачи"""
    message = f"Вам назначена задача **'{task_title}'** (ID: {task_id})"
    return await send_notification(
        message=message,
        channel=channel,
        notification_type=NotificationType.TASK_ASSIGNED,
        title="Новая задача",
        recipients=[assignee],
        team=team,
    )


async def notify_deployment_completed(
    deployment_id: str,
    deployment_url: str,
    environment: str,
    channel: str,
    team: Optional[str] = None,
) -> NotificationResult:
    """Уведомление о завершении развертывания"""
    message = f"Развертывание в **{environment}** завершено\n\nID: {deployment_id}\nURL: {deployment_url}"
    return await send_notification(
        message=message,
        channel=channel,
        notification_type=NotificationType.DEPLOYMENT_COMPLETED,
        title="Развертывание завершено",
        team=team,
    )


async def notify_deployment_failed(
    deployment_id: str,
    error_message: str,
    channel: str,
    team: Optional[str] = None,
) -> NotificationResult:
    """Уведомление о сбое развертывания"""
    message = f"❌ Развертывание **{deployment_id}** не удалось\n\nОшибка: {error_message}"
    return await send_notification(
        message=message,
        channel=channel,
        notification_type=NotificationType.DEPLOYMENT_FAILED,
        title="Ошибка развертывания",
        team=team,
    )


async def notify_pr_created(
    pr_id: str,
    pr_title: str,
    pr_url: str,
    author: str,
    channel: str,
    team: Optional[str] = None,
) -> NotificationResult:
    """Уведомление о создании Pull Request"""
    message = f"Создан новый Pull Request **'{pr_title}'**\n\nID: {pr_id}\nАвтор: {author}\nURL: {pr_url}"
    return await send_notification(
        message=message,
        channel=channel,
        notification_type=NotificationType.PR_CREATED,
        title="Новый Pull Request",
        team=team,
    )


async def notify_pr_merged(
    pr_id: str,
    pr_title: str,
    pr_url: str,
    merger: str,
    channel: str,
    team: Optional[str] = None,
) -> NotificationResult:
    """Уведомление о слиянии Pull Request"""
    message = f"Pull Request **'{pr_title}'** (ID: {pr_id}) слит в main\n\nСлил: {merger}\nURL: {pr_url}"
    return await send_notification(
        message=message,
        channel=channel,
        notification_type=NotificationType.PR_MERGED,
        title="Pull Request слит",
        team=team,
    )
