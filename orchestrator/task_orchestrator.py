"""
Task Orchestrator for UAW
Оркестратор задач для управления выполнением рабочих процессов
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path

from ..core.uaw_core import UAWCore, Workflow, WorkflowStep, TaskStatus
from ..core.state_manager import StateManager
from ..core.audit import AuditLogger, AuditEventType
from ..integrations.registry import IntegrationRegistry
from ..adapters.registry import AdapterRegistry


class OrchestratorMode(Enum):
    """Orchestrator execution modes"""
    SEQUENTIAL = auto()  # Execute tasks one at a time
    PARALLEL = auto()    # Execute independent tasks in parallel
    SMART = auto()       # Mix of sequential and parallel based on dependencies


class ExecutionStrategy(Enum):
    """Execution strategies"""
    IMMEDIATE = auto()   # Execute immediately
    QUEUED = auto()      # Queue for execution
    SCHEDULED = auto()   # Schedule for later execution
    BATCHED = auto()     # Batch with other tasks


@dataclass
class TaskExecution:
    """Single task execution context"""
    task_id: str
    workflow_id: str
    step: WorkflowStep
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    retries: int = 0
    dependencies_completed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "step": self.step.to_dict(),
            "status": self.status.name,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "retries": self.retries,
            "dependencies_completed": self.dependencies_completed
        }


@dataclass
class WorkflowExecution:
    """Workflow execution context"""
    workflow_id: str
    workflow: Workflow
    tasks: Dict[str, TaskExecution] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    current_task: Optional[str] = None
    completed_tasks: Set[str] = field(default_factory=set)
    failed_tasks: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow": self.workflow.to_dict(),
            "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
            "status": self.status.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "results": self.results,
            "errors": self.errors,
            "current_task": self.current_task,
            "completed_tasks": list(self.completed_tasks),
            "failed_tasks": list(self.failed_tasks)
        }


class TaskOrchestrator:
    """
    Orchestrates the execution of workflows and tasks.
    Manages dependencies, parallel execution, retries, and state persistence.
    """
    
    def __init__(
        self,
        uaw_core: UAWCore,
        mode: OrchestratorMode = OrchestratorMode.SMART,
        max_concurrent_tasks: int = 10,
        default_timeout: int = 300  # 5 minutes
    ):
        self.uaw_core = uaw_core
        self.mode = mode
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_timeout = default_timeout
        
        # State management
        self.state_manager = uaw_core.state_manager
        self.audit_logger = uaw_core.audit_logger
        
        # Registries
        self.integration_registry = uaw_core.integration_registry
        self.adapter_registry = uaw_core.adapter_registry
        
        # Active executions
        self.active_executions: Dict[str, WorkflowExecution] = {}
        
        # Task queue
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._running_tasks: Set[str] = set()
        
        # Event loop
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._shutdown = False
        
        # Callbacks
        self._on_task_complete: List[Callable[[TaskExecution], Coroutine]] = []
        self._on_workflow_complete: List[Callable[[WorkflowExecution], Coroutine]] = []
        self._on_error: List[Callable[[TaskExecution, Exception], Coroutine]] = []
        
        # Load existing executions
        self._load_state()
    
    def _load_state(self):
        """Load state from state manager"""
        # This would load saved executions from the state manager
        pass
    
    def _save_state(self):
        """Save state to state manager"""
        # This would save active executions to the state manager
        pass
    
    async def initialize(self):
        """Initialize the orchestrator"""
        self._loop = asyncio.get_event_loop()
        
        # Start worker tasks
        if self.mode in [OrchestratorMode.PARALLEL, OrchestratorMode.SMART]:
            for i in range(self.max_concurrent_tasks):
                self._loop.create_task(self._worker(f"worker_{i}"))
        
        self.audit_logger.log(
            AuditEventType.SYSTEM_START,
            "Orchestrator initialized",
            {
                "mode": self.mode.name,
                "max_concurrent_tasks": self.max_concurrent_tasks
            }
        )
    
    async def shutdown(self):
        """Shutdown the orchestrator"""
        self._shutdown = True
        
        # Wait for running tasks to complete
        while self._running_tasks:
            await asyncio.sleep(0.1)
        
        self.audit_logger.log(
            AuditEventType.SYSTEM_SHUTDOWN,
            "Orchestrator shutdown",
            {"pending_tasks": self._task_queue.qsize()}
        )
    
    async def _worker(self, worker_id: str):
        """Worker task that processes queued tasks"""
        while not self._shutdown:
            try:
                # Get next task with timeout
                try:
                    task_execution = await asyncio.wait_for(
                        self._task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Add to running tasks
                self._running_tasks.add(task_execution.task_id)
                
                # Execute the task
                try:
                    await self._execute_task(task_execution)
                except Exception as e:
                    self.audit_logger.log(
                        AuditEventType.ERROR,
                        "Task execution failed in worker",
                        {
                            "worker_id": worker_id,
                            "task_id": task_execution.task_id,
                            "error": str(e)
                        },
                        severity="error"
                    )
                finally:
                    # Remove from running tasks
                    self._running_tasks.discard(task_execution.task_id)
                    self._task_queue.task_done()
                    
            except Exception as e:
                self.audit_logger.log(
                    AuditEventType.ERROR,
                    "Worker error",
                    {
                        "worker_id": worker_id,
                        "error": str(e)
                    },
                    severity="error"
                )
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        strategy: ExecutionStrategy = ExecutionStrategy.IMMEDIATE
    ) -> WorkflowExecution:
        """
        Execute a workflow.
        
        Args:
            workflow: Workflow to execute
            strategy: Execution strategy
            
        Returns:
            WorkflowExecution with results
        """
        workflow_id = workflow.id
        
        # Create execution context
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            workflow=workflow
        )
        
        self.active_executions[workflow_id] = execution
        
        # Initialize tasks
        for step_id, step in workflow.steps.items():
            task_execution = TaskExecution(
                task_id=f"{workflow_id}_{step_id}",
                workflow_id=workflow_id,
                step=step
            )
            execution.tasks[step_id] = task_execution
        
        # Set start time
        execution.start_time = datetime.now(timezone.utc).isoformat()
        workflow.started_at = execution.start_time
        
        self.audit_logger.log(
            AuditEventType.WORKFLOW_START,
            "Workflow execution started",
            {
                "workflow_id": workflow_id,
                "name": workflow.name,
                "step_count": len(workflow.steps)
            }
        )
        
        try:
            if strategy == ExecutionStrategy.IMMEDIATE:
                await self._execute_workflow_immediate(execution)
            elif strategy == ExecutionStrategy.QUEUED:
                await self._execute_workflow_queued(execution)
            elif strategy == ExecutionStrategy.SCHEDULED:
                await self._execute_workflow_scheduled(execution)
            else:
                await self._execute_workflow_immediate(execution)
            
            # Check if workflow is complete
            if execution.status == TaskStatus.COMPLETED:
                self.audit_logger.log(
                    AuditEventType.WORKFLOW_COMPLETE,
                    "Workflow completed",
                    {
                        "workflow_id": workflow_id,
                        "duration": f"{(execution.end_time - execution.start_time) if execution.end_time and execution.start_time else 'N/A'}"
                    }
                )
                
                # Call completion callbacks
                for callback in self._on_workflow_complete:
                    await callback(execution)
            
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.errors.append(str(e))
            
            self.audit_logger.log(
                AuditEventType.WORKFLOW_FAIL,
                "Workflow failed",
                {
                    "workflow_id": workflow_id,
                    "error": str(e)
                },
                severity="error"
            )
        
        return execution
    
    async def _execute_workflow_immediate(self, execution: WorkflowExecution):
        """Execute workflow immediately"""
        workflow = execution.workflow
        
        # Get execution order
        execution_order = workflow.get_execution_order()
        
        for step_id in execution_order:
            task_execution = execution.tasks[step_id]
            
            # Execute the task
            await self._execute_task(task_execution)
            
            # Check if we should stop
            if execution.status == TaskStatus.CANCELLED:
                break
            if task_execution.status == TaskStatus.FAILED:
                # Check if we should continue with other tasks
                if self._should_continue_on_failure(execution):
                    continue
                else:
                    execution.status = TaskStatus.FAILED
                    break
        
        # Update workflow status
        if execution.status == TaskStatus.PENDING:
            execution.status = TaskStatus.COMPLETED
        
        execution.end_time = datetime.now(timezone.utc).isoformat()
        workflow.completed_at = execution.end_time
    
    async def _execute_workflow_queued(self, execution: WorkflowExecution):
        """Execute workflow using task queue"""
        workflow = execution.workflow
        
        # Queue all ready tasks
        for step_id in workflow.get_ready_steps():
            task_execution = execution.tasks[step_id]
            await self._task_queue.put(task_execution)
        
        # Wait for all tasks to complete
        while True:
            # Check if all tasks are complete
            all_complete = all(
                task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                for task in execution.tasks.values()
            )
            
            if all_complete:
                # Update workflow status
                if execution.status == TaskStatus.PENDING:
                    execution.status = TaskStatus.COMPLETED
                execution.end_time = datetime.now(timezone.utc).isoformat()
                workflow.completed_at = execution.end_time
                break
            
            # Check for failures
            if any(task.status == TaskStatus.FAILED for task in execution.tasks.values()):
                if not self._should_continue_on_failure(execution):
                    execution.status = TaskStatus.FAILED
                    execution.end_time = datetime.now(timezone.utc).isoformat()
                    break
            
            # Wait a bit
            await asyncio.sleep(0.1)
    
    async def _execute_workflow_scheduled(self, execution: WorkflowExecution):
        """Execute workflow on a schedule"""
        # For now, just execute immediately
        await self._execute_workflow_immediate(execution)
    
    def _should_continue_on_failure(self, execution: WorkflowExecution) -> bool:
        """Determine if we should continue execution after a task failure"""
        # Check workflow configuration or settings
        # For now, always continue
        return True
    
    async def _execute_task(self, task_execution: TaskExecution):
        """Execute a single task"""
        step = task_execution.step
        workflow_id = task_execution.workflow_id
        task_id = task_execution.task_id
        
        # Get execution context
        execution = self.active_executions.get(workflow_id)
        if not execution:
            task_execution.status = TaskStatus.FAILED
            task_execution.error = "Workflow execution not found"
            return
        
        # Set start time
        task_execution.start_time = datetime.now(timezone.utc).isoformat()
        execution.current_task = task_id
        
        self.audit_logger.log(
            AuditEventType.STEP_START,
            "Task execution started",
            {
                "workflow_id": workflow_id,
                "task_id": task_id,
                "step_name": step.name
            }
        )
        
        try:
            # Check dependencies
            if not task_execution.dependencies_completed:
                if not self._check_dependencies(task_execution, execution):
                    task_execution.status = TaskStatus.PENDING
                    return
                task_execution.dependencies_completed = True
            
            # Execute the step
            result = await self.uaw_core._execute_step(step, execution.workflow)
            
            # Update task status
            task_execution.status = TaskStatus.COMPLETED
            task_execution.result = result
            execution.results[task_id] = result
            execution.completed_tasks.add(task_id)
            
            self.audit_logger.log(
                AuditEventType.STEP_COMPLETE,
                "Task completed",
                {
                    "workflow_id": workflow_id,
                    "task_id": task_id,
                    "step_name": step.name,
                    "result": result
                }
            )
            
            # Call completion callbacks
            for callback in self._on_task_complete:
                await callback(task_execution)
            
            # Queue dependent tasks
            await self._queue_dependent_tasks(task_execution, execution)
            
        except Exception as e:
            task_execution.status = TaskStatus.FAILED
            task_execution.error = str(e)
            task_execution.retries += 1
            execution.failed_tasks.add(task_id)
            
            self.audit_logger.log(
                AuditEventType.STEP_FAIL,
                "Task failed",
                {
                    "workflow_id": workflow_id,
                    "task_id": task_id,
                    "step_name": step.name,
                    "error": str(e),
                    "retries": task_execution.retries
                },
                severity="error"
            )
            
            # Call error callbacks
            for callback in self._on_error:
                await callback(task_execution, e)
            
            # Check if we should retry
            if task_execution.retries < step.max_retries:
                task_execution.status = TaskStatus.PENDING
                task_execution.dependencies_completed = False
            else:
                task_execution.status = TaskStatus.FAILED
        finally:
            # Set end time
            task_execution.end_time = datetime.now(timezone.utc).isoformat()
            execution.current_task = None
    
    def _check_dependencies(
        self,
        task_execution: TaskExecution,
        execution: WorkflowExecution
    ) -> bool:
        """Check if all dependencies are completed"""
        step = task_execution.step
        
        for dep_id in step.dependencies:
            dep_task = execution.tasks.get(dep_id)
            if not dep_task:
                return False
            if dep_task.status not in [TaskStatus.COMPLETED]:
                return False
        
        return True
    
    async def _queue_dependent_tasks(
        self,
        task_execution: TaskExecution,
        execution: WorkflowExecution
    ):
        """Queue tasks that depend on this task"""
        task_id = task_execution.task_id
        workflow = execution.workflow
        
        # Find tasks that depend on this task
        for step_id, step in workflow.steps.items():
            if task_id in step.dependencies:
                dep_task = execution.tasks.get(step_id)
                if dep_task and dep_task.status == TaskStatus.PENDING:
                    # Check if all dependencies are now complete
                    all_deps_complete = all(
                        execution.tasks[dep].status == TaskStatus.COMPLETED
                        for dep in step.dependencies
                    )
                    
                    if all_deps_complete:
                        dep_task.dependencies_completed = True
                        
                        if self.mode == OrchestratorMode.PARALLEL:
                            await self._task_queue.put(dep_task)
                        else:
                            # In sequential mode, tasks will be picked up in order
                            pass
    
    def get_execution(self, workflow_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID"""
        return self.active_executions.get(workflow_id)
    
    def list_executions(self) -> List[WorkflowExecution]:
        """List all active executions"""
        return list(self.active_executions.values())
    
    async def cancel_execution(self, workflow_id: str) -> bool:
        """Cancel a workflow execution"""
        execution = self.active_executions.get(workflow_id)
        if not execution:
            return False
        
        execution.status = TaskStatus.CANCELLED
        execution.end_time = datetime.now(timezone.utc).isoformat()
        
        # Cancel all pending tasks
        for task in execution.tasks.values():
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
        
        self.audit_logger.log(
            AuditEventType.WORKFLOW_CANCEL,
            "Workflow execution cancelled",
            {"workflow_id": workflow_id}
        )
        
        return True
    
    def on_task_complete(
        self,
        callback: Callable[[TaskExecution], Coroutine]
    ) -> None:
        """Register callback for task completion"""
        self._on_task_complete.append(callback)
    
    def on_workflow_complete(
        self,
        callback: Callable[[WorkflowExecution], Coroutine]
    ) -> None:
        """Register callback for workflow completion"""
        self._on_workflow_complete.append(callback)
    
    def on_error(
        self,
        callback: Callable[[TaskExecution, Exception], Coroutine]
    ) -> None:
        """Register callback for errors"""
        self._on_error.append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            "active_executions": len(self.active_executions),
            "pending_tasks": self._task_queue.qsize(),
            "running_tasks": len(self._running_tasks),
            "completed_tasks": sum(
                len(execution.completed_tasks)
                for execution in self.active_executions.values()
            ),
            "failed_tasks": sum(
                len(execution.failed_tasks)
                for execution in self.active_executions.values()
            )
        }
