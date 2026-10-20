"""
UAW Core - Central coordinator for the Unified Agentic Workspace
Центральный координатор системы UAW
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

from .state_manager import StateManager
from .resource_mapping import ResourceMapper
from .security import SecurityManager, PermissionLevel
from .audit import AuditLogger, AuditEventType


class TaskStatus(Enum):
    """Status of a task in the workflow"""
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    WAITING_APPROVAL = auto()


class IntegrationStatus(Enum):
    """Status of integration connection"""
    CONNECTED = "connected"
    PARTIAL = "partial"
    READ_ONLY = "read_only"
    UNAUTHORISED = "unauthorised"
    UNAVAILABLE = "unavailable"


@dataclass
class WorkflowStep:
    """Single step in a workflow"""
    id: str
    name: str
    description: str
    action: str  # Integration action to execute
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    timeout: int = 60  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "status": self.status.name,
            "result": self.result,
            "error": self.error
        }


@dataclass
class Workflow:
    """Complete workflow definition"""
    id: str
    name: str
    description: str
    user_request: str
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    current_step: Optional[str] = None
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def get_execution_order(self) -> List[str]:
        """Get steps in execution order respecting dependencies"""
        visited = set()
        order = []
        
        def visit(step_id: str):
            if step_id in visited:
                return
            for dep in self.dependencies.get(step_id, []):
                visit(dep)
            visited.add(step_id)
            order.append(step_id)
        
        for step_id in self.steps:
            visit(step_id)
        
        return order
    
    def get_ready_steps(self) -> List[str]:
        """Get steps that are ready to execute (all dependencies completed)"""
        ready = []
        for step_id, step in self.steps.items():
            if step.status in [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS]:
                continue
            
            # Check if all dependencies are completed
            deps_completed = all(
                self.steps[dep].status == TaskStatus.COMPLETED
                for dep in step.dependencies
            )
            
            if deps_completed:
                ready.append(step_id)
        
        return ready
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "user_request": self.user_request,
            "status": self.status.name,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "current_step": self.current_step,
            "steps": {sid: step.to_dict() for sid, step in self.steps.items()},
            "dependencies": self.dependencies,
            "results": self.results,
            "errors": self.errors
        }


class UAWCore:
    """
    Central coordinator for UAW system.
    Converts user requests into executable workflows,
    manages state, and coordinates across integrations.
    """
    
    def __init__(
        self,
        state_dir: Union[str, Path] = "/workspace/uaw/state",
        config_dir: Union[str, Path] = "/workspace/uaw/config"
    ):
        self.state_dir = Path(state_dir)
        self.config_dir = Path(config_dir)
        
        # Initialize components
        self.state_manager = StateManager(state_dir)
        self.resource_mapper = ResourceMapper()
        self.security_manager = SecurityManager()
        self.audit_logger = AuditLogger()
        
        # Integration registry (will be initialized with available integrations)
        self.integration_registry = None
        
        # Adapter registry
        self.adapter_registry = None
        
        # Active workflows
        self.active_workflows: Dict[str, Workflow] = {}
        
        # Initialize directories
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing state
        self._load_state()
    
    def initialize_registry(self, integration_registry):
        """Initialize integration registry"""
        self.integration_registry = integration_registry
    
    def initialize_adapters(self, adapter_registry):
        """Initialize adapter registry"""
        self.adapter_registry = adapter_registry
    
    def _load_state(self):
        """Load persistent state from disk"""
        state_file = self.state_dir / "uaw_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    # Restore active workflows
                    for wf_data in state.get("active_workflows", []):
                        workflow = self._from_dict(wf_data)
                        self.active_workflows[workflow.id] = workflow
            except Exception as e:
                self.audit_logger.log(
                    AuditEventType.ERROR,
                    "Failed to load state",
                    {"error": str(e)},
                    severity="high"
                )
    
    def _save_state(self):
        """Save persistent state to disk"""
        state_file = self.state_dir / "uaw_state.json"
        try:
            state = {
                "active_workflows": [
                    wf.to_dict() for wf in self.active_workflows.values()
                ],
                "saved_at": datetime.now(timezone.utc).isoformat()
            }
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.audit_logger.log(
                AuditEventType.ERROR,
                "Failed to save state",
                {"error": str(e)},
                severity="high"
            )
    
    def _from_dict(self, data: Dict[str, Any]) -> Workflow:
        """Create workflow from dictionary"""
        workflow = Workflow(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            user_request=data["user_request"],
            status=TaskStatus[data["status"]],
            created_at=data["created_at"],
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            current_step=data.get("current_step"),
            results=data.get("results", {}),
            errors=data.get("errors", [])
        )
        
        for step_id, step_data in data.get("steps", {}).items():
            step = WorkflowStep(
                id=step_data["id"],
                name=step_data["name"],
                description=step_data["description"],
                action=step_data["action"],
                parameters=step_data["parameters"],
                dependencies=step_data.get("dependencies", []),
                status=TaskStatus[step_data["status"]],
                result=step_data.get("result"),
                error=step_data.get("error"),
                retries=step_data.get("retries", 0),
                max_retries=step_data.get("max_retries", 3),
                timeout=step_data.get("timeout", 60)
            )
            workflow.steps[step_id] = step
        
        workflow.dependencies = data.get("dependencies", {})
        return workflow
    
    async def parse_request(self, user_request: str) -> Dict[str, Any]:
        """
        Parse user request and determine intent.
        
        Args:
            user_request: Natural language request from user
            
        Returns:
            Dict with intent, entities, and suggested workflow
        """
        self.audit_logger.log(
            AuditEventType.REQUEST,
            "Parsing user request",
            {"request": user_request[:200]}
        )
        
        # Simple NLP parsing (can be enhanced with LLM)
        request_lower = user_request.lower()
        
        intent = {
            "action": "unknown",
            "entities": {},
            "priority": "normal"
        }
        
        # Detect main actions
        if any(word in request_lower for word in ["исправь", "fix", "починь", "реши"]):
            intent["action"] = "fix_issue"
        elif any(word in request_lower for word in ["создай", "create", "сделай"]):
            intent["action"] = "create"
        elif any(word in request_lower for word in ["найди", "search", "поиск"]):
            intent["action"] = "search"
        elif any(word in request_lower for word in ["разверни", "deploy", "задеплой"]):
            intent["action"] = "deploy"
        elif any(word in request_lower for word in ["уведоми", "сообщи", "notify"]):
            intent["action"] = "notify"
        
        # Extract entities
        if "github" in request_lower or "репозиторий" in request_lower:
            intent["entities"]["service"] = "github"
        if "asana" in request_lower or "задача" in request_lower:
            intent["entities"]["service"] = "asana"
        if "календарь" in request_lower or "встреча" in request_lower:
            intent["entities"]["service"] = "calendar"
        if "slack" in request_lower or "команда" in request_lower:
            intent["entities"]["service"] = "slack"
        
        # Detect urgency
        if any(word in request_lower for word in ["срочно", "urgent", "немедленно"]):
            intent["priority"] = "high"
        
        self.audit_logger.log(
            AuditEventType.PARSE,
            "Request parsed",
            {"intent": intent}
        )
        
        return intent
    
    async def plan_workflow(
        self,
        user_request: str,
        intent: Optional[Dict[str, Any]] = None
    ) -> Workflow:
        """
        Create a workflow plan from user request.
        
        Args:
            user_request: Natural language request
            intent: Pre-parsed intent (optional)
            
        Returns:
            Workflow object with steps and dependencies
        """
        if intent is None:
            intent = await self.parse_request(user_request)
        
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        
        # Create workflow based on intent
        if intent["action"] == "fix_issue":
            workflow = self._create_fix_issue_workflow(workflow_id, user_request, intent)
        elif intent["action"] == "create":
            workflow = self._create_create_workflow(workflow_id, user_request, intent)
        elif intent["action"] == "deploy":
            workflow = self._create_deploy_workflow(workflow_id, user_request, intent)
        else:
            # Default workflow
            workflow = Workflow(
                id=workflow_id,
                name="Custom Workflow",
                description=f"Workflow for: {user_request[:100]}",
                user_request=user_request
            )
            
            # Add generic step
            step_id = f"step_{uuid.uuid4().hex[:8]}"
            workflow.steps[step_id] = WorkflowStep(
                id=step_id,
                name="Process Request",
                description="Process user request",
                action="process_request",
                parameters={"request": user_request}
            )
        
        self.audit_logger.log(
            AuditEventType.PLAN,
            "Workflow planned",
            {
                "workflow_id": workflow.id,
                "name": workflow.name,
                "steps": len(workflow.steps)
            }
        )
        
        return workflow
    
    def _create_fix_issue_workflow(
        self,
        workflow_id: str,
        user_request: str,
        intent: Dict[str, Any]
    ) -> Workflow:
        """Create workflow for fixing an issue"""
        workflow = Workflow(
            id=workflow_id,
            name="Fix Issue Workflow",
            description="Find repository, create issue, implement fix, test, PR, deploy",
            user_request=user_request
        )
        
        # Step 1: Find repository
        step1 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Find Repository",
            description="Search for relevant GitHub repository",
            action="github_search_repositories",
            parameters={"query": intent.get("repository", "")}
        )
        workflow.steps[step1.id] = step1
        
        # Step 2: Create issue
        step2 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Create Issue",
            description="Create GitHub issue for the fix",
            action="github_create_issue",
            parameters={"title": "Fix: " + user_request[:50], "body": user_request},
            dependencies=[step1.id]
        )
        workflow.steps[step2.id] = step2
        workflow.dependencies[step2.id] = [step1.id]
        
        # Step 3: Create task in Asana
        step3 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Create Asana Task",
            description="Create corresponding task in Asana",
            action="asana_create_task",
            parameters={"name": "Fix: " + user_request[:50]},
            dependencies=[step2.id]
        )
        workflow.steps[step3.id] = step3
        workflow.dependencies[step3.id] = [step2.id]
        
        # Step 4: Link issue and task
        step4 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Link Resources",
            description="Link GitHub issue with Asana task",
            action="uaw_link_resources",
            parameters={},
            dependencies=[step2.id, step3.id]
        )
        workflow.steps[step4.id] = step4
        workflow.dependencies[step4.id] = [step2.id, step3.id]
        
        # Step 5: Create branch
        step5 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Create Branch",
            description="Create feature branch for fix",
            action="github_create_branch",
            parameters={"branch": "fix/" + uuid.uuid4().hex[:8]},
            dependencies=[step4.id]
        )
        workflow.steps[step5.id] = step5
        workflow.dependencies[step5.id] = [step4.id]
        
        # Step 6: Implement fix
        step6 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Implement Fix",
            description="Make code changes",
            action="github_update_file",
            parameters={},
            dependencies=[step5.id]
        )
        workflow.steps[step6.id] = step6
        workflow.dependencies[step6.id] = [step5.id]
        
        # Step 7: Run tests
        step7 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Run Tests",
            description="Run automated tests",
            action="github_run_tests",
            parameters={},
            dependencies=[step6.id]
        )
        workflow.steps[step7.id] = step7
        workflow.dependencies[step7.id] = [step6.id]
        
        # Step 8: Create PR
        step8 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Create Pull Request",
            description="Create PR for the fix",
            action="github_create_pull_request",
            parameters={},
            dependencies=[step7.id]
        )
        workflow.steps[step8.id] = step8
        workflow.dependencies[step8.id] = [step7.id]
        
        # Step 9: Request review
        step9 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Request Review",
            description="Request code review",
            action="github_request_review",
            parameters={},
            dependencies=[step8.id]
        )
        workflow.steps[step9.id] = step9
        workflow.dependencies[step9.id] = [step8.id]
        
        # Step 10: Deploy to preview (if available)
        step10 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Deploy to Preview",
            description="Deploy to preview environment",
            action="netlify_deploy",
            parameters={"environment": "preview"},
            dependencies=[step9.id]
        )
        workflow.steps[step10.id] = step10
        workflow.dependencies[step10.id] = [step9.id]
        
        # Step 11: Verify deployment
        step11 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Verify Deployment",
            description="Check deployment health",
            action="netlify_check_health",
            parameters={},
            dependencies=[step10.id]
        )
        workflow.steps[step11.id] = step11
        workflow.dependencies[step11.id] = [step10.id]
        
        # Step 12: Notify team
        step12 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Notify Team",
            description="Send notification to team",
            action="slack_send_message",
            parameters={},
            dependencies=[step11.id]
        )
        workflow.steps[step12.id] = step12
        workflow.dependencies[step12.id] = [step11.id]
        
        # Step 13: Schedule meeting (optional)
        step13 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Schedule Meeting",
            description="Schedule discussion meeting",
            action="calendar_create_event",
            parameters={},
            dependencies=[step12.id]
        )
        workflow.steps[step13.id] = step13
        workflow.dependencies[step13.id] = [step12.id]
        
        return workflow
    
    def _create_create_workflow(
        self,
        workflow_id: str,
        user_request: str,
        intent: Dict[str, Any]
    ) -> Workflow:
        """Create workflow for creating something"""
        workflow = Workflow(
            id=workflow_id,
            name="Create Workflow",
            description="Create new resource based on request",
            user_request=user_request
        )
        
        # Step 1: Determine what to create
        step1 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Determine Resource Type",
            description="Analyze what needs to be created",
            action="analyze_request",
            parameters={"request": user_request}
        )
        workflow.steps[step1.id] = step1
        
        # Step 2: Create in primary service
        step2 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Create Resource",
            description="Create resource in primary service",
            action="create_resource",
            parameters={},
            dependencies=[step1.id]
        )
        workflow.steps[step2.id] = step2
        workflow.dependencies[step2.id] = [step1.id]
        
        # Step 3: Sync to other services
        step3 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Sync to Other Services",
            description="Create corresponding resources in other services",
            action="sync_resources",
            parameters={},
            dependencies=[step2.id]
        )
        workflow.steps[step3.id] = step3
        workflow.dependencies[step3.id] = [step2.id]
        
        return workflow
    
    def _create_deploy_workflow(
        self,
        workflow_id: str,
        user_request: str,
        intent: Dict[str, Any]
    ) -> Workflow:
        """Create workflow for deployment"""
        workflow = Workflow(
            id=workflow_id,
            name="Deploy Workflow",
            description="Deploy application to specified environment",
            user_request=user_request
        )
        
        # Step 1: Check current branch
        step1 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Check Branch",
            description="Verify current branch status",
            action="github_get_branch",
            parameters={}
        )
        workflow.steps[step1.id] = step1
        
        # Step 2: Run tests
        step2 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Run Tests",
            description="Run all tests before deployment",
            action="github_run_tests",
            parameters={},
            dependencies=[step1.id]
        )
        workflow.steps[step2.id] = step2
        workflow.dependencies[step2.id] = [step1.id]
        
        # Step 3: Build application
        step3 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Build Application",
            description="Build application artifacts",
            action="build_application",
            parameters={},
            dependencies=[step2.id]
        )
        workflow.steps[step3.id] = step3
        workflow.dependencies[step3.id] = [step2.id]
        
        # Step 4: Deploy
        step4 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Deploy",
            description="Deploy to target environment",
            action="deploy",
            parameters={"environment": "preview"},
            dependencies=[step3.id]
        )
        workflow.steps[step4.id] = step4
        workflow.dependencies[step4.id] = [step3.id]
        
        # Step 5: Verify
        step5 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Verify Deployment",
            description="Check deployment health and functionality",
            action="verify_deployment",
            parameters={},
            dependencies=[step4.id]
        )
        workflow.steps[step5.id] = step5
        workflow.dependencies[step5.id] = [step4.id]
        
        # Step 6: Notify
        step6 = WorkflowStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name="Notify Team",
            description="Send deployment notification",
            action="slack_send_message",
            parameters={},
            dependencies=[step5.id]
        )
        workflow.steps[step6.id] = step6
        workflow.dependencies[step6.id] = [step5.id]
        
        return workflow
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        auto_confirm: bool = False
    ) -> Workflow:
        """
        Execute a workflow step by step.
        
        Args:
            workflow: Workflow to execute
            auto_confirm: Whether to auto-confirm L2+ operations
            
        Returns:
            Workflow with updated status and results
        """
        workflow_id = workflow.id
        self.active_workflows[workflow_id] = workflow
        workflow.status = TaskStatus.IN_PROGRESS
        workflow.started_at = datetime.now(timezone.utc).isoformat()
        
        self.audit_logger.log(
            AuditEventType.EXECUTE,
            "Workflow execution started",
            {"workflow_id": workflow_id, "name": workflow.name}
        )
        
        try:
            # Get execution order
            execution_order = workflow.get_execution_order()
            
            for step_id in execution_order:
                step = workflow.steps[step_id]
                
                # Check if step is ready
                if step_id not in workflow.get_ready_steps():
                    continue
                
                workflow.current_step = step_id
                step.status = TaskStatus.IN_PROGRESS
                self._save_state()
                
                self.audit_logger.log(
                    AuditEventType.STEP_START,
                    "Step execution started",
                    {"workflow_id": workflow_id, "step_id": step_id, "step_name": step.name}
                )
                
                # Execute the step
                try:
                    # Check permissions
                    permission_level = self.security_manager.get_permission_level(step.action)
                    
                    if permission_level > PermissionLevel.L1:
                        if not auto_confirm:
                            # Need user confirmation
                            step.status = TaskStatus.WAITING_APPROVAL
                            self.audit_logger.log(
                                AuditEventType.APPROVAL_REQUIRED,
                                "Approval required for step",
                                {
                                    "workflow_id": workflow_id,
                                    "step_id": step_id,
                                    "action": step.action,
                                    "required_level": permission_level.name
                                }
                            )
                            continue
                    
                    # Execute through integration or adapter
                    result = await self._execute_step(step, workflow)
                    
                    step.status = TaskStatus.COMPLETED
                    step.result = result
                    workflow.results[step_id] = result
                    
                    self.audit_logger.log(
                        AuditEventType.STEP_COMPLETE,
                        "Step completed successfully",
                        {
                            "workflow_id": workflow_id,
                            "step_id": step_id,
                            "result": result
                        }
                    )
                    
                except Exception as e:
                    step.error = str(e)
                    step.retries += 1
                    
                    if step.retries >= step.max_retries:
                        step.status = TaskStatus.FAILED
                        workflow.errors.append(f"Step {step_id} failed: {str(e)}")
                        
                        self.audit_logger.log(
                            AuditEventType.ERROR,
                            "Step failed",
                            {
                                "workflow_id": workflow_id,
                                "step_id": step_id,
                                "error": str(e),
                                "retries": step.retries
                            },
                            severity="high"
                        )
                    else:
                        step.status = TaskStatus.PENDING
                        self.audit_logger.log(
                            AuditEventType.RETRY,
                            "Step will be retried",
                            {
                                "workflow_id": workflow_id,
                                "step_id": step_id,
                                "retries": step.retries,
                                "max_retries": step.max_retries
                            }
                        )
                
                self._save_state()
            
            # Check if workflow is complete
            if all(
                step.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
                for step in workflow.steps.values()
            ):
                workflow.status = TaskStatus.COMPLETED
                workflow.completed_at = datetime.now(timezone.utc).isoformat()
                
                self.audit_logger.log(
                    AuditEventType.COMPLETE,
                    "Workflow completed",
                    {
                        "workflow_id": workflow_id,
                        "status": workflow.status.name,
                        "duration": f"{(workflow.completed_at - workflow.started_at) if workflow.completed_at and workflow.started_at else 'N/A'}"
                    }
                )
            
        except Exception as e:
            workflow.status = TaskStatus.FAILED
            workflow.errors.append(f"Workflow execution failed: {str(e)}")
            
            self.audit_logger.log(
                AuditEventType.ERROR,
                "Workflow execution failed",
                {
                    "workflow_id": workflow_id,
                    "error": str(e)
                },
                severity="critical"
            )
        
        self._save_state()
        return workflow
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        workflow: Workflow
    ) -> Dict[str, Any]:
        """Execute a single workflow step"""
        # Route to appropriate integration or adapter
        if step.action.startswith("github_"):
            if self.integration_registry and "github" in self.integration_registry.integrations:
                return await self.integration_registry.execute("github", step.action, step.parameters)
        elif step.action.startswith("asana_"):
            if self.integration_registry and "asana" in self.integration_registry.integrations:
                return await self.integration_registry.execute("asana", step.action, step.parameters)
        elif step.action.startswith("slack_"):
            if self.integration_registry and "slack" in self.integration_registry.integrations:
                return await self.integration_registry.execute("slack", step.action, step.parameters)
        elif step.action.startswith("calendar_"):
            if self.integration_registry and ("google_calendar" in self.integration_registry.integrations or 
                   "outlook_calendar" in self.integration_registry.integrations):
                return await self.integration_registry.execute("calendar", step.action, step.parameters)
        elif step.action.startswith("netlify_"):
            if self.integration_registry and "netlify" in self.integration_registry.integrations:
                return await self.integration_registry.execute("netlify", step.action, step.parameters)
        elif step.action.startswith("uaw_"):
            # Internal UAW operations
            if step.action == "uaw_link_resources":
                return await self._link_resources(step.parameters)
        
        # Try adapters for unavailable integrations
        if self.adapter_registry:
            adapter_name = step.action.split("_")[0]
            if adapter_name in self.adapter_registry.adapters:
                return await self.adapter_registry.execute(adapter_name, step.action, step.parameters)
        
        raise ValueError(f"No integration or adapter found for action: {step.action}")
    
    async def _link_resources(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Link resources across different services"""
        # This would be implemented based on the resource mapping
        return {
            "status": "linked",
            "message": "Resources linked successfully",
            "mapping_id": f"link_{uuid.uuid4().hex[:12]}"
        }
    
    async def resume_workflow(self, workflow_id: str) -> Workflow:
        """Resume a paused or failed workflow"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.active_workflows[workflow_id]
        
        self.audit_logger.log(
            AuditEventType.RESUME,
            "Resuming workflow",
            {"workflow_id": workflow_id}
        )
        
        return await self.execute_workflow(workflow)
    
    async def cancel_workflow(self, workflow_id: str) -> Workflow:
        """Cancel an active workflow"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.active_workflows[workflow_id]
        workflow.status = TaskStatus.CANCELLED
        workflow.completed_at = datetime.now(timezone.utc).isoformat()
        
        for step in workflow.steps.values():
            if step.status == TaskStatus.IN_PROGRESS:
                step.status = TaskStatus.CANCELLED
        
        self.audit_logger.log(
            AuditEventType.CANCEL,
            "Workflow cancelled",
            {"workflow_id": workflow_id}
        )
        
        self._save_state()
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID"""
        return self.active_workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Workflow]:
        """List all active workflows"""
        return list(self.active_workflows.values())
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall UAW system status"""
        return {
            "active_workflows": len(self.active_workflows),
            "completed_workflows": len([
                wf for wf in self.active_workflows.values()
                if wf.status == TaskStatus.COMPLETED
            ]),
            "failed_workflows": len([
                wf for wf in self.active_workflows.values()
                if wf.status == TaskStatus.FAILED
            ]),
            "pending_workflows": len([
                wf for wf in self.active_workflows.values()
                if wf.status == TaskStatus.PENDING
            ]),
            "integrations": {
                name: status.value for name, status in 
                (self.integration_registry.get_status() if self.integration_registry else {}).items()
            } if self.integration_registry else {}
        }
