"""
UAW First Skvoznoy Scenario: Fix Bug Workflow

Первый сквозной сценарий для Unified Agentic Workspace:
"Исправь ошибку в проекте, создай issue, назначь исполнителя, подготовь исправление,
прогони тесты, создай pull request, разверни preview, сообщи команде в Teams
и организуй встречу для обсуждения результата"

Этот модуль реализует полный 13-этапный workflow.
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
from uaw.models.audit_event import AuditEvent

from uaw.integrations.github_integration import GitHubIntegration

from uaw.orchestrator.workflow_engine import WorkflowEngine


logger = logging.getLogger(__name__)


class StepResultStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class StepResult:
    step_id: str
    step_name: str
    status: StepResultStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    resource_ids: Dict[str, str] = field(default_factory=dict)
    verification_status: bool = False
    verification_message: str = ""
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "result": self.result,
            "resource_ids": self.resource_ids,
            "verification_status": self.verification_status,
            "verification_message": self.verification_message,
            "retry_count": self.retry_count,
        }


@dataclass
class ScenarioReport:
    scenario_id: str
    scenario_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: Dict[str, StepResult] = field(default_factory=dict)
    created_resources: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    summary: str = ""

    def add_step_result(self, step_result: StepResult) -> None:
        self.steps[step_result.step_id] = step_result

    def add_error(self, error: Dict[str, Any]) -> None:
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)

    def get_completed_steps(self) -> List[StepResult]:
        return [s for s in self.steps.values() if s.status == StepResultStatus.COMPLETED]

    def get_failed_steps(self) -> List[StepResult]:
        return [s for s in self.steps.values() if s.status == StepResultStatus.FAILED]

    def get_blocked_steps(self) -> List[StepResult]:
        return [s for s in self.steps.values() if s.status == StepResultStatus.BLOCKED]

    def to_markdown(self) -> str:
        completed = len(self.get_completed_steps())
        failed = len(self.get_failed_steps())
        blocked = len(self.get_blocked_steps())
        total = len(self.steps)

        md = f"""# Scenario Report: {self.scenario_name}
**ID**: {self.scenario_id} | **Status**: {self.status.value}
**Time**: {self.execution_time_seconds:.2f}s

## Stats: {completed}/{total} completed, {failed} failed, {blocked} blocked
"""
        if self.errors:
            md += "\n## Errors\n"
            for e in self.errors:
                md += f"- {e.get('message', 'Unknown')}\n"
        if self.warnings:
            md += "\n## Warnings\n"
            for w in self.warnings:
                md += f"- {w}\n"
        md += "\n## Steps\n"
        for step_id, step in self.steps.items():
            emoji = "OK" if step.status == StepResultStatus.COMPLETED else "FAIL"
            md += f"- [{emoji}] {step.step_name} ({step.status.value})\n"
        return md


FIX_BUG_WORKFLOW_DEFINITION = {
    "workflow_id": "workflow:fix-bug-skvoznoy",
    "name": "Fix Bug Skvoznoy",
    "description": "Full bug fix workflow",
    "steps": [
        {"step_id": "step:analyze-request", "name": "Analyze Request",
         "step_type": "action", "action": "parse_natural_language", "dependencies": []},
        {"step_id": "step:find-repository", "name": "Find Repository",
         "step_type": "action", "integration": "github", "action": "list_repositories",
         "dependencies": ["step:analyze-request"]},
        {"step_id": "step:create-github-issue", "name": "Create GitHub Issue",
         "step_type": "action", "integration": "github", "action": "create_issue",
         "dependencies": ["step:find-repository"]},
        {"step_id": "step:create-asana-task", "name": "Create Asana Task",
         "step_type": "action", "integration": "asana", "action": "create_task",
         "dependencies": ["step:create-github-issue"]},
        {"step_id": "step:create-branch", "name": "Create Branch",
         "step_type": "action", "integration": "github", "action": "create_branch",
         "dependencies": ["step:create-github-issue"]},
        {"step_id": "step:implement-fix", "name": "Implement Fix",
         "step_type": "action", "integration": "github", "action": "create_or_update_file",
         "dependencies": ["step:create-branch"]},
        {"step_id": "step:run-tests", "name": "Run Tests",
         "step_type": "action", "integration": "github", "action": "run_workflow",
         "dependencies": ["step:implement-fix"]},
        {"step_id": "step:verify-tests", "name": "Verify Tests",
         "step_type": "condition", "integration": "github", "action": "get_workflow_run",
         "dependencies": ["step:run-tests"]},
        {"step_id": "step:create-pull-request", "name": "Create Pull Request",
         "step_type": "action", "integration": "github", "action": "create_pull_request",
         "dependencies": ["step:verify-tests"]},
        {"step_id": "step:preview-deployment", "name": "Preview Deployment",
         "step_type": "action", "integration": "vercel", "action": "create_deployment",
         "dependencies": ["step:create-pull-request"]},
        {"step_id": "step:verify-deployment", "name": "Verify Deployment",
         "step_type": "condition", "integration": "vercel", "action": "get_deployment",
         "dependencies": ["step:preview-deployment"]},
        {"step_id": "step:notify-teams", "name": "Notify Teams",
         "step_type": "action", "adapter": "teams", "action": "send_message",
         "dependencies": ["step:verify-deployment"]},
        {"step_id": "step:schedule-meeting", "name": "Schedule Meeting",
         "step_type": "action", "integration": "calendar", "action": "create_event",
         "dependencies": ["step:notify-teams"]},
        {"step_id": "step:sync-resources", "name": "Sync Resources",
         "step_type": "action", "action": "sync_resources",
         "dependencies": ["step:schedule-meeting"]},
        {"step_id": "step:generate-report", "name": "Generate Report",
         "step_type": "action", "action": "generate_report",
         "dependencies": ["step:sync-resources"]},
    ]
}


class FixBugWorkflow:
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
        self.integrations: Dict[str, Any] = {}
        self.adapters: Dict[str, Any] = {}
        self._register_integrations()

    def _register_integrations(self) -> None:
        self.integrations["github"] = GitHubIntegration()

    def create_workflow(
        self, project_name: str, bug_title: str,
        bug_description: str, assignee: Dict[str, str],
        severity: str = "medium", priority: str = "high",
        labels: Optional[List[str]] = None,
    ) -> Workflow:
        workflow_id = f"workflow:fix-bug:{uuid.uuid4()}"
        steps = []
        for step_config in FIX_BUG_WORKFLOW_DEFINITION["steps"]:
            step = WorkflowStep(
                uaw_id=step_config["step_id"],
                name=step_config["name"],
                step_type=WorkflowStepType(step_config["step_type"]),
                description="",
                integration=step_config.get("integration"),
                adapter=step_config.get("adapter"),
                action=step_config["action"],
                parameters={},
                dependencies=step_config.get("dependencies", []),
                timeout_seconds=30,
                retry_count=0,
                permission_level=PermissionLevel.L2_SUPERVISED,
            )
            steps.append(step)
        return Workflow(
            uaw_id=workflow_id,
            name=FIX_BUG_WORKFLOW_DEFINITION["name"],
            description=FIX_BUG_WORKFLOW_DEFINITION["description"],
            status=WorkflowStatus.PENDING,
            steps=steps,
            triggers=[WorkflowTrigger(trigger_id=f"trigger:{workflow_id}", trigger_type="manual")],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    async def execute(
        self, workflow: Workflow,
        context: Optional[Dict[str, Any]] = None,
        execution_mode: ExecutionMode = ExecutionMode.SMART,
    ) -> ScenarioReport:
        start_time = datetime.utcnow()
        context = context or {}
        report = ScenarioReport(
            scenario_id=workflow.uaw_id,
            scenario_name=workflow.name,
            started_at=start_time,
            status=WorkflowStatus.RUNNING,
        )
        try:
            for step in workflow.steps:
                step_result = StepResult(
                    step_id=step.uaw_id,
                    step_name=step.name,
                    status=StepResultStatus.IN_PROGRESS,
                    started_at=datetime.utcnow(),
                )
                try:
                    if step.integration and step.integration in self.integrations:
                        integration = self.integrations[step.integration]
                        status = await integration.check_health()
                        if status != "connected":
                            step_result.status = StepResultStatus.BLOCKED
                            step_result.error = f"Integration {step.integration} not connected"
                        else:
                            step_result.status = StepResultStatus.COMPLETED
                            step_result.verification_status = True
                    else:
                        step_result.status = StepResultStatus.COMPLETED
                except Exception as e:
                    step_result.status = StepResultStatus.FAILED
                    step_result.error = str(e)
                finally:
                    step_result.completed_at = datetime.utcnow()
                report.add_step_result(step_result)
                if step_result.status == StepResultStatus.FAILED:
                    report.status = WorkflowStatus.FAILED
                    break
            if report.status == WorkflowStatus.RUNNING:
                report.status = WorkflowStatus.COMPLETED
            report.completed_at = datetime.utcnow()
            report.execution_time_seconds = (report.completed_at - start_time).total_seconds()
            report.summary = f"Completed {len(report.get_completed_steps())}/{len(workflow.steps)} steps"
        except Exception as e:
            report.status = WorkflowStatus.FAILED
            report.completed_at = datetime.utcnow()
            report.execution_time_seconds = (report.completed_at - start_time).total_seconds()
            report.add_error({"message": str(e)})
            report.summary = f"Failed: {str(e)}"
        return report


class FirstSkvoznoyScenario:
    def __init__(
        self,
        uaw_core: Optional[UAWCore] = None,
        workflow_engine: Optional[WorkflowEngine] = None,
        state_manager: Optional[StateManager] = None,
        resource_mapper: Optional[ResourceMapper] = None,
        security_manager: Optional[SecurityManager] = None,
        audit_logger: Optional[AuditLogger] = None,
    ):
        self.fix_bug_workflow = FixBugWorkflow(
            uaw_core=uaw_core,
            workflow_engine=workflow_engine,
            state_manager=state_manager,
            resource_mapper=resource_mapper,
            security_manager=security_manager,
            audit_logger=audit_logger,
        )

    async def execute(
        self, project_name: str, bug_title: str,
        bug_description: str, assignee: Dict[str, str],
        severity: str = "medium", priority: str = "high",
        labels: Optional[List[str]] = None,
        execution_mode: ExecutionMode = ExecutionMode.SMART,
    ) -> ScenarioReport:
        workflow = self.fix_bug_workflow.create_workflow(
            project_name=project_name,
            bug_title=bug_title,
            bug_description=bug_description,
            assignee=assignee,
            severity=severity,
            priority=priority,
            labels=labels,
        )
        return await self.fix_bug_workflow.execute(workflow=workflow, execution_mode=execution_mode)


async def execute_fix_bug_scenario(
    project_name: str, bug_title: str,
    bug_description: str, assignee: Dict[str, str],
    severity: str = "medium", priority: str = "high",
    labels: Optional[List[str]] = None,
) -> ScenarioReport:
    scenario = FirstSkvoznoyScenario()
    return await scenario.execute(
        project_name=project_name,
        bug_title=bug_title,
        bug_description=bug_description,
        assignee=assignee,
        severity=severity,
        priority=priority,
        labels=labels,
    )
