"""
Workflow Model for UAW
Модель сценария, его этапов, условий, зависимостей и состояния
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

from .base import BaseModel, EntityType, UAWIdentifier


class WorkflowStatus(Enum):
    """Status of a workflow"""
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowTriggerType(Enum):
    """Type of workflow trigger"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    EVENT = "event"
    CONDITION = "condition"


class StepStatus(Enum):
    """Status of a workflow step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowCondition:
    """Workflow condition"""
    type: str  # field, expression, script
    field: Optional[str] = None
    operator: Optional[str] = None  # eq, neq, gt, gte, lt, lte, in, not_in, contains
    value: Any = None
    expression: Optional[str] = None
    script: Optional[str] = None
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context"""
        if self.type == "field" and self.field:
            field_value = context.get(self.field)
            if self.operator == "eq":
                return field_value == self.value
            elif self.operator == "neq":
                return field_value != self.value
            elif self.operator == "gt":
                return field_value > self.value
            elif self.operator == "gte":
                return field_value >= self.value
            elif self.operator == "lt":
                return field_value < self.value
            elif self.operator == "lte":
                return field_value <= self.value
            elif self.operator == "in":
                return field_value in self.value
            elif self.operator == "not_in":
                return field_value not in self.value
            elif self.operator == "contains":
                return isinstance(field_value, str) and self.value in field_value
        elif self.type == "expression" and self.expression:
            # Simple expression evaluation
            try:
                return eval(self.expression, {}, context)
            except:
                return False
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
            "expression": self.expression,
            "script": self.script
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowCondition":
        return cls(
            type=data.get("type", "field"),
            field=data.get("field"),
            operator=data.get("operator"),
            value=data.get("value"),
            expression=data.get("expression"),
            script=data.get("script")
        )


@dataclass
class WorkflowAction:
    """Workflow action"""
    type: str  # tool, integration, adapter, script
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    integration: Optional[str] = None
    adapter: Optional[str] = None
    tool: Optional[str] = None
    script: Optional[str] = None
    timeout_seconds: int = 300
    retry_count: int = 0
    retry_delay: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "name": self.name,
            "parameters": self.parameters,
            "integration": self.integration,
            "adapter": self.adapter,
            "tool": self.tool,
            "script": self.script,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowAction":
        return cls(
            type=data.get("type", "tool"),
            name=data.get("name", ""),
            parameters=data.get("parameters", {}),
            integration=data.get("integration"),
            adapter=data.get("adapter"),
            tool=data.get("tool"),
            script=data.get("script"),
            timeout_seconds=data.get("timeout_seconds", 300),
            retry_count=data.get("retry_count", 0),
            retry_delay=data.get("retry_delay", 5)
        )


@dataclass
class WorkflowStep:
    """Workflow step"""
    step_id: str
    name: str
    description: Optional[str] = None
    step_type: str = "action"  # action, condition, wait, parallel, loop
    
    # For action steps
    action: Optional[WorkflowAction] = None
    
    # For condition steps
    condition: Optional[WorkflowCondition] = None
    true_step: Optional[str] = None
    false_step: Optional[str] = None
    
    # For wait steps
    wait_seconds: Optional[int] = None
    wait_until: Optional[str] = None
    
    # For parallel steps
    parallel_steps: List[str] = field(default_factory=list)
    
    # For loop steps
    loop_items: Optional[str] = None  # Context key for items
    loop_step: Optional[str] = None
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    
    # Execution
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    attempts: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "step_type": self.step_type,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "attempts": self.attempts
        }
        
        if self.action:
            result["action"] = self.action.to_dict()
        if self.condition:
            result["condition"] = self.condition.to_dict()
        if self.true_step:
            result["true_step"] = self.true_step
        if self.false_step:
            result["false_step"] = self.false_step
        if self.wait_seconds is not None:
            result["wait_seconds"] = self.wait_seconds
        if self.wait_until:
            result["wait_until"] = self.wait_until
        if self.parallel_steps:
            result["parallel_steps"] = self.parallel_steps
        if self.loop_items:
            result["loop_items"] = self.loop_items
        if self.loop_step:
            result["loop_step"] = self.loop_step
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStep":
        action = None
        if data.get("action"):
            action = WorkflowAction.from_dict(data["action"])
        
        condition = None
        if data.get("condition"):
            condition = WorkflowCondition.from_dict(data["condition"])
        
        return cls(
            step_id=data.get("step_id", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            step_type=data.get("step_type", "action"),
            action=action,
            condition=condition,
            true_step=data.get("true_step"),
            false_step=data.get("false_step"),
            wait_seconds=data.get("wait_seconds"),
            wait_until=data.get("wait_until"),
            parallel_steps=data.get("parallel_steps", []),
            loop_items=data.get("loop_items"),
            loop_step=data.get("loop_step"),
            dependencies=data.get("dependencies", []),
            status=StepStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            attempts=data.get("attempts", 0)
        )


@dataclass
class WorkflowTrigger:
    """Workflow trigger"""
    trigger_id: str
    name: str
    trigger_type: WorkflowTriggerType = WorkflowTriggerType.MANUAL
    
    # For scheduled triggers
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    
    # For webhook triggers
    webhook_url: Optional[str] = None
    webhook_events: List[str] = field(default_factory=list)
    
    # For event triggers
    event_source: Optional[str] = None
    event_types: List[str] = field(default_factory=list)
    
    # Filter conditions
    conditions: List[WorkflowCondition] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_id": self.trigger_id,
            "name": self.name,
            "trigger_type": self.trigger_type.value,
            "cron_expression": self.cron_expression,
            "interval_seconds": self.interval_seconds,
            "webhook_url": self.webhook_url,
            "webhook_events": self.webhook_events,
            "event_source": self.event_source,
            "event_types": self.event_types,
            "conditions": [c.to_dict() for c in self.conditions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowTrigger":
        conditions = []
        for c_data in data.get("conditions", []):
            conditions.append(WorkflowCondition.from_dict(c_data))
        
        return cls(
            trigger_id=data.get("trigger_id", ""),
            name=data.get("name", ""),
            trigger_type=WorkflowTriggerType(data.get("trigger_type", "manual")),
            cron_expression=data.get("cron_expression"),
            interval_seconds=data.get("interval_seconds"),
            webhook_url=data.get("webhook_url"),
            webhook_events=data.get("webhook_events", []),
            event_source=data.get("event_source"),
            event_types=data.get("event_types", []),
            conditions=conditions
        )


@dataclass
class Workflow(BaseModel):
    """
    Workflow model representing a scenario with steps, conditions, dependencies, and state.
    
    Attributes:
        uaw_id: Unique UAW identifier
        name: Workflow name
        description: Workflow description
        status: Current workflow status
        version: Workflow version
        trigger: Workflow trigger
        steps: List of workflow steps
        variables: Workflow variables
        entry_step: Entry step ID
        current_step: Current step ID
        completed_steps: List of completed step IDs
        failed_steps: List of failed step IDs
        context: Current execution context
        created_by: UAW ID of workflow creator
        approved_by: List of UAW IDs of people who approved
        approval_required: Whether approval is required
        max_retries: Maximum number of retries
        timeout_minutes: Maximum execution time in minutes
        external_ids: IDs in external systems
        custom_fields: Custom workflow fields
    """
    
    entity_type: ClassVar[EntityType] = EntityType.WORKFLOW
    
    version: str = "1.0"
    status: WorkflowStatus = WorkflowStatus.DRAFT
    
    trigger: Optional[WorkflowTrigger] = None
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    
    variables: Dict[str, Any] = field(default_factory=dict)
    entry_step: Optional[str] = None
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    
    context: Dict[str, Any] = field(default_factory=dict)
    
    created_by: Optional[str] = None
    approved_by: List[str] = field(default_factory=list)
    approval_required: bool = False
    
    max_retries: int = 3
    timeout_minutes: int = 60
    
    # External system IDs
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.steps, list):
            self.steps = {s.step_id: s for s in self.steps}
        if isinstance(self.completed_steps, str):
            self.completed_steps = [self.completed_steps]
        if isinstance(self.failed_steps, str):
            self.failed_steps = [self.failed_steps]
        if isinstance(self.approved_by, str):
            self.approved_by = [self.approved_by]
        if isinstance(self.trigger, dict):
            self.trigger = WorkflowTrigger.from_dict(self.trigger)
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow"""
        self.steps[step.step_id] = step
        if self.entry_step is None:
            self.entry_step = step.step_id
    
    def remove_step(self, step_id: str) -> bool:
        """Remove a step from the workflow"""
        if step_id in self.steps:
            del self.steps[step_id]
            if self.entry_step == step_id:
                self.entry_step = None
            if self.current_step == step_id:
                self.current_step = None
            return True
        return False
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID"""
        return self.steps.get(step_id)
    
    def add_external_id(self, system: str, external_id: str) -> None:
        """Add an external system ID"""
        self.external_ids[system] = external_id
    
    def get_external_id(self, system: str) -> Optional[str]:
        """Get external ID for a system"""
        return self.external_ids.get(system)
    
    def set_variable(self, key: str, value: Any) -> None:
        """Set a workflow variable"""
        self.variables[key] = value
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a workflow variable"""
        return self.variables.get(key, default)
    
    def set_context(self, key: str, value: Any) -> None:
        """Set a context value"""
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value"""
        return self.context.get(key, default)
    
    def set_status(self, status: WorkflowStatus) -> None:
        """Set workflow status"""
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def add_approval(self, person_id: str) -> None:
        """Add an approval"""
        if person_id not in self.approved_by:
            self.approved_by.append(person_id)
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field"""
        self.custom_fields[key] = value
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field"""
        return self.custom_fields.get(key, default)
    
    def is_running(self) -> bool:
        """Check if workflow is running"""
        return self.status == WorkflowStatus.RUNNING
    
    def is_completed(self) -> bool:
        """Check if workflow is completed"""
        return self.status == WorkflowStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if workflow failed"""
        return self.status == WorkflowStatus.FAILED
    
    def has_all_steps_completed(self) -> bool:
        """Check if all steps are completed"""
        return len(self.completed_steps) == len(self.steps)
    
    def has_failures(self) -> bool:
        """Check if workflow has failures"""
        return len(self.failed_steps) > 0
    
    def get_next_step(self) -> Optional[str]:
        """Get the next step to execute"""
        if self.current_step:
            current = self.steps.get(self.current_step)
            if current:
                # Check if current step has dependencies
                if current.dependencies:
                    # Find first dependency that is not completed
                    for dep in current.dependencies:
                        if dep not in self.completed_steps:
                            return dep
                
                # Check step type
                if current.step_type == "condition" and current.condition:
                    # Evaluate condition
                    if current.condition.evaluate(self.context):
                        return current.true_step
                    else:
                        return current.false_step
                
                if current.step_type == "parallel":
                    # Return first incomplete parallel step
                    for ps in current.parallel_steps:
                        if ps not in self.completed_steps:
                            return ps
        
        # Return entry step if nothing else
        return self.entry_step
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        result.update({
            "version": self.version,
            "status": self.status.value,
            "trigger": self.trigger.to_dict() if self.trigger else None,
            "steps": {k: v.to_dict() for k, v in self.steps.items()},
            "variables": self.variables,
            "entry_step": self.entry_step,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "context": self.context,
            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "approval_required": self.approval_required,
            "max_retries": self.max_retries,
            "timeout_minutes": self.timeout_minutes,
            "external_ids": self.external_ids,
            "custom_fields": self.custom_fields
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Create from dictionary"""
        uaw_id = data.get("uaw_id")
        if isinstance(uaw_id, str):
            uaw_id = UAWIdentifier.from_string(uaw_id)
        
        # Parse steps
        steps = {}
        for step_id, step_data in data.get("steps", {}).items():
            steps[step_id] = WorkflowStep.from_dict(step_data)
        
        # Parse trigger
        trigger = None
        if data.get("trigger"):
            trigger = WorkflowTrigger.from_dict(data["trigger"])
        
        return cls(
            uaw_id=uaw_id,
            name=data.get("name", ""),
            description=data.get("description"),
            version=data.get("version", "1.0"),
            status=WorkflowStatus(data.get("status", "draft")),
            trigger=trigger,
            steps=steps,
            variables=data.get("variables", {}),
            entry_step=data.get("entry_step"),
            current_step=data.get("current_step"),
            completed_steps=data.get("completed_steps", []),
            failed_steps=data.get("failed_steps", []),
            context=data.get("context", {}),
            created_by=data.get("created_by"),
            approved_by=data.get("approved_by", []),
            approval_required=data.get("approval_required", False),
            max_retries=data.get("max_retries", 3),
            timeout_minutes=data.get("timeout_minutes", 60),
            external_ids=data.get("external_ids", {}),
            custom_fields=data.get("custom_fields", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            is_active=data.get("is_active", True)
        )


@dataclass
class WorkflowBuilder:
    """Builder for creating Workflow instances"""
    
    name: str
    
    def with_description(self, description: str) -> "WorkflowBuilder":
        """Set description"""
        self._description = description
        return self
    
    def with_version(self, version: str) -> "WorkflowBuilder":
        """Set version"""
        self._version = version
        return self
    
    def with_trigger(self, trigger: WorkflowTrigger) -> "WorkflowBuilder":
        """Set trigger"""
        self._trigger = trigger
        return self
    
    def with_entry_step(self, step_id: str) -> "WorkflowBuilder":
        """Set entry step"""
        self._entry_step = step_id
        return self
    
    def with_variable(self, key: str, value: Any) -> "WorkflowBuilder":
        """Add variable"""
        self._variables = getattr(self, "_variables", {})
        self._variables[key] = value
        return self
    
    def with_external_id(self, system: str, external_id: str) -> "WorkflowBuilder":
        """Add external ID"""
        self._external_ids = getattr(self, "_external_ids", {})
        self._external_ids[system] = external_id
        return self
    
    def build(self) -> Workflow:
        """Build Workflow instance"""
        return Workflow(
            uaw_id=Workflow.generate_id(),
            name=self.name,
            description=getattr(self, "_description", None),
            version=getattr(self, "_version", "1.0"),
            trigger=getattr(self, "_trigger", None),
            entry_step=getattr(self, "_entry_step", None),
            variables=getattr(self, "_variables", {}),
            external_ids=getattr(self, "_external_ids", {})
        )
