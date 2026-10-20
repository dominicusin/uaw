"""
Workflow Engine for UAW
Движок рабочих процессов для Unified Agentic Workspace
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Tuple, Union
from enum import Enum
import uuid
import hashlib

from ..models.workflow import (
    Workflow, WorkflowBuilder, WorkflowStatus, WorkflowTriggerType,
    WorkflowStep, StepStatus, WorkflowCondition, WorkflowAction
)
from ..models.base import UAWIdentifier, EntityType
from ..core.state_manager import StateManager
from ..core.audit import AuditLogger


class ExecutionMode(Enum):
    """Execution mode for workflows"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    SMART = "smart"


class WorkflowPriority(Enum):
    """Priority of workflow execution"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ExecutionContext:
    """
    Context for workflow execution.
    Contains runtime data and state.
    """
    workflow_id: str
    execution_id: str
    current_step_id: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    completed_steps: Set[str] = field(default_factory=set)
    failed_steps: Set[str] = field(default_factory=set)
    pending_steps: Set[str] = field(default_factory=set)
    running_steps: Set[str] = field(default_factory=set)
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_activity_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def update_last_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity_at = datetime.now(timezone.utc).isoformat()
    
    def mark_step_started(self, step_id: str) -> None:
        """Mark a step as started"""
        self.running_steps.add(step_id)
        self.pending_steps.discard(step_id)
        self.current_step_id = step_id
        self.update_last_activity()
    
    def mark_step_completed(self, step_id: str, result: Any = None) -> None:
        """Mark a step as completed"""
        self.running_steps.discard(step_id)
        self.completed_steps.add(step_id)
        if result:
            self.results[step_id] = result
        self.update_last_activity()
    
    def mark_step_failed(self, step_id: str, error: str) -> None:
        """Mark a step as failed"""
        self.running_steps.discard(step_id)
        self.failed_steps.add(step_id)
        self.errors[step_id] = error
        self.update_last_activity()
    
    def is_step_completed(self, step_id: str) -> bool:
        """Check if a step is completed"""
        return step_id in self.completed_steps
    
    def is_step_failed(self, step_id: str) -> bool:
        """Check if a step is failed"""
        return step_id in self.failed_steps
    
    def is_step_running(self, step_id: str) -> bool:
        """Check if a step is running"""
        return step_id in self.running_steps
    
    def is_step_pending(self, step_id: str) -> bool:
        """Check if a step is pending"""
        return step_id in self.pending_steps
    
    def get_step_status(self, step_id: str) -> str:
        """Get status of a step"""
        if step_id in self.completed_steps:
            return "completed"
        elif step_id in self.failed_steps:
            return "failed"
        elif step_id in self.running_steps:
            return "running"
        elif step_id in self.pending_steps:
            return "pending"
        return "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "current_step_id": self.current_step_id,
            "variables": self.variables,
            "results": self.results,
            "errors": self.errors,
            "completed_steps": list(self.completed_steps),
            "failed_steps": list(self.failed_steps),
            "pending_steps": list(self.pending_steps),
            "running_steps": list(self.running_steps),
            "started_at": self.started_at,
            "last_activity_at": self.last_activity_at
        }


@dataclass
class DependencyGraph:
    """
    Dependency graph for workflow steps.
    Manages dependencies between steps.
    """
    workflow_id: str
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    adjacency_list: Dict[str, List[str]] = field(default_factory=dict)
    reverse_adjacency_list: Dict[str, List[str]] = field(default_factory=dict)
    in_degree: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize after creation"""
        self._build_graph()
    
    def _build_graph(self) -> None:
        """Build the dependency graph"""
        # Reset graph structures
        self.adjacency_list = {}
        self.reverse_adjacency_list = {}
        self.in_degree = {}
        
        # Initialize all steps
        for step_id, step in self.steps.items():
            self.adjacency_list[step_id] = []
            self.reverse_adjacency_list[step_id] = []
            self.in_degree[step_id] = 0
        
        # Build edges based on dependencies
        for step_id, step in self.steps.items():
            for dep_id in step.dependencies:
                if dep_id in self.steps:
                    self.adjacency_list[dep_id].append(step_id)
                    self.reverse_adjacency_list[step_id].append(dep_id)
                    self.in_degree[step_id] = self.in_degree.get(step_id, 0) + 1
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the graph"""
        self.steps[step.step_id] = step
        self._build_graph()
    
    def remove_step(self, step_id: str) -> bool:
        """Remove a step from the graph"""
        if step_id in self.steps:
            del self.steps[step_id]
            self._build_graph()
            return True
        return False
    
    def get_dependencies(self, step_id: str) -> List[str]:
        """Get dependencies for a step"""
        step = self.steps.get(step_id)
        if step:
            return step.dependencies
        return []
    
    def get_dependents(self, step_id: str) -> List[str]:
        """Get steps that depend on this step"""
        return self.adjacency_list.get(step_id, [])
    
    def get_roots(self) -> List[str]:
        """Get root steps (no dependencies)"""
        return [step_id for step_id, degree in self.in_degree.items() if degree == 0]
    
    def get_leaves(self) -> List[str]:
        """Get leaf steps (no dependents)"""
        return [step_id for step_id, deps in self.adjacency_list.items() if len(deps) == 0]
    
    def topological_sort(self) -> List[str]:
        """
        Perform topological sort on the graph.
        Returns steps in execution order.
        """
        # Kahn's algorithm
        in_degree = self.in_degree.copy()
        result = []
        queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
        
        while queue:
            # Sort queue by step order if available
            queue.sort()
            
            step_id = queue.pop(0)
            result.append(step_id)
            
            for dependent in self.adjacency_list.get(step_id, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check for cycles
        if len(result) != len(self.steps):
            raise ValueError("Graph contains cycles, cannot perform topological sort")
        
        return result
    
    def get_execution_order(self, entry_step: Optional[str] = None) -> List[str]:
        """
        Get execution order starting from entry step.
        Respects dependencies.
        """
        if entry_step and entry_step in self.steps:
            # Find all steps reachable from entry step
            reachable = self._find_reachable(entry_step)
            
            # Create subgraph with only reachable steps
            subgraph_steps = {sid: self.steps[sid] for sid in reachable}
            subgraph = DependencyGraph(
                workflow_id=self.workflow_id,
                steps=subgraph_steps
            )
            
            return subgraph.topological_sort()
        
        return self.topological_sort()
    
    def _find_reachable(self, start_step_id: str) -> Set[str]:
        """Find all steps reachable from start step"""
        visited = set()
        queue = [start_step_id]
        
        while queue:
            step_id = queue.pop(0)
            if step_id in visited:
                continue
            
            visited.add(step_id)
            
            # Add dependencies
            for dep_id in self.steps.get(step_id, WorkflowStep(step_id, "")).dependencies:
                if dep_id in self.steps and dep_id not in visited:
                    queue.append(dep_id)
            
            # Add dependents
            for dep_id in self.adjacency_list.get(step_id, []):
                if dep_id in self.steps and dep_id not in visited:
                    queue.append(dep_id)
        
        return visited
    
    def has_cycles(self) -> bool:
        """Check if graph has cycles"""
        try:
            self.topological_sort()
            return False
        except ValueError:
            return True
    
    def get_cycle(self) -> Optional[List[str]]:
        """Find a cycle in the graph if one exists"""
        # DFS-based cycle detection
        visited = set()
        recursion_stack = set()
        parent = {}
        
        def dfs(node: str) -> Optional[List[str]]:
            visited.add(node)
            recursion_stack.add(node)
            
            for neighbor in self.adjacency_list.get(node, []):
                if neighbor not in visited:
                    parent[neighbor] = node
                    result = dfs(neighbor)
                    if result:
                        return result
                elif neighbor in recursion_stack:
                    # Found cycle
                    cycle = [neighbor, node]
                    current = node
                    while parent.get(current) != neighbor:
                        current = parent[current]
                        cycle.append(current)
                    cycle.append(neighbor)
                    return cycle[::-1]
            
            recursion_stack.discard(node)
            return None
        
        for step_id in self.steps:
            if step_id not in visited:
                result = dfs(step_id)
                if result:
                    return result
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "steps": {k: v.to_dict() for k, v in self.steps.items()},
            "adjacency_list": self.adjacency_list,
            "reverse_adjacency_list": self.reverse_adjacency_list,
            "in_degree": self.in_degree
        }


@dataclass
class TaskQueue:
    """
    Task queue for workflow execution.
    Manages pending, running, and completed tasks.
    """
    max_workers: int = 10
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    running_tasks: Dict[str, asyncio.Task] = field(default_factory=dict)
    completed_tasks: Dict[str, Any] = field(default_factory=dict)
    failed_tasks: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize after creation"""
        if not isinstance(self.queue, asyncio.Queue):
            self.queue = asyncio.Queue()
    
    async def enqueue(self, task_id: str, coroutine: Coroutine) -> None:
        """Add a task to the queue"""
        await self.queue.put((task_id, coroutine))
    
    async def dequeue(self) -> Tuple[str, Coroutine]:
        """Get next task from queue"""
        return await self.queue.get()
    
    async def execute_task(self, task_id: str, coroutine: Coroutine) -> Any:
        """Execute a task"""
        try:
            result = await coroutine
            self.completed_tasks[task_id] = result
            return result
        except Exception as e:
            self.failed_tasks[task_id] = str(e)
            raise
    
    async def worker(self) -> None:
        """Worker that processes tasks from queue"""
        while True:
            task_id, coroutine = await self.dequeue()
            
            # Create task
            task = asyncio.create_task(self.execute_task(task_id, coroutine))
            self.running_tasks[task_id] = task
            
            # Wait for task completion
            try:
                await task
            except Exception:
                pass
            finally:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
    
    async def start_workers(self, num_workers: Optional[int] = None) -> List[asyncio.Task]:
        """Start worker tasks"""
        num = num_workers or self.max_workers
        workers = []
        
        for _ in range(num):
            worker = asyncio.create_task(self.worker())
            workers.append(worker)
        
        return workers
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return self.queue.empty()
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()
    
    def get_running_count(self) -> int:
        """Get number of running tasks"""
        return len(self.running_tasks)
    
    def is_task_running(self, task_id: str) -> bool:
        """Check if a task is running"""
        return task_id in self.running_tasks
    
    def is_task_completed(self, task_id: str) -> bool:
        """Check if a task is completed"""
        return task_id in self.completed_tasks
    
    def is_task_failed(self, task_id: str) -> bool:
        """Check if a task failed"""
        return task_id in self.failed_tasks
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get result of a completed task"""
        return self.completed_tasks.get(task_id)
    
    def get_task_error(self, task_id: str) -> Optional[str]:
        """Get error of a failed task"""
        return self.failed_tasks.get(task_id)


class WorkflowEngine:
    """
    Workflow engine for UAW.
    Executes workflows with dependency management, retries, and state persistence.
    """
    
    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        audit_logger: Optional[AuditLogger] = None,
        max_workers: int = 10
    ):
        self.state_manager = state_manager or StateManager()
        self.audit_logger = audit_logger or AuditLogger()
        self.max_workers = max_workers
        
        # Active workflows
        self.active_workflows: Dict[str, Workflow] = {}
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.active_dependency_graphs: Dict[str, DependencyGraph] = {}
        
        # Task queue
        self.task_queue = TaskQueue(max_workers=max_workers)
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {}
        
        # Statistics
        self.total_executions = 0
        self.completed_executions = 0
        self.failed_executions = 0
    
    async def initialize(self) -> bool:
        """Initialize the workflow engine"""
        # Start task queue workers
        self.workers = await self.task_queue.start_workers(self.max_workers)
        return True
    
    async def shutdown(self) -> None:
        """Shutdown the workflow engine"""
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        mode: ExecutionMode = ExecutionMode.SMART,
        priority: WorkflowPriority = WorkflowPriority.NORMAL,
        variables: Optional[Dict[str, Any]] = None
    ) -> Workflow:
        """
        Execute a workflow.
        
        Args:
            workflow: Workflow to execute
            mode: Execution mode (sequential, parallel, smart)
            priority: Workflow priority
            variables: Initial variables
            
        Returns:
            Executed workflow with updated state
        """
        # Generate execution ID
        execution_id = str(uuid.uuid4())
        
        # Create execution context
        context = ExecutionContext(
            workflow_id=workflow.uaw_id.entity_id,
            execution_id=execution_id,
            variables=variables or {}
        )
        
        # Update workflow status
        workflow.set_status(WorkflowStatus.RUNNING)
        workflow.current_step = workflow.entry_step
        
        # Store active workflow
        self.active_workflows[workflow.uaw_id.entity_id] = workflow
        self.active_executions[workflow.uaw_id.entity_id] = context
        
        # Build dependency graph
        dependency_graph = DependencyGraph(
            workflow_id=workflow.uaw_id.entity_id,
            steps=workflow.steps
        )
        self.active_dependency_graphs[workflow.uaw_id.entity_id] = dependency_graph
        
        # Log start
        await self.audit_logger.log_workflow_start(workflow, context)
        
        try:
            # Get execution order
            execution_order = dependency_graph.get_execution_order(workflow.entry_step)
            
            # Execute based on mode
            if mode == ExecutionMode.SEQUENTIAL:
                await self._execute_sequential(workflow, execution_order, context)
            elif mode == ExecutionMode.PARALLEL:
                await self._execute_parallel(workflow, execution_order, context)
            else:  # SMART
                await self._execute_smart(workflow, execution_order, context)
            
            # Check for failures
            if context.failed_steps:
                workflow.set_status(WorkflowStatus.FAILED)
                self.failed_executions += 1
            else:
                workflow.set_status(WorkflowStatus.COMPLETED)
                self.completed_executions += 1
            
            self.total_executions += 1
            
            # Log completion
            await self.audit_logger.log_workflow_complete(workflow, context)
            
            # Trigger callbacks
            await self._trigger_callbacks("workflow_complete", workflow, context)
            
        except Exception as e:
            workflow.set_status(WorkflowStatus.FAILED)
            workflow.set_context("error", str(e))
            self.failed_executions += 1
            self.total_executions += 1
            
            # Log failure
            await self.audit_logger.log_workflow_failure(workflow, context, str(e))
            
            # Trigger callbacks
            await self._trigger_callbacks("workflow_failed", workflow, context)
        
        # Clean up
        if workflow.uaw_id.entity_id in self.active_workflows:
            del self.active_workflows[workflow.uaw_id.entity_id]
        if workflow.uaw_id.entity_id in self.active_executions:
            del self.active_executions[workflow.uaw_id.entity_id]
        if workflow.uaw_id.entity_id in self.active_dependency_graphs:
            del self.active_dependency_graphs[workflow.uaw_id.entity_id]
        
        return workflow
    
    async def _execute_sequential(
        self,
        workflow: Workflow,
        execution_order: List[str],
        context: ExecutionContext
    ) -> None:
        """Execute workflow steps sequentially"""
        for step_id in execution_order:
            step = workflow.steps.get(step_id)
            if not step:
                continue
            
            # Check if step can be executed
            if not self._can_execute_step(step, context):
                context.mark_step_failed(step_id, "Dependencies not met")
                continue
            
            # Execute step
            await self._execute_step(workflow, step, context)
            
            # Check for failures
            if step_id in context.failed_steps:
                # Stop execution on failure in sequential mode
                break
    
    async def _execute_parallel(
        self,
        workflow: Workflow,
        execution_order: List[str],
        context: ExecutionContext
    ) -> None:
        """Execute workflow steps in parallel where possible"""
        # Group steps by dependency level
        levels = self._group_by_dependency_level(workflow, execution_order)
        
        for level in levels:
            # Execute all steps in this level in parallel
            tasks = []
            for step_id in level:
                step = workflow.steps.get(step_id)
                if step and self._can_execute_step(step, context):
                    task = asyncio.create_task(
                        self._execute_step(workflow, step, context)
                    )
                    tasks.append(task)
            
            # Wait for all tasks in this level to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_smart(
        self,
        workflow: Workflow,
        execution_order: List[str],
        context: ExecutionContext
    ) -> None:
        """Execute workflow steps intelligently (parallel where safe)"""
        # Use task queue for smart execution
        
        # Initialize all steps as pending
        for step_id in execution_order:
            context.pending_steps.add(step_id)
        
        # Queue initial steps (no dependencies or dependencies met)
        for step_id in execution_order:
            step = workflow.steps.get(step_id)
            if step and self._can_execute_step(step, context):
                await self._queue_step(workflow, step, context)
        
        # Wait for all steps to complete
        while context.pending_steps or context.running_steps:
            await asyncio.sleep(0.1)
    
    def _group_by_dependency_level(
        self,
        workflow: Workflow,
        execution_order: List[str]
    ) -> List[List[str]]:
        """Group steps by dependency level"""
        levels = []
        level_map = {}
        
        for step_id in execution_order:
            step = workflow.steps.get(step_id)
            if not step:
                continue
            
            # Calculate level (longest path from entry step)
            level = self._calculate_dependency_level(workflow, step_id, {})
            level_map[step_id] = level
        
        # Group by level
        max_level = max(level_map.values()) if level_map else 0
        for i in range(max_level + 1):
            levels.append([
                step_id for step_id, level in level_map.items() if level == i
            ])
        
        return levels
    
    def _calculate_dependency_level(
        self,
        workflow: Workflow,
        step_id: str,
        visited: Set[str]
    ) -> int:
        """Calculate dependency level for a step"""
        if step_id in visited:
            return 0  # Avoid infinite recursion
        
        visited.add(step_id)
        
        step = workflow.steps.get(step_id)
        if not step or not step.dependencies:
            return 0
        
        max_level = 0
        for dep_id in step.dependencies:
            if dep_id in workflow.steps:
                level = self._calculate_dependency_level(workflow, dep_id, visited.copy())
                max_level = max(max_level, level + 1)
        
        return max_level
    
    def _can_execute_step(self, step: WorkflowStep, context: ExecutionContext) -> bool:
        """Check if a step can be executed"""
        # Check if step is already completed or failed
        if step.step_id in context.completed_steps or step.step_id in context.failed_steps:
            return False
        
        # Check if step is running
        if step.step_id in context.running_steps:
            return False
        
        # Check dependencies
        for dep_id in step.dependencies:
            if dep_id not in context.completed_steps:
                return False
        
        # Check condition if present
        if step.condition:
            if not step.condition.evaluate(context.variables):
                return False
        
        return True
    
    async def _queue_step(
        self,
        workflow: Workflow,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> None:
        """Queue a step for execution"""
        if not self._can_execute_step(step, context):
            return
        
        # Mark as started
        context.mark_step_started(step.step_id)
        
        # Create coroutine for step execution
        coroutine = self._execute_step(workflow, step, context)
        
        # Queue the step
        await self.task_queue.enqueue(step.step_id, coroutine)
    
    async def _execute_step(
        self,
        workflow: Workflow,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> None:
        """Execute a single workflow step"""
        try:
            # Mark step as running
            context.mark_step_started(step.step_id)
            
            # Execute based on step type
            if step.step_type == "action":
                result = await self._execute_action(step, context)
            elif step.step_type == "condition":
                result = await self._execute_condition(step, context)
            elif step.step_type == "wait":
                result = await self._execute_wait(step, context)
            elif step.step_type == "parallel":
                result = await self._execute_parallel_steps(step, context)
            elif step.step_type == "loop":
                result = await self._execute_loop(step, context)
            else:
                result = None
            
            # Store result
            context.mark_step_completed(step.step_id, result)
            
            # Queue dependent steps
            await self._queue_dependent_steps(workflow, step, context)
            
            # Log success
            await self.audit_logger.log_step_complete(workflow, step, context, result)
            
        except Exception as e:
            context.mark_step_failed(step.step_id, str(e))
            
            # Log failure
            await self.audit_logger.log_step_failure(workflow, step, context, str(e))
    
    async def _execute_action(
        self,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> Any:
        """Execute an action step"""
        if not step.action:
            return None
        
        # Get action parameters
        parameters = step.action.parameters.copy()
        
        # Resolve variables in parameters
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("$"):
                var_name = value[1:]
                parameters[key] = context.variables.get(var_name, value)
        
        # Execute based on action type
        if step.action.type == "tool":
            # Execute MCP tool
            return await self._execute_tool(step.action.tool or "", parameters)
        elif step.action.type == "integration":
            # Execute integration action
            return await self._execute_integration(
                step.action.integration or "",
                step.action.name,
                parameters
            )
        elif step.action.type == "adapter":
            # Execute adapter action
            return await self._execute_adapter(
                step.action.adapter or "",
                step.action.name,
                parameters
            )
        elif step.action.type == "script":
            # Execute script
            return await self._execute_script(step.action.script or "", parameters)
        else:
            # Unknown action type
            return None
    
    async def _execute_condition(
        self,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> bool:
        """Execute a condition step"""
        if not step.condition:
            return True
        
        result = step.condition.evaluate(context.variables)
        
        # Follow true or false path
        if result and step.true_step:
            # Queue true step
            true_step = context.workflow.steps.get(step.true_step)
            if true_step:
                await self._queue_step(context.workflow, true_step, context)
        elif not result and step.false_step:
            # Queue false step
            false_step = context.workflow.steps.get(step.false_step)
            if false_step:
                await self._queue_step(context.workflow, false_step, context)
        
        return result
    
    async def _execute_wait(
        self,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> None:
        """Execute a wait step"""
        if step.wait_seconds:
            await asyncio.sleep(step.wait_seconds)
        elif step.wait_until:
            # Parse wait_until as ISO timestamp
            from datetime import datetime as dt
            wait_until = dt.fromisoformat(step.wait_until)
            now = dt.now(timezone.utc)
            wait_seconds = (wait_until - now).total_seconds()
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
    
    async def _execute_parallel_steps(
        self,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> List[Any]:
        """Execute parallel steps"""
        results = []
        
        tasks = []
        for parallel_step_id in step.parallel_steps:
            parallel_step = context.workflow.steps.get(parallel_step_id)
            if parallel_step:
                task = asyncio.create_task(
                    self._execute_step(context.workflow, parallel_step, context)
                )
                tasks.append(task)
        
        # Wait for all parallel steps
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        for parallel_step_id in step.parallel_steps:
            if parallel_step_id in context.completed_steps:
                results.append(context.results.get(parallel_step_id))
            elif parallel_step_id in context.failed_steps:
                results.append({"error": context.errors.get(parallel_step_id)})
        
        return results
    
    async def _execute_loop(
        self,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> List[Any]:
        """Execute a loop step"""
        results = []
        
        if not step.loop_items or not step.loop_step:
            return results
        
        # Get items to loop over
        items = context.variables.get(step.loop_items, [])
        
        # Get loop step
        loop_step = context.workflow.steps.get(step.loop_step)
        if not loop_step:
            return results
        
        # Execute for each item
        for i, item in enumerate(items):
            # Set loop variable
            context.variables[f"{step.loop_items}_index"] = i
            context.variables[f"{step.loop_items}_item"] = item
            
            # Execute loop step
            await self._execute_step(context.workflow, loop_step, context)
            
            # Collect result if step completed
            if step.loop_step in context.completed_steps:
                results.append(context.results.get(step.loop_step))
        
        return results
    
    async def _queue_dependent_steps(
        self,
        workflow: Workflow,
        step: WorkflowStep,
        context: ExecutionContext
    ) -> None:
        """Queue dependent steps after a step completes"""
        # Get dependency graph
        dep_graph = self.active_dependency_graphs.get(workflow.uaw_id.entity_id)
        if not dep_graph:
            return
        
        # Get dependents of this step
        dependents = dep_graph.get_dependents(step.step_id)
        
        # Queue each dependent if it can be executed
        for dep_id in dependents:
            dep_step = workflow.steps.get(dep_id)
            if dep_step and self._can_execute_step(dep_step, context):
                await self._queue_step(workflow, dep_step, context)
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute an MCP tool"""
        # This would be implemented with actual MCP tool execution
        # For now, return mock result
        return {
            "tool": tool_name,
            "parameters": parameters,
            "status": "executed"
        }
    
    async def _execute_integration(
        self,
        integration_name: str,
        action: str,
        parameters: Dict[str, Any]
    ) -> Any:
        """Execute an integration action"""
        # This would be implemented with actual integration execution
        # For now, return mock result
        return {
            "integration": integration_name,
            "action": action,
            "parameters": parameters,
            "status": "executed"
        }
    
    async def _execute_adapter(
        self,
        adapter_name: str,
        action: str,
        parameters: Dict[str, Any]
    ) -> Any:
        """Execute an adapter action"""
        # This would be implemented with actual adapter execution
        # For now, return mock result
        return {
            "adapter": adapter_name,
            "action": action,
            "parameters": parameters,
            "status": "executed"
        }
    
    async def _execute_script(
        self,
        script: str,
        parameters: Dict[str, Any]
    ) -> Any:
        """Execute a script"""
        # This would execute a Python script
        # For now, return mock result
        return {
            "script": script,
            "parameters": parameters,
            "status": "executed"
        }
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if workflow:
            workflow.set_status(WorkflowStatus.PAUSED)
            return True
        return False
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow"""
        # Get workflow from state manager
        workflow_data = await self.state_manager.get_workflow(workflow_id)
        if not workflow_data:
            return False
        
        workflow = Workflow.from_dict(workflow_data)
        workflow.set_status(WorkflowStatus.RUNNING)
        
        # Re-execute workflow
        asyncio.create_task(self.execute_workflow(workflow))
        return True
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if workflow:
            workflow.set_status(WorkflowStatus.CANCELLED)
            return True
        return False
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[str]:
        """Get status of a workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if workflow:
            return workflow.status.value
        return None
    
    async def get_execution_context(self, workflow_id: str) -> Optional[ExecutionContext]:
        """Get execution context for a workflow"""
        return self.active_executions.get(workflow_id)
    
    def on(self, event: str, callback: Callable) -> None:
        """Register a callback for an event"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    async def _trigger_callbacks(
        self,
        event: str,
        workflow: Workflow,
        context: ExecutionContext
    ) -> None:
        """Trigger callbacks for an event"""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(workflow, context)
                    else:
                        callback(workflow, context)
                except Exception as e:
                    # Log callback error
                    await self.audit_logger.log_error(
                        f"Callback error for event {event}",
                        str(e),
                        {"workflow_id": workflow.uaw_id.entity_id}
                    )
    
    async def save_state(self) -> None:
        """Save current state"""
        # Save active workflows
        for workflow_id, workflow in self.active_workflows.items():
            await self.state_manager.save_workflow(workflow)
        
        # Save active executions
        for exec_id, context in self.active_executions.items():
            await self.state_manager.save_execution_context(exec_id, context.to_dict())
    
    async def restore_state(self) -> None:
        """Restore state from persistence"""
        # Restore active workflows
        workflows = await self.state_manager.list_workflows()
        for workflow_data in workflows:
            workflow = Workflow.from_dict(workflow_data)
            if workflow.status == WorkflowStatus.RUNNING:
                self.active_workflows[workflow.uaw_id.entity_id] = workflow
        
        # Restore active executions
        executions = await self.state_manager.list_execution_contexts()
        for exec_data in executions:
            context = ExecutionContext(**exec_data)
            self.active_executions[context.workflow_id] = context


# Singleton instance
workflow_engine = WorkflowEngine()
