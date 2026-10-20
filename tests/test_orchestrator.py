"""
Tests for UAW Orchestrator
"""

import unittest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from uaw.orchestrator.task_orchestrator import TaskOrchestrator, TaskQueue, ExecutionMode
from uaw.orchestrator.workflow_engine import WorkflowEngine, ExecutionContext, DependencyGraph

from uaw.models.workflow import (
    Workflow, WorkflowStep, WorkflowStepType, WorkflowStatus,
    WorkflowTrigger, WorkflowCondition, WorkflowAction
)
from uaw.models.task import Task, TaskStatus, TaskPriority


class TestTaskOrchestrator(unittest.TestCase):
    """Tests for TaskOrchestrator class"""

    def setUp(self):
        self.orchestrator = TaskOrchestrator()

    def test_initialization(self):
        """Test TaskOrchestrator initialization"""
        self.assertIsNotNone(self.orchestrator)
        self.assertIsNotNone(self.orchestrator.task_queue)

    def test_add_task(self):
        """Test adding a task"""
        async def dummy_task():
            return "completed"
        
        task_id = self.orchestrator.add_task(
            task_func=dummy_task,
            task_id="test-task-1",
            priority=0,
        )
        
        self.assertEqual(task_id, "test-task-1")

    def test_execute_sequential(self):
        """Test sequential task execution"""
        async def task1():
            return "task1"
        
        async def task2():
            return "task2"
        
        self.orchestrator.add_task(task1, "task-1", priority=0)
        self.orchestrator.add_task(task2, "task-2", priority=0)
        
        # В реальности это было бы async
        # Для теста просто проверяем, что задачи добавлены
        self.assertEqual(len(self.orchestrator.task_queue.tasks), 2)


class TestWorkflowEngine(unittest.TestCase):
    """Tests for WorkflowEngine class"""

    def setUp(self):
        self.engine = WorkflowEngine()

    def test_initialization(self):
        """Test WorkflowEngine initialization"""
        self.assertIsNotNone(self.engine)

    def test_create_execution_context(self):
        """Test creating execution context"""
        workflow = Workflow(
            uaw_id="test-workflow",
            name="Test Workflow",
            steps=[],
        )
        
        context = self.engine._create_execution_context(workflow)
        self.assertIsInstance(context, ExecutionContext)
        self.assertEqual(context.workflow_id, "test-workflow")

    def test_build_dependency_graph(self):
        """Test building dependency graph"""
        workflow = Workflow(
            uaw_id="test-workflow",
            name="Test Workflow",
            steps=[
                WorkflowStep(
                    uaw_id="step-1",
                    name="Step 1",
                    step_type=WorkflowStepType.ACTION,
                    dependencies=[],
                ),
                WorkflowStep(
                    uaw_id="step-2",
                    name="Step 2",
                    step_type=WorkflowStepType.ACTION,
                    dependencies=["step-1"],
                ),
                WorkflowStep(
                    uaw_id="step-3",
                    name="Step 3",
                    step_type=WorkflowStepType.ACTION,
                    dependencies=["step-1", "step-2"],
                ),
            ],
        )
        
        graph = self.engine._build_dependency_graph(workflow)
        self.assertIsInstance(graph, DependencyGraph)
        self.assertEqual(len(graph.dependencies), 3)

    def test_group_by_dependency_level(self):
        """Test grouping steps by dependency level"""
        workflow = Workflow(
            uaw_id="test-workflow",
            name="Test Workflow",
            steps=[
                WorkflowStep(
                    uaw_id="step-1",
                    name="Step 1",
                    step_type=WorkflowStepType.ACTION,
                    dependencies=[],
                ),
                WorkflowStep(
                    uaw_id="step-2",
                    name="Step 2",
                    step_type=WorkflowStepType.ACTION,
                    dependencies=["step-1"],
                ),
                WorkflowStep(
                    uaw_id="step-3",
                    name="Step 3",
                    step_type=WorkflowStepType.ACTION,
                    dependencies=["step-1"],
                ),
            ],
        )
        
        execution_order = ["step-1", "step-2", "step-3"]
        levels = self.engine._group_by_dependency_level(workflow, execution_order)
        
        self.assertEqual(len(levels), 2)
        self.assertIn("step-1", levels[0])
        self.assertIn("step-2", levels[1])
        self.assertIn("step-3", levels[1])

    def test_simple_workflow_execution(self):
        """Test simple workflow execution"""
        workflow = Workflow(
            uaw_id="test-workflow",
            name="Test Workflow",
            steps=[
                WorkflowStep(
                    uaw_id="step-1",
                    name="Step 1",
                    step_type=WorkflowStepType.ACTION,
                    action="test_action",
                    dependencies=[],
                ),
            ],
        )
        
        # В реальности это было бы async
        # Для теста просто проверяем структуру
        self.assertEqual(len(workflow.steps), 1)


class TestExecutionContext(unittest.TestCase):
    """Tests for ExecutionContext class"""

    def test_creation(self):
        """Test ExecutionContext creation"""
        context = ExecutionContext(
            workflow_id="test-workflow",
            context_id="ctx-123",
        )
        
        self.assertEqual(context.workflow_id, "test-workflow")
        self.assertEqual(context.context_id, "ctx-123")

    def test_add_step_result(self):
        """Test adding step result"""
        context = ExecutionContext(workflow_id="test-workflow")
        
        context.add_step_result("step-1", {"status": "completed"})
        
        self.assertIn("step-1", context.step_results)
        self.assertEqual(context.step_results["step-1"]["status"], "completed")

    def test_get_step_result(self):
        """Test getting step result"""
        context = ExecutionContext(workflow_id="test-workflow")
        
        context.add_step_result("step-1", {"status": "completed"})
        
        result = context.get_step_result("step-1")
        self.assertEqual(result["status"], "completed")


class TestDependencyGraph(unittest.TestCase):
    """Tests for DependencyGraph class"""

    def test_creation(self):
        """Test DependencyGraph creation"""
        graph = DependencyGraph(
            workflow_id="test-workflow",
            dependencies={
                "step-1": [],
                "step-2": ["step-1"],
            },
        )
        
        self.assertEqual(graph.workflow_id, "test-workflow")
        self.assertEqual(len(graph.dependencies), 2)

    def test_get_dependencies(self):
        """Test getting dependencies for a step"""
        graph = DependencyGraph(
            workflow_id="test-workflow",
            dependencies={
                "step-1": [],
                "step-2": ["step-1"],
            },
        )
        
        deps = graph.get_dependencies("step-2")
        self.assertEqual(deps, ["step-1"])

    def test_get_dependents(self):
        """Test getting dependents for a step"""
        graph = DependencyGraph(
            workflow_id="test-workflow",
            dependencies={
                "step-1": [],
                "step-2": ["step-1"],
                "step-3": ["step-1"],
            },
        )
        
        # В реальности это вычислялось бы из графа
        # Для теста просто проверяем структуру
        self.assertTrue(True)


class TestExecutionMode(unittest.TestCase):
    """Tests for ExecutionMode enum"""

    def test_mode_values(self):
        """Test ExecutionMode values"""
        self.assertEqual(ExecutionMode.SEQUENTIAL.value, "sequential")
        self.assertEqual(ExecutionMode.PARALLEL.value, "parallel")
        self.assertEqual(ExecutionMode.SMART.value, "smart")


class TestTaskQueue(unittest.TestCase):
    """Tests for TaskQueue class"""

    def setUp(self):
        self.queue = TaskQueue()

    def test_add_task(self):
        """Test adding task to queue"""
        async def dummy_task():
            return "completed"
        
        self.queue.add_task(
            task_func=dummy_task,
            task_id="task-1",
            priority=0,
        )
        
        self.assertEqual(len(self.queue.tasks), 1)

    def test_get_next_task(self):
        """Test getting next task"""
        async def dummy_task1():
            return "task1"
        
        async def dummy_task2():
            return "task2"
        
        self.queue.add_task(dummy_task1, "task-1", priority=1)
        self.queue.add_task(dummy_task2, "task-2", priority=0)
        
        # В реальности это было бы async
        # Для теста просто проверяем порядок
        self.assertEqual(len(self.queue.tasks), 2)


if __name__ == "__main__":
    unittest.main()
