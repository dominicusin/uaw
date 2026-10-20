"""
UAW Scenario: Deployment Workflow

Сценарий развертывания приложения
"Разверни новую версию приложения на Vercel/Netlify из ветки main"
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
from uaw.models.deployment import Deployment, DeploymentStatus, BuildInfo, HealthCheck
from uaw.models.repository import Repository, Branch

from uaw.integrations.github_integration import GitHubIntegration

from uaw.adapters.vercel_adapter import VercelAdapter
from uaw.adapters.netlify_adapter import NetlifyAdapter

from uaw.orchestrator.workflow_engine import WorkflowEngine


logger = logging.getLogger(__name__)


# Определение workflow для развертывания
DEPLOY_WORKFLOW_DEFINITION = {
    "workflow_id": "workflow:deploy",
    "name": "Deployment Workflow",
    "description": "Развертывание приложения на Vercel или Netlify",
    "version": "1.0.0",
    "steps": [
        {
            "step_id": "step:parse-request",
            "name": "Парсинг запроса",
            "step_type": "action",
            "action": "parse_natural_language",
            "description": "Анализ запроса на развертывание",
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
                    "field": "branch",
                    "expected": True,
                    "action_on_failure": "use_default"
                },
                {
                    "type": "required_field",
                    "field": "environment",
                    "expected": True,
                    "action_on_failure": "use_default"
                }
            ]
        },
        {
            "step_id": "step:check-branch",
            "name": "Проверка ветки",
            "step_type": "action",
            "action": "get_branch",
            "description": "Проверка существования ветки в репозитории",
            "integration": "github",
            "dependencies": ["step:validate-parameters"],
            "timeout_seconds": 60,
            "retry_count": 2,
            "permission_level": "L0_READ_ONLY",
        },
        {
            "step_id": "step:run-tests",
            "name": "Запуск тестов",
            "step_type": "action",
            "action": "run_workflow",
            "description": "Запуск тестов перед развертыванием",
            "integration": "github",
            "parameters": {
                "workflow_id": "test.yml"
            },
            "dependencies": ["step:check-branch"],
            "timeout_seconds": 300,
            "retry_count": 1,
            "permission_level": "L3_POLICY_BASED",
        },
        {
            "step_id": "step:verify-tests",
            "name": "Проверка тестов",
            "step_type": "condition",
            "action": "verify_workflow_run",
            "description": "Ожидание и проверка результатов тестов",
            "integration": "github",
            "dependencies": ["step:run-tests"],
            "timeout_seconds": 600,
            "retry_count": 5,
            "retry_delay": 30,
            "permission_level": "L0_READ_ONLY",
            "conditions": [
                {
                    "type": "status_check",
                    "field": "conclusion",
                    "expected": "success",
                    "action_on_failure": "stop_and_notify"
                }
            ]
        },
        {
            "step_id": "step:create-deployment",
            "name": "Создание deployment",
            "step_type": "action",
            "action": "create_deployment",
            "description": "Развертывание на Vercel или Netlify",
            "adapter": "vercel",
            "fallback": {
                "adapter": "netlify",
                "action": "create_deployment"
            },
            "parameters": {
                "branch": "{{branch}}",
                "environment": "{{environment}}",
                "comment": "Deployment from UAW"
            },
            "dependencies": ["step:verify-tests"],
            "timeout_seconds": 300,
            "retry_count": 2,
            "permission_level": "L3_POLICY_BASED",
        },
        {
            "step_id": "step:monitor-deployment",
            "name": "Мониторинг deployment",
            "step_type": "condition",
            "action": "monitor_deployment",
            "description": "Ожидание завершения развертывания",
            "adapter": "vercel",
            "fallback": {
                "adapter": "netlify",
                "action": "get_deployment"
            },
            "dependencies": ["step:create-deployment"],
            "timeout_seconds": 600,
            "retry_count": 5,
            "retry_delay": 30,
            "permission_level": "L0_READ_ONLY",
            "conditions": [
                {
                    "type": "status_check",
                    "field": "status",
                    "expected": "ready",
                    "action_on_failure": "stop_and_notify"
                }
            ]
        },
        {
            "step_id": "step:verify-health",
            "name": "Проверка health checks",
            "step_type": "action",
            "action": "check_health",
            "description": "Проверка работоспособности развернутого приложения",
            "adapter": "vercel",
            "fallback": {
                "adapter": "netlify"
            },
            "dependencies": ["step:monitor-deployment"],
            "timeout_seconds": 120,
            "retry_count": 3,
            "retry_delay": 30,
            "permission_level": "L0_READ_ONLY",
        },
        {
            "step_id": "step:notify-team",
            "name": "Уведомление команды",
            "step_type": "action",
            "action": "send_deployment_notification",
            "description": "Отправка уведомления о развертывании",
            "adapter": "teams",
            "fallback": {
                "adapter": "slack"
            },
            "dependencies": ["step:verify-health"],
            "timeout_seconds": 60,
            "retry_count": 2,
            "permission_level": "L2_SUPERVISED",
        },
        {
            "step_id": "step:link-resources",
            "name": "Связывание ресурсов",
            "step_type": "action",
            "action": "link_resources",
            "description": "Связывание deployment с коммитом и веткой",
            "dependencies": ["step:notify-team"],
            "timeout_seconds": 30,
            "retry_count": 1,
            "permission_level": "L0_READ_ONLY",
        },
        {
            "step_id": "step:generate-report",
            "name": "Формирование отчёта",
            "step_type": "action",
            "action": "generate_report",
            "description": "Сбор информации и формирование итогового отчёта",
            "dependencies": ["step:link-resources"],
            "timeout_seconds": 30,
            "retry_count": 0,
            "permission_level": "L0_READ_ONLY",
        }
    ]
}


@dataclass
class DeployResult:
    """Результат развертывания"""
    deployment_id: str
    deployment_url: str
    status: str
    environment: str
    branch: str
    commit_sha: str
    repository_id: str
    build_info: Optional[Dict[str, Any]] = None
    health_checks: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "deployment_id": self.deployment_id,
            "deployment_url": self.deployment_url,
            "status": self.status,
            "environment": self.environment,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "repository_id": self.repository_id,
            "build_info": self.build_info,
            "health_checks": self.health_checks,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "external_ids": self.external_ids,
        }


class DeployWorkflow:
    """Workflow для развертывания"""
    
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
            "github": GitHubIntegration(),
        }
        self.adapters: Dict[str, Any] = {
            "vercel": VercelAdapter(),
            "netlify": NetlifyAdapter(),
        }
        
    def create_workflow(
        self,
        repository_id: str,
        branch: str = "main",
        environment: str = "production",
        comment: str = "Deployment from UAW",
    ) -> Workflow:
        """Создание workflow для развертывания"""
        workflow_id = f"workflow:deploy:{uuid.uuid4()}"
        
        steps = []
        for step_config in DEPLOY_WORKFLOW_DEFINITION["steps"]:
            step = WorkflowStep(
                uaw_id=step_config["step_id"],
                name=step_config["name"],
                step_type=WorkflowStepType(step_config["step_type"]),
                description=step_config["description"],
                integration=step_config.get("integration"),
                adapter=step_config.get("adapter"),
                action=step_config["action"],
                parameters=self._resolve_parameters(step_config.get("parameters", {}), {
                    "repository_id": repository_id,
                    "branch": branch,
                    "environment": environment,
                    "comment": comment,
                }),
                dependencies=step_config.get("dependencies", []),
                timeout_seconds=step_config.get("timeout_seconds", 30),
                retry_count=step_config.get("retry_count", 0),
                retry_delay=step_config.get("retry_delay", 10),
                permission_level=PermissionLevel(step_config.get("permission_level", "L3_POLICY_BASED")),
                conditions=[
                    WorkflowCondition(**c) for c in step_config.get("conditions", [])
                ],
                fallback=step_config.get("fallback"),
            )
            steps.append(step)
        
        return Workflow(
            uaw_id=workflow_id,
            name=DEPLOY_WORKFLOW_DEFINITION["name"],
            description=DEPLOY_WORKFLOW_DEFINITION["description"],
            version=DEPLOY_WORKFLOW_DEFINITION["version"],
            status=WorkflowStatus.PENDING,
            steps=steps,
            triggers=[
                WorkflowTrigger(
                    trigger_id=f"trigger:{workflow_id}",
                    trigger_type="manual",
                    description="Ручной запуск развертывания"
                ),
                WorkflowTrigger(
                    trigger_id=f"trigger:{workflow_id}:webhook",
                    trigger_type="webhook",
                    description="Запуск через webhook (GitHub push)",
                    event_type="push",
                    filter_conditions={"branch": branch}
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
    ) -> DeployResult:
        """Выполнение workflow развертывания"""
        context = context or {}
        result = DeployResult(
            deployment_id="",
            deployment_url="",
            status="pending",
            environment="",
            branch="",
            commit_sha="",
            repository_id="",
        )
        
        # Выполнение через WorkflowEngine
        executed_workflow = await self.workflow_engine.execute_workflow(
            workflow, 
            mode=ExecutionMode.SMART,
            context=context
        )
        
        # Извлечение результатов
        for step in executed_workflow.steps:
            if step.uaw_id == "step:create-deployment" and step.result:
                result.deployment_id = step.result.get("deployment_id", "")
                result.deployment_url = step.result.get("url", "")
                result.status = step.result.get("status", "")
                result.environment = step.result.get("environment", "")
                result.branch = step.result.get("branch", "")
                result.commit_sha = step.result.get("commit_sha", "")
                result.repository_id = step.result.get("repository_id", "")
                result.external_ids = step.result.get("external_ids", {})
                
            if step.uaw_id == "step:verify-health" and step.result:
                result.health_checks = step.result.get("health_checks", [])
                result.completed_at = datetime.utcnow()
                
        return result


async def deploy(
    repository_id: str,
    branch: str = "main",
    environment: str = "production",
    comment: str = "Deployment from UAW",
) -> DeployResult:
    """
    Удобная функция для развертывания
    
    Args:
        repository_id: ID репозитория
        branch: Ветка для развертывания
        environment: Окружение (production, staging, preview)
        comment: Комментарий к развертыванию
        
    Returns:
        DeployResult с информацией о развертывании
    """
    workflow = DeployWorkflow()
    workflow_obj = workflow.create_workflow(
        repository_id=repository_id,
        branch=branch,
        environment=environment,
        comment=comment,
    )
    
    return await workflow.execute(
        workflow_obj,
        context={
            "repository_id": repository_id,
            "branch": branch,
            "environment": environment,
            "comment": comment,
        }
    )
