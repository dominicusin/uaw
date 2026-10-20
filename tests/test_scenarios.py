"""
Tests for UAW Scenarios
"""

import unittest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from uaw.scenarios.first_skvoznoy import (
    FirstSkvoznoyScenario,
    FixBugWorkflow,
    execute_fix_bug_scenario,
    FIX_BUG_WORKFLOW_DEFINITION,
    ScenarioReport,
    StepResult,
    StepResultStatus,
)
from uaw.models.workflow import Workflow, WorkflowStep, WorkflowStepType, WorkflowStatus
from uaw.models.person import Person


class TestFixBugWorkflow(unittest.TestCase):
    """Tests for FixBugWorkflow class"""

    def setUp(self):
        self.workflow = FixBugWorkflow()

    def test_workflow_definition(self):
        """Test workflow definition structure"""
        self.assertIn("workflow_id", FIX_BUG_WORKFLOW_DEFINITION)
        self.assertIn("name", FIX_BUG_WORKFLOW_DEFINITION)
        self.assertIn("steps", FIX_BUG_WORKFLOW_DEFINITION)
        self.assertGreater(len(FIX_BUG_WORKFLOW_DEFINITION["steps"]), 0)

    def test_workflow_definition_steps(self):
        """Test that all required steps are defined"""
        steps = FIX_BUG_WORKFLOW_DEFINITION["steps"]
        step_ids = [s["step_id"] for s in steps]
        
        required_steps = [
            "step:analyze-request",
            "step:find-repository",
            "step:create-github-issue",
            "step:create-asana-task",
            "step:create-branch",
            "step:implement-fix",
            "step:run-tests",
            "step:verify-tests",
            "step:create-pull-request",
            "step:preview-deployment",
            "step:verify-deployment",
            "step:notify-teams",
            "step:schedule-meeting",
            "step:sync-resources",
            "step:generate-report",
        ]
        
        for step_id in required_steps:
            self.assertIn(step_id, step_ids)

    def test_create_workflow(self):
        """Test workflow creation"""
        workflow = self.workflow.create_workflow(
            project_name="test-project",
            bug_title="Test Bug",
            bug_description="Test description",
            assignee={"name": "John Doe", "github": "johndoe"},
        )
        
        self.assertIsInstance(workflow, Workflow)
        self.assertEqual(workflow.name, FIX_BUG_WORKFLOW_DEFINITION["name"])
        self.assertGreater(len(workflow.steps), 0)

    def test_workflow_steps_structure(self):
        """Test that workflow steps have correct structure"""
        workflow = self.workflow.create_workflow(
            project_name="test-project",
            bug_title="Test Bug",
            bug_description="Test description",
            assignee={"name": "John Doe"},
        )
        
        for step in workflow.steps:
            self.assertIsInstance(step, WorkflowStep)
            self.assertIsNotNone(step.uaw_id)
            self.assertIsNotNone(step.name)
            self.assertIsInstance(step.step_type, WorkflowStepType)


class TestFirstSkvoznoyScenario(unittest.TestCase):
    """Tests for FirstSkvoznoyScenario class"""

    def setUp(self):
        self.scenario = FirstSkvoznoyScenario()

    @patch('uaw.scenarios.first_skvoznoy.FixBugWorkflow')
    async def test_execute(self, mock_workflow_class):
        """Test scenario execution"""
        # Setup mock
        mock_workflow = AsyncMock()
        mock_workflow.create_workflow.return_value = Workflow(
            uaw_id="test-workflow",
            name="Test",
            steps=[],
        )
        mock_workflow.execute.return_value = ScenarioReport(
            scenario_id="test",
            scenario_name="Test",
            started_at=datetime.utcnow(),
            status=WorkflowStatus.COMPLETED,
        )
        mock_workflow_class.return_value = mock_workflow
        
        # Execute
        report = await self.scenario.execute(
            project_name="test-project",
            bug_title="Test Bug",
            bug_description="Test description",
            assignee={"name": "John Doe"},
        )
        
        self.assertIsInstance(report, ScenarioReport)
        self.assertEqual(report.status, WorkflowStatus.COMPLETED)


class TestExecuteFixBugScenario(unittest.TestCase):
    """Tests for execute_fix_bug_scenario function"""

    @patch('uaw.scenarios.first_skvoznoy.FirstSkvoznoyScenario')
    async def test_execute_fix_bug_scenario(self, mock_scenario_class):
        """Test execute_fix_bug_scenario function"""
        # Setup mock
        mock_scenario = AsyncMock()
        mock_scenario.execute.return_value = ScenarioReport(
            scenario_id="test",
            scenario_name="Test",
            started_at=datetime.utcnow(),
            status=WorkflowStatus.COMPLETED,
        )
        mock_scenario_class.return_value = mock_scenario
        
        # Execute
        report = await execute_fix_bug_scenario(
            project_name="test-project",
            bug_title="Test Bug",
            bug_description="Test description",
            assignee={"name": "John Doe", "github": "johndoe"},
        )
        
        self.assertIsInstance(report, ScenarioReport)


class TestScenarioReport(unittest.TestCase):
    """Tests for ScenarioReport class"""

    def test_report_creation(self):
        """Test report creation"""
        report = ScenarioReport(
            scenario_id="test-123",
            scenario_name="Test Scenario",
            started_at=datetime.utcnow(),
        )
        
        self.assertEqual(report.scenario_id, "test-123")
        self.assertEqual(report.scenario_name, "Test Scenario")
        self.assertIsNotNone(report.started_at)

    def test_add_step_result(self):
        """Test adding step result"""
        report = ScenarioReport(
            scenario_id="test-123",
            scenario_name="Test",
            started_at=datetime.utcnow(),
        )
        
        step_result = StepResult(
            step_id="step:1",
            step_name="Test Step",
            status=StepResultStatus.COMPLETED,
        )
        
        report.add_step_result(step_result)
        
        self.assertIn("step:1", report.steps)
        self.assertEqual(report.steps["step:1"].status, StepResultStatus.COMPLETED)

    def test_get_completed_steps(self):
        """Test getting completed steps"""
        report = ScenarioReport(
            scenario_id="test-123",
            scenario_name="Test",
            started_at=datetime.utcnow(),
        )
        
        # Add some steps
        report.add_step_result(StepResult(
            step_id="step:1",
            step_name="Step 1",
            status=StepResultStatus.COMPLETED,
        ))
        report.add_step_result(StepResult(
            step_id="step:2",
            step_name="Step 2",
            status=StepResultStatus.FAILED,
        ))
        report.add_step_result(StepResult(
            step_id="step:3",
            step_name="Step 3",
            status=StepResultStatus.COMPLETED,
        ))
        
        completed = report.get_completed_steps()
        self.assertEqual(len(completed), 2)

    def test_get_failed_steps(self):
        """Test getting failed steps"""
        report = ScenarioReport(
            scenario_id="test-123",
            scenario_name="Test",
            started_at=datetime.utcnow(),
        )
        
        report.add_step_result(StepResult(
            step_id="step:1",
            step_name="Step 1",
            status=StepResultStatus.FAILED,
        ))
        report.add_step_result(StepResult(
            step_id="step:2",
            step_name="Step 2",
            status=StepResultStatus.FAILED,
        ))
        
        failed = report.get_failed_steps()
        self.assertEqual(len(failed), 2)

    def test_add_error(self):
        """Test adding error"""
        report = ScenarioReport(
            scenario_id="test-123",
            scenario_name="Test",
            started_at=datetime.utcnow(),
        )
        
        report.add_error({"message": "Test error", "details": "Error details"})
        
        self.assertEqual(len(report.errors), 1)
        self.assertEqual(report.errors[0]["message"], "Test error")

    def test_add_warning(self):
        """Test adding warning"""
        report = ScenarioReport(
            scenario_id="test-123",
            scenario_name="Test",
            started_at=datetime.utcnow(),
        )
        
        report.add_warning("Test warning")
        
        self.assertEqual(len(report.warnings), 1)
        self.assertEqual(report.warnings[0], "Test warning")

    def test_to_markdown(self):
        """Test markdown report generation"""
        report = ScenarioReport(
            scenario_id="test-123",
            scenario_name="Test Scenario",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            status=WorkflowStatus.COMPLETED,
            execution_time_seconds=10.5,
            summary="Test completed successfully",
        )
        
        report.add_step_result(StepResult(
            step_id="step:1",
            step_name="Test Step",
            status=StepResultStatus.COMPLETED,
        ))
        
        md = report.to_markdown()
        
        self.assertIn("Test Scenario", md)
        self.assertIn("COMPLETED", md)
        self.assertIn("Test Step", md)


class TestStepResult(unittest.TestCase):
    """Tests for StepResult class"""

    def test_step_result_creation(self):
        """Test step result creation"""
        result = StepResult(
            step_id="step:1",
            step_name="Test Step",
            status=StepResultStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        
        self.assertEqual(result.step_id, "step:1")
        self.assertEqual(result.step_name, "Test Step")
        self.assertEqual(result.status, StepResultStatus.COMPLETED)

    def test_step_result_to_dict(self):
        """Test step result to_dict"""
        result = StepResult(
            step_id="step:1",
            step_name="Test Step",
            status=StepResultStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            error=None,
            result={"key": "value"},
            resource_ids={"github": "issue-123"},
            verification_status=True,
            verification_message="Verified",
            retry_count=0,
        )
        
        data = result.to_dict()
        
        self.assertIn("step_id", data)
        self.assertIn("step_name", data)
        self.assertIn("status", data)
        self.assertIn("resource_ids", data)


if __name__ == "__main__":
    unittest.main()
