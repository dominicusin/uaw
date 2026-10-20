"""
Tests for UAW Core Components
"""

import unittest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from uaw.core.uaw_core import UAWCore
from uaw.core.state_manager import StateManager, WorkflowState
from uaw.core.resource_mapping import ResourceMapper
from uaw.core.security import SecurityManager, PermissionLevel
from uaw.core.audit import AuditLogger, AuditEventType

from uaw.models.workflow import Workflow, WorkflowStep, WorkflowStepType, WorkflowStatus
from uaw.models.issue import Issue, IssueType, IssueSeverity, IssueStatus
from uaw.models.person import Person


class TestUAWCore(unittest.TestCase):
    """Tests for UAWCore class"""

    def setUp(self):
        self.core = UAWCore()

    def test_initialization(self):
        """Test UAWCore initialization"""
        self.assertIsNotNone(self.core)
        self.assertIsNotNone(self.core.state_manager)
        self.assertIsNotNone(self.core.resource_mapper)
        self.assertIsNotNone(self.core.security_manager)
        self.assertIsNotNone(self.core.audit_logger)

    def test_parse_request_natural_language(self):
        """Test natural language request parsing"""
        request = "Create a new issue in the project and assign it to John"
        result = self.core.parse_request(request)
        
        self.assertIn("intent", result)
        self.assertIn("entities", result)
        self.assertIn("actions", result)

    def test_parse_request_with_context(self):
        """Test request parsing with context"""
        request = "Fix the bug in the login system"
        context = {"project": "auth-service", "priority": "high"}
        result = self.core.parse_request(request, context)
        
        self.assertIsNotNone(result)

    def test_plan_workflow(self):
        """Test workflow planning"""
        request = "Create issue and notify team"
        workflow = self.core.plan_workflow(request)
        
        self.assertIsInstance(workflow, Workflow)
        self.assertGreater(len(workflow.steps), 0)

    @patch('uaw.core.uaw_core.UUID')
    def test_generate_workflow_id(self, mock_uuid):
        """Test workflow ID generation"""
        mock_uuid.uuid4.return_value = "test-uuid"
        workflow_id = self.core._generate_workflow_id()
        self.assertEqual(workflow_id, "workflow:test-uuid")


class TestStateManager(unittest.TestCase):
    """Tests for StateManager class"""

    def setUp(self):
        self.state_manager = StateManager()

    def test_save_state(self):
        """Test saving workflow state"""
        workflow_id = "test-workflow"
        state = WorkflowState(
            workflow_id=workflow_id,
            current_step="step-1",
            completed_steps=["step-1"],
            pending_steps=["step-2"],
            failed_steps=[],
            context={"key": "value"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        self.state_manager.save_state(workflow_id, state)
        saved_state = self.state_manager.get_state(workflow_id)
        
        self.assertIsNotNone(saved_state)
        self.assertEqual(saved_state.workflow_id, workflow_id)

    def test_get_nonexistent_state(self):
        """Test getting non-existent state"""
        state = self.state_manager.get_state("nonexistent")
        self.assertIsNone(state)

    def test_delete_state(self):
        """Test deleting state"""
        workflow_id = "test-workflow"
        state = WorkflowState(workflow_id=workflow_id)
        self.state_manager.save_state(workflow_id, state)
        
        self.state_manager.delete_state(workflow_id)
        deleted_state = self.state_manager.get_state(workflow_id)
        
        self.assertIsNone(deleted_state)

    def test_list_states(self):
        """Test listing all states"""
        workflow_ids = ["workflow-1", "workflow-2", "workflow-3"]
        for wf_id in workflow_ids:
            state = WorkflowState(workflow_id=wf_id)
            self.state_manager.save_state(wf_id, state)
        
        states = self.state_manager.list_states()
        self.assertEqual(len(states), len(workflow_ids))

    def test_cleanup_expired_states(self):
        """Test cleanup of expired states"""
        # Create expired state
        expired_state = WorkflowState(
            workflow_id="expired",
            created_at=datetime.utcnow() - timedelta(days=31),
        )
        self.state_manager.save_state("expired", expired_state)
        
        # Create valid state
        valid_state = WorkflowState(workflow_id="valid")
        self.state_manager.save_state("valid", valid_state)
        
        # Cleanup
        self.state_manager.cleanup_expired_states(ttl_days=30)
        
        self.assertIsNone(self.state_manager.get_state("expired"))
        self.assertIsNotNone(self.state_manager.get_state("valid"))


class TestResourceMapper(unittest.TestCase):
    """Tests for ResourceMapper class"""

    def setUp(self):
        self.mapper = ResourceMapper()

    def test_generate_uaw_id(self):
        """Test UAW ID generation"""
        uaw_id = self.mapper.generate_uaw_id("issue", "github")
        self.assertTrue(uaw_id.startswith("issue:"))
        self.assertIn("github", uaw_id)

    def test_link_resources(self):
        """Test linking resources"""
        uaw_id = self.mapper.generate_uaw_id("issue", "github")
        external_id = "github-issue-123"
        
        self.mapper.link_resources(uaw_id, external_id, "github")
        
        # Check forward mapping
        self.assertEqual(self.mapper.get_external_id(uaw_id, "github"), external_id)
        
        # Check reverse mapping
        self.assertEqual(self.mapper.get_uaw_id(external_id, "github"), uaw_id)

    def test_get_nonexistent_mapping(self):
        """Test getting non-existent mapping"""
        result = self.mapper.get_external_id("nonexistent", "github")
        self.assertIsNone(result)

    def test_unlink_resources(self):
        """Test unlinking resources"""
        uaw_id = self.mapper.generate_uaw_id("issue", "github")
        external_id = "github-issue-123"
        
        self.mapper.link_resources(uaw_id, external_id, "github")
        self.mapper.unlink_resources(uaw_id, external_id, "github")
        
        self.assertIsNone(self.mapper.get_external_id(uaw_id, "github"))

    def test_sync_across_services(self):
        """Test synchronization across services"""
        # Create mappings for same resource in different services
        uaw_id = self.mapper.generate_uaw_id("issue", "uaw")
        self.mapper.link_resources(uaw_id, "github-123", "github")
        self.mapper.link_resources(uaw_id, "asana-456", "asana")
        self.mapper.link_resources(uaw_id, "linear-789", "linear")
        
        # Get all external IDs
        external_ids = self.mapper.get_all_external_ids(uaw_id)
        
        self.assertEqual(len(external_ids), 3)
        self.assertIn("github-123", external_ids.values())


class TestSecurityManager(unittest.TestCase):
    """Tests for SecurityManager class"""

    def setUp(self):
        self.security = SecurityManager()

    def test_check_permission_L0(self):
        """Test L0 permission check"""
        # L0 allows read-only actions
        result = asyncio.run(self.security.check_permission(
            user_id="user1",
            action="list_repositories",
            integration="github",
        ))
        self.assertTrue(result)

    def test_check_permission_L4(self):
        """Test L4 permission check"""
        # L4 requires explicit confirmation
        result = asyncio.run(self.security.check_permission(
            user_id="user1",
            action="delete_production",
            integration="github",
        ))
        # Should be False by default for L4
        self.assertFalse(result)

    def test_generate_session_token(self):
        """Test session token generation"""
        token = self.security.generate_session_token("user1")
        self.assertIsNotNone(token)
        self.assertTrue(len(token) > 10)

    def test_validate_session_token(self):
        """Test session token validation"""
        token = self.security.generate_session_token("user1")
        is_valid = self.security.validate_session_token(token)
        self.assertTrue(is_valid)

    def test_invalidate_session_token(self):
        """Test session token invalidation"""
        token = self.security.generate_session_token("user1")
        self.security.invalidate_session_token(token)
        is_valid = self.security.validate_session_token(token)
        self.assertFalse(is_valid)

    def test_get_permission_level(self):
        """Test getting permission level"""
        level = self.security.get_permission_level("user1", "github")
        self.assertEqual(level, PermissionLevel.L0_READ_ONLY)


class TestAuditLogger(unittest.TestCase):
    """Tests for AuditLogger class"""

    def setUp(self):
        self.audit = AuditLogger()

    def test_log_event(self):
        """Test logging an event"""
        event = MagicMock()
        event.event_type = AuditEventType.WORKFLOW_STARTED
        event.resource_type = "workflow"
        event.resource_id = "workflow-123"
        event.action = "start"
        event.status = "success"
        event.details = {}
        event.timestamp = datetime.utcnow()
        
        asyncio.run(self.audit.log_event(event))
        
        # Check that event was logged
        self.assertGreater(len(self.audit.events), 0)

    def test_get_events(self):
        """Test getting logged events"""
        event = MagicMock()
        event.event_type = AuditEventType.WORKFLOW_STARTED
        event.resource_type = "workflow"
        event.resource_id = "workflow-123"
        event.action = "start"
        event.status = "success"
        event.details = {}
        event.timestamp = datetime.utcnow()
        
        asyncio.run(self.audit.log_event(event))
        
        events = self.audit.get_events(resource_type="workflow")
        self.assertGreater(len(events), 0)

    def test_rotate_logs(self):
        """Test log rotation"""
        # Add multiple events
        for i in range(100):
            event = MagicMock()
            event.event_type = AuditEventType.WORKFLOW_STARTED
            event.resource_type = "workflow"
            event.resource_id = f"workflow-{i}"
            event.action = "start"
            event.status = "success"
            event.details = {}
            event.timestamp = datetime.utcnow()
            asyncio.run(self.audit.log_event(event))
        
        # Rotate logs
        self.audit.rotate_logs(max_events=50)
        
        events = self.audit.get_events()
        self.assertLessEqual(len(events), 50)


if __name__ == "__main__":
    unittest.main()
