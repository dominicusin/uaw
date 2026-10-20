"""
UAW Scenario: Create Task Workflow

Сценарий создания задачи в системе управления проектами
"Создай задачу в Asana для проекта X, назначь её на John, установи приоритет высокий"
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
from uaw.models.task import Task, TaskStatus, TaskPriority
from uaw.models.project import Project
from uaw.models.person import Person

from uaw.integrations.asana_integration import AsanaIntegration
from uaw.integrations.linear_integration import LinearIntegration
from uaw.integrations.github_integration import GitHubIntegration

from uaw.orchestrator.workflow_engine import WorkflowEngine


logger = logging.getLogger(__name__)


# Определение workflow для создания задачи
CREATE_TASK_WORKFLOW_DEFINITION = {
    "workflow_id": "workflow:create-task",
    "name": "Create Task Workflow",
    "description": "Создание задачи в системе управления проектами",
    "version": "1.0.0",
    "steps": [
        {
            "step_id": "step:parse-request",
            "name": "Парсинг запроса",
            "step_type": "action",
            "action": "parse_natural_language",
            "description": "Анализ запроса на создание задачи",
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
                    "field": "title",
                    "expected": True,
                    "action_on_failure": "request_clarification"
                },
                {
                    "type": "required_field",
                    "field": "project",
                    "expected": True,
                    "action_on_failure": "request_clarification"
                }
            ]
        },
        {
            "step_id": "step:find-project",
            "name": "Поиск проекта",
            "step_type": "action",
            "action": "find_project",
            "description": "Поиск проекта в Asana или Linear",
            "integration": "asana",
            "fallback": {
                "integration": "linear",
                "action": "find_project"
            },
            "dependencies": ["step:validate-parameters"],
            "timeout_seconds": 60,
            "retry_count": 2,
            "permission_level": "L0_READ_ONLY",
        },
        {
            "step_id": "step:find-assignee",
            "name": "Поиск исполнителя",
            "step_type": "action",
            "action": "find_person",
            "description": "Поиск пользователя по имени или email",
            "integration": "asana",
            "fallback": {
                "integration": "linear",
                "action": "find_user"
            },
            "dependencies": ["step:validate-parameters"],
            "timeout_seconds": 60,
            "retry_count": 2,
            "permission_level": "L0_READ_ONLY",
        },
        {
            "step_id": "step:create-asana-task",
            "name": "Создание задачи в Asana",
            "step_type": "action",
            "action": "create_task",
            "description": "Создание задачи в Asana с заданными параметрами",
            "integration": "asana",
            "parameters": {
                "workspace": "{{workspace}}",
                "project": "{{project_id}}",
                "name": "{{title}}",
                "notes": "{{description}}",
                "assignee": "{{assignee_id}}",
                "priority": "{{priority}}",
                "due_on": "{{due_date}}",
                "tags": ["{{tags}}"]
            },
            "dependencies": ["step:find-project", "step:find-assignee"],
            "timeout_seconds": 60,
            "retry_count": 2,
            "permission_level": "L2_SUPERVISED",
            "fallback": {
                "integration": "linear",
                "action": "create_issue",
                "parameters": {
                    "team": "{{team_id}}",
                    "title": "{{title}}",
                    "description": "{{description}}",
                    "assignee": "{{assignee_id}}",
                    "priority": "{{priority}}"
                }
            }
        },
        {
            "step_id": "step:verify-task-creation",
            "name": "Проверка создания задачи",
            "step_type": "condition",
            "action": "verify_task",
            "description": "Проверка, что задача действительно создана",
            "integration": "asana",
            "dependencies": ["step:create-asana-task"],
            "timeout_seconds": 30,
            "retry_count": 2,
            "permission_level": "L0_READ_ONLY",
            "conditions": [
                {
                    "type": "existence_check",
                    "field": "task_id",
                    "expected": True,
                    "action_on_failure": "retry"
                }
            ]
        },
        {
            "step_id": "step:link-resources",
            "name": "Связывание ресурсов",
            "step_type": "action",
            "action": "link_resources",
            "description": "Связывание созданной задачи с проектом и исполнителем",
            "dependencies": ["step:verify-task-creation"],
            "timeout_seconds": 30,
            "retry_count": 1,
            "permission_level": "L0_READ_ONLY",
        },
        {
            "step_id": "step:notify-assignee",
            "name": "Уведомление исполнителя",
            "step_type": "action",
            "action": "send_notification",
            "description": "Отправка уведомления исполнителю о новой задаче",
            "adapter": "teams",
            "fallback": {
                "adapter": "slack"
            },
            "dependencies": ["step:link-resources"],
            "timeout_seconds": 60,
            "retry_count": 2,
            "permission_level": "L2_SUPERVISED",
        },
        {
            "step_id": "step:generate-report",
            "name": "Формирование отчёта",
            "step_type": "action",
            "action": "generate_report",
            "description": "Сбор информации и формирование итогового отчёта",
            "dependencies": ["step:notify-assignee"],
            "timeout_seconds": 30,
            "retry_count": 0,
            "permission_level": "L0_READ_ONLY",
        }
    ]
}


@dataclass
class CreateTaskResult:
    """Результат создания задачи"""
    task_id: str
    task_url: str
    project_id: str
    assignee_id: str
    title: str
    description: str
    priority: str
    due_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_url": self.task_url,
            "project_id": self.project_id,
            "assignee_id": self.assignee_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "external_ids": self.external_ids,
        }


class CreateTaskWorkflow:
    """Workflow для создания задачи"""
    
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
        
        self.integrations: Dict[str, Any] = {
            "asana": AsanaIntegration(),
            "linear": LinearIntegration(),
        }
        
    def create_workflow(
        self,
        title: str,
        project_name: str,
        assignee_name: str,
        description: str = "",
        priority: str = "medium",
        due_date: Optional[str] = None,
        tags: Optional[List[str]] = None,
        workspace: str = "default",
    ) -> Workflow:
        """Создание workflow для создания задачи"""
        workflow_id = f"workflow:create-task:{uuid.uuid4()}"
        
        steps = []
        for step_config in CREATE_TASK_WORKFLOW_DEFINITION["steps"]:
            step = WorkflowStep(
                uaw_id=step_config["step_id"],
                name=step_config["name"],
                step_type=WorkflowStepType(step_config["step_type"]),
                description=step_config["description"],
                integration=step_config.get("integration"),
                adapter=step_config.get("adapter"),
                action=step_config["action"],
                parameters=self._resolve_parameters(step_config.get("parameters", {}), {
                    "title": title,
                    "project": project_name,
                    "project_id": "TBD",
                    "assignee": assignee_name,
                    "assignee_id": "TBD",
                    "description": description,
                    "priority": priority,
                    "due_date": due_date,
                    "tags": tags or [],
                    "workspace": workspace,
                    "team_id": "TBD",
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
            name=CREATE_TASK_WORKFLOW_DEFINITION["name"],
            description=CREATE_TASK_WORKFLOW_DEFINITION["description"],
            version=CREATE_TASK_WORKFLOW_DEFINITION["version"],
            status=WorkflowStatus.PENDING,
            steps=steps,
            triggers=[
                WorkflowTrigger(
                    trigger_id=f"trigger:{workflow_id}",
                    trigger_type="manual",
                    description="Ручной запуск создания задачи"
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
    
    async def execute(
        self,
        workflow: Workflow,
        context: Optional[Dict[str, Any]] = None,
    ) -> CreateTaskResult:
        """Выполнение workflow создания задачи"""
        context = context or {}
        result = CreateTaskResult(
            task_id="",
            task_url="",
            project_id="",
            assignee_id="",
            title="",
            description="",
            priority="",
        )
        
        # Выполнение через WorkflowEngine
        executed_workflow = await self.workflow_engine.execute_workflow(
            workflow, 
            mode=ExecutionMode.SMART,
            context=context
        )
        
        # Извлечение результатов
        for step in executed_workflow.steps:
            if step.uaw_id == "step:create-asana-task" and step.result:
                result.task_id = step.result.get("task_id", "")
                result.task_url = step.result.get("task_url", "")
                result.project_id = step.result.get("project_id", "")
                result.assignee_id = step.result.get("assignee_id", "")
                result.title = step.result.get("title", "")
                result.description = step.result.get("description", "")
                result.priority = step.result.get("priority", "")
                result.external_ids = step.result.get("external_ids", {})
                
        return result


async def create_task(
    title: str,
    project_name: str,
    assignee_name: str,
    description: str = "",
    priority: str = "medium",
    due_date: Optional[str] = None,
    tags: Optional[List[str]] = None,
    workspace: str = "default",
) -> CreateTaskResult:
    """
    Удобная функция для создания задачи
    
    Args:
        title: Заголовок задачи
        project_name: Название проекта
        assignee_name: Имя исполнителя
        description: Описание задачи
        priority: Приоритет (low, medium, high, urgent)
        due_date: Срок выполнения (YYYY-MM-DD)
        tags: Метки
        workspace: Рабочая область
        
    Returns:
        CreateTaskResult с информацией о созданной задаче
    """
    workflow = CreateTaskWorkflow()
    workflow_obj = workflow.create_workflow(
        title=title,
        project_name=project_name,
        assignee_name=assignee_name,
        description=description,
        priority=priority,
        due_date=due_date,
        tags=tags,
        workspace=workspace,
    )
    
    return await workflow.execute(
        workflow_obj,
        context={
            "title": title,
            "project": project_name,
            "assignee": assignee_name,
            "description": description,
            "priority": priority,
            "due_date": due_date,
            "tags": tags,
            "workspace": workspace,
        }
    )
