"""
UAW Automation Module Tests

Comprehensive tests for the automation module including:
- EventManager
- WebhookServer
- TriggerManager
- AutomationEngine
"""

import unittest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from uaw.automation.event_manager import EventManager, Event, EventType, EventStatus
from uaw.automation.webhook_server import WebhookServer, WebhookPayload, WebhookConfig
from uaw.automation.trigger import TriggerManager, Trigger, TriggerType, TriggerCondition
from uaw.automation.automation_engine import AutomationEngine, AutomationRule, AutomationWorkflow
from uaw.models.base import UAWIdentifier
from uaw.core.audit import AuditEventType


class TestEventManager(unittest.TestCase):
    """Tests for EventManager class"""

    def setUp(self):
        self.event_manager = EventManager()
        self.test_event_id = "test_event_001"
        self.test_event = Event(
            uaw_id=self.test_event_id,
            event_type=EventType.GITHUB_ISSUE_CREATED,
            resource_type="issue",
            resource_id="issue_123",
            source="github",
            payload={"action": "opened", "issue": {"number": 123}},
            timestamp=datetime.utcnow().isoformat()
        )

    def test_event_creation(self):
        """Test creating an event"""
        self.assertEqual(self.test_event.uaw_id, self.test_event_id)
        self.assertEqual(self.test_event.event_type, EventType.GITHUB_ISSUE_CREATED)
        self.assertEqual(self.test_event.resource_type, "issue")
        self.assertEqual(self.test_event.source, "github")

    def test_event_to_dict(self):
        """Test event serialization"""
        event_dict = self.test_event.to_dict()
        self.assertIn("uaw_id", event_dict)
        self.assertIn("event_type", event_dict)
        self.assertIn("resource_type", event_dict)
        self.assertIn("source", event_dict)
        self.assertIn("payload", event_dict)
        self.assertIn("timestamp", event_dict)

    def test_event_from_dict(self):
        """Test event deserialization"""
        event_dict = self.test_event.to_dict()
        restored_event = Event.from_dict(event_dict)
        self.assertEqual(restored_event.uaw_id, self.test_event.uaw_id)
        self.assertEqual(restored_event.event_type, self.test_event.event_type)

    def test_add_event(self):
        """Test adding an event to the manager"""
        self.event_manager.add_event(self.test_event)
        self.assertEqual(len(self.event_manager._events), 1)
        self.assertIn(self.test_event_id, self.event_manager._events)

    def test_deduplication(self):
        """Test event deduplication"""
        # Add the same event twice
        self.event_manager.add_event(self.test_event)
        self.event_manager.add_event(self.test_event)
        # Should only have one event due to deduplication
        self.assertEqual(len(self.event_manager._events), 1)

    def test_deduplication_different_events(self):
        """Test that different events are not deduplicated"""
        event2 = Event(
            uaw_id="test_event_002",
            event_type=EventType.GITHUB_ISSUE_CREATED,
            resource_type="issue",
            resource_id="issue_456",
            source="github",
            payload={"action": "opened", "issue": {"number": 456}},
            timestamp=datetime.utcnow().isoformat()
        )
        self.event_manager.add_event(self.test_event)
        self.event_manager.add_event(event2)
        self.assertEqual(len(self.event_manager._events), 2)

    def test_get_event(self):
        """Test retrieving an event"""
        self.event_manager.add_event(self.test_event)
        retrieved = self.event_manager.get_event(self.test_event_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.uaw_id, self.test_event_id)

    def test_get_nonexistent_event(self):
        """Test retrieving a non-existent event"""
        retrieved = self.event_manager.get_event("nonexistent")
        self.assertIsNone(retrieved)

    def test_remove_event(self):
        """Test removing an event"""
        self.event_manager.add_event(self.test_event)
        self.assertIn(self.test_event_id, self.event_manager._events)
        self.event_manager.remove_event(self.test_event_id)
        self.assertNotIn(self.test_event_id, self.event_manager._events)

    def test_list_events(self):
        """Test listing all events"""
        event2 = Event(
            uaw_id="test_event_002",
            event_type=EventType.SLACK_MESSAGE_RECEIVED,
            resource_type="message",
            resource_id="msg_123",
            source="slack",
            payload={"text": "test"},
            timestamp=datetime.utcnow().isoformat()
        )
        self.event_manager.add_event(self.test_event)
        self.event_manager.add_event(event2)
        events = self.event_manager.list_events()
        self.assertEqual(len(events), 2)

    def test_list_events_by_type(self):
        """Test filtering events by type"""
        event2 = Event(
            uaw_id="test_event_002",
            event_type=EventType.SLACK_MESSAGE_RECEIVED,
            resource_type="message",
            resource_id="msg_123",
            source="slack",
            payload={"text": "test"},
            timestamp=datetime.utcnow().isoformat()
        )
        self.event_manager.add_event(self.test_event)
        self.event_manager.add_event(event2)
        github_events = self.event_manager.list_events(
            event_type=EventType.GITHUB_ISSUE_CREATED
        )
        self.assertEqual(len(github_events), 1)
        self.assertEqual(github_events[0].event_type, EventType.GITHUB_ISSUE_CREATED)

    def test_list_events_by_source(self):
        """Test filtering events by source"""
        event2 = Event(
            uaw_id="test_event_002",
            event_type=EventType.GITHUB_ISSUE_CREATED,
            resource_type="issue",
            resource_id="issue_456",
            source="gitlab",
            payload={"action": "opened"},
            timestamp=datetime.utcnow().isoformat()
        )
        self.event_manager.add_event(self.test_event)
        self.event_manager.add_event(event2)
        github_events = self.event_manager.list_events(source="github")
        self.assertEqual(len(github_events), 1)
        self.assertEqual(github_events[0].source, "github")

    def test_event_expiration(self):
        """Test event expiration based on TTL"""
        old_timestamp = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        old_event = Event(
            uaw_id="old_event",
            event_type=EventType.GITHUB_ISSUE_CREATED,
            resource_type="issue",
            resource_id="issue_old",
            source="github",
            payload={"action": "opened"},
            timestamp=old_timestamp
        )
        self.event_manager.add_event(old_event)
        self.event_manager.add_event(self.test_event)
        
        # Clean up expired events (TTL is 1 hour by default)
        self.event_manager._cleanup_expired_events()
        
        # Old event should be removed
        self.assertNotIn("old_event", self.event_manager._events)
        # Recent event should remain
        self.assertIn(self.test_event_id, self.event_manager._events)

    def test_event_status(self):
        """Test event status transitions"""
        self.assertEqual(self.test_event.status, EventStatus.PENDING)
        self.test_event.mark_processed()
        self.assertEqual(self.test_event.status, EventStatus.PROCESSED)
        self.test_event.mark_failed("Test error")
        self.assertEqual(self.test_event.status, EventStatus.FAILED)
        self.assertEqual(self.test_event.error_message, "Test error")


class TestWebhookServer(unittest.TestCase):
    """Tests for WebhookServer class"""

    def setUp(self):
        self.webhook_server = WebhookServer()
        self.test_payload = {
            "action": "opened",
            "issue": {"number": 123, "title": "Test issue"},
            "repository": {"name": "test-repo"}
        }
        self.test_signature = "sha256=test_signature"
        self.test_config = WebhookConfig(
            secret="test_secret",
            path="/webhook/github",
            allowed_sources=["github"]
        )

    def test_webhook_payload_creation(self):
        """Test creating a webhook payload"""
        payload = WebhookPayload(
            source="github",
            event_type="issues",
            payload=self.test_payload,
            signature=self.test_signature,
            timestamp=datetime.utcnow().isoformat()
        )
        self.assertEqual(payload.source, "github")
        self.assertEqual(payload.event_type, "issues")
        self.assertEqual(payload.payload, self.test_payload)

    def test_verify_signature_success(self):
        """Test signature verification success"""
        # Mock the hash computation
        with patch('hashlib.sha256') as mock_sha256:
            mock_hash = MagicMock()
            mock_hash.hexdigest.return_value = "test_hash"
            mock_sha256.return_value = mock_hash
            
            config = WebhookConfig(
                secret="test_secret",
                path="/webhook",
                allowed_sources=["github"]
            )
            
            result = config.verify_signature(
                payload=self.test_payload,
                signature="sha256=test_hash"
            )
            self.assertTrue(result)

    def test_verify_signature_failure(self):
        """Test signature verification failure"""
        config = WebhookConfig(
            secret="test_secret",
            path="/webhook",
            allowed_sources=["github"]
        )
        
        result = config.verify_signature(
            payload=self.test_payload,
            signature="sha256=wrong_hash"
        )
        self.assertFalse(result)

    def test_register_webhook_handler(self):
        """Test registering a webhook handler"""
        async def test_handler(payload):
            return {"status": "ok"}
        
        self.webhook_server.register_handler("github", test_handler)
        self.assertIn("github", self.webhook_server._handlers)

    def test_process_webhook(self):
        """Test processing a webhook"""
        async def test_handler(payload):
            return {"status": "processed"}
        
        self.webhook_server.register_handler("github", test_handler)
        
        payload = WebhookPayload(
            source="github",
            event_type="issues",
            payload=self.test_payload,
            signature=self.test_signature
        )
        
        # Run the async method
        result = asyncio.run(self.webhook_server.process_webhook(payload))
        self.assertEqual(result["status"], "processed")

    def test_process_webhook_no_handler(self):
        """Test processing a webhook with no handler"""
        payload = WebhookPayload(
            source="unknown",
            event_type="issues",
            payload=self.test_payload,
            signature=self.test_signature
        )
        
        result = asyncio.run(self.webhook_server.process_webhook(payload))
        self.assertEqual(result["status"], "error")
        self.assertIn("No handler", result["error"])

    def test_start_server(self):
        """Test starting the webhook server"""
        # This is a basic test - full server testing would require HTTP requests
        self.webhook_server.start()
        self.assertTrue(self.webhook_server._running)
        self.webhook_server.stop()
        self.assertFalse(self.webhook_server._running)


class TestTriggerManager(unittest.TestCase):
    """Tests for TriggerManager class"""

    def setUp(self):
        self.trigger_manager = TriggerManager()
        self.test_trigger_id = "trigger_001"

    def test_trigger_creation(self):
        """Test creating a trigger"""
        trigger = Trigger(
            uaw_id=self.test_trigger_id,
            name="Test Trigger",
            trigger_type=TriggerType.WEBHOOK,
            source="github",
            event_type="issues",
            conditions=[
                TriggerCondition(
                    field="action",
                    operator="equals",
                    value="opened"
                )
            ],
            is_active=True
        )
        self.assertEqual(trigger.uaw_id, self.test_trigger_id)
        self.assertEqual(trigger.trigger_type, TriggerType.WEBHOOK)
        self.assertEqual(trigger.source, "github")
        self.assertEqual(len(trigger.conditions), 1)

    def test_trigger_to_dict(self):
        """Test trigger serialization"""
        trigger = Trigger(
            uaw_id=self.test_trigger_id,
            name="Test Trigger",
            trigger_type=TriggerType.SCHEDULED,
            source="cron",
            schedule="0 * * * *"
        )
        trigger_dict = trigger.to_dict()
        self.assertIn("uaw_id", trigger_dict)
        self.assertIn("name", trigger_dict)
        self.assertIn("trigger_type", trigger_dict)
        self.assertIn("source", trigger_dict)

    def test_trigger_from_dict(self):
        """Test trigger deserialization"""
        trigger = Trigger(
            uaw_id=self.test_trigger_id,
            name="Test Trigger",
            trigger_type=TriggerType.SCHEDULED,
            source="cron",
            schedule="0 * * * *"
        )
        trigger_dict = trigger.to_dict()
        restored = Trigger.from_dict(trigger_dict)
        self.assertEqual(restored.uaw_id, trigger.uaw_id)
        self.assertEqual(restored.name, trigger.name)
        self.assertEqual(restored.trigger_type, trigger.trigger_type)

    def test_register_trigger(self):
        """Test registering a trigger"""
        trigger = Trigger(
            uaw_id=self.test_trigger_id,
            name="Test Trigger",
            trigger_type=TriggerType.WEBHOOK,
            source="github"
        )
        self.trigger_manager.register_trigger(trigger)
        self.assertEqual(len(self.trigger_manager._triggers), 1)
        self.assertIn(self.test_trigger_id, self.trigger_manager._triggers)

    def test_get_trigger(self):
        """Test retrieving a trigger"""
        trigger = Trigger(
            uaw_id=self.test_trigger_id,
            name="Test Trigger",
            trigger_type=TriggerType.WEBHOOK,
            source="github"
        )
        self.trigger_manager.register_trigger(trigger)
        retrieved = self.trigger_manager.get_trigger(self.test_trigger_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.uaw_id, self.test_trigger_id)

    def test_remove_trigger(self):
        """Test removing a trigger"""
        trigger = Trigger(
            uaw_id=self.test_trigger_id,
            name="Test Trigger",
            trigger_type=TriggerType.WEBHOOK,
            source="github"
        )
        self.trigger_manager.register_trigger(trigger)
        self.trigger_manager.remove_trigger(self.test_trigger_id)
        self.assertEqual(len(self.trigger_manager._triggers), 0)

    def test_list_triggers(self):
        """Test listing all triggers"""
        trigger1 = Trigger(
            uaw_id="trigger_001",
            name="Trigger 1",
            trigger_type=TriggerType.WEBHOOK,
            source="github"
        )
        trigger2 = Trigger(
            uaw_id="trigger_002",
            name="Trigger 2",
            trigger_type=TriggerType.SCHEDULED,
            source="cron"
        )
        self.trigger_manager.register_trigger(trigger1)
        self.trigger_manager.register_trigger(trigger2)
        triggers = self.trigger_manager.list_triggers()
        self.assertEqual(len(triggers), 2)

    def test_evaluate_condition_equals(self):
        """Test condition evaluation with equals operator"""
        condition = TriggerCondition(
            field="action",
            operator="equals",
            value="opened"
        )
        payload = {"action": "opened"}
        self.assertTrue(condition.evaluate(payload))
        
        payload2 = {"action": "closed"}
        self.assertFalse(condition.evaluate(payload2))

    def test_evaluate_condition_not_equals(self):
        """Test condition evaluation with not_equals operator"""
        condition = TriggerCondition(
            field="action",
            operator="not_equals",
            value="closed"
        )
        payload = {"action": "opened"}
        self.assertTrue(condition.evaluate(payload))
        
        payload2 = {"action": "closed"}
        self.assertFalse(condition.evaluate(payload2))

    def test_evaluate_condition_contains(self):
        """Test condition evaluation with contains operator"""
        condition = TriggerCondition(
            field="labels",
            operator="contains",
            value="bug"
        )
        payload = {"labels": ["bug", "critical"]}
        self.assertTrue(condition.evaluate(payload))
        
        payload2 = {"labels": ["feature", "enhancement"]}
        self.assertFalse(condition.evaluate(payload2))

    def test_evaluate_condition_greater_than(self):
        """Test condition evaluation with greater_than operator"""
        condition = TriggerCondition(
            field="priority",
            operator="greater_than",
            value=2
        )
        payload = {"priority": 3}
        self.assertTrue(condition.evaluate(payload))
        
        payload2 = {"priority": 1}
        self.assertFalse(condition.evaluate(payload2))

    def test_trigger_matching(self):
        """Test trigger matching with event"""
        trigger = Trigger(
            uaw_id=self.test_trigger_id,
            name="GitHub Issue Opened",
            trigger_type=TriggerType.WEBHOOK,
            source="github",
            event_type="issues",
            conditions=[
                TriggerCondition(
                    field="action",
                    operator="equals",
                    value="opened"
                )
            ]
        )
        self.trigger_manager.register_trigger(trigger)
        
        # Matching event
        event = {
            "source": "github",
            "event_type": "issues",
            "payload": {"action": "opened"}
        }
        matching = self.trigger_manager.find_matching_triggers(event)
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].uaw_id, self.test_trigger_id)

    def test_trigger_not_matching(self):
        """Test trigger not matching with event"""
        trigger = Trigger(
            uaw_id=self.test_trigger_id,
            name="GitHub Issue Opened",
            trigger_type=TriggerType.WEBHOOK,
            source="github",
            event_type="issues",
            conditions=[
                TriggerCondition(
                    field="action",
                    operator="equals",
                    value="opened"
                )
            ]
        )
        self.trigger_manager.register_trigger(trigger)
        
        # Non-matching event
        event = {
            "source": "github",
            "event_type": "issues",
            "payload": {"action": "closed"}
        }
        matching = self.trigger_manager.find_matching_triggers(event)
        self.assertEqual(len(matching), 0)


class TestAutomationEngine(unittest.TestCase):
    """Tests for AutomationEngine class"""

    def setUp(self):
        self.automation_engine = AutomationEngine()
        self.event_manager = EventManager()
        self.trigger_manager = TriggerManager()
        
        # Setup automation engine with dependencies
        self.automation_engine.event_manager = self.event_manager
        self.automation_engine.trigger_manager = self.trigger_manager

    def test_automation_rule_creation(self):
        """Test creating an automation rule"""
        rule = AutomationRule(
            uaw_id="rule_001",
            name="Auto Assign Bugs",
            trigger_type=TriggerType.WEBHOOK,
            source="github",
            event_type="issues",
            conditions=[
                {"field": "labels", "operator": "contains", "value": "bug"}
            ],
            actions=[
                {"type": "linear", "action": "create_issue"},
                {"type": "linear", "action": "assign_user", "user": "dev-team"}
            ],
            is_active=True
        )
        self.assertEqual(rule.uaw_id, "rule_001")
        self.assertEqual(rule.name, "Auto Assign Bugs")
        self.assertEqual(len(rule.conditions), 1)
        self.assertEqual(len(rule.actions), 2)

    def test_automation_workflow_creation(self):
        """Test creating an automation workflow"""
        workflow = AutomationWorkflow(
            uaw_id="workflow_001",
            name="Bug Fix Workflow",
            description="Automated bug fix process",
            triggers=[
                Trigger(
                    uaw_id="trigger_001",
                    name="GitHub Bug Issue",
                    trigger_type=TriggerType.WEBHOOK,
                    source="github",
                    event_type="issues"
                )
            ],
            rules=[
                AutomationRule(
                    uaw_id="rule_001",
                    name="Create Linear Task",
                    trigger_type=TriggerType.WEBHOOK,
                    source="github",
                    actions=[{"type": "linear", "action": "create_issue"}]
                )
            ]
        )
        self.assertEqual(workflow.uaw_id, "workflow_001")
        self.assertEqual(len(workflow.triggers), 1)
        self.assertEqual(len(workflow.rules), 1)

    def test_add_rule(self):
        """Test adding an automation rule"""
        rule = AutomationRule(
            uaw_id="rule_001",
            name="Test Rule",
            trigger_type=TriggerType.WEBHOOK,
            source="github",
            actions=[{"type": "test", "action": "test"}]
        )
        self.automation_engine.add_rule(rule)
        self.assertEqual(len(self.automation_engine._rules), 1)

    def test_add_workflow(self):
        """Test adding an automation workflow"""
        workflow = AutomationWorkflow(
            uaw_id="workflow_001",
            name="Test Workflow",
            triggers=[],
            rules=[]
        )
        self.automation_engine.add_workflow(workflow)
        self.assertEqual(len(self.automation_engine._workflows), 1)

    def test_get_rule(self):
        """Test retrieving an automation rule"""
        rule = AutomationRule(
            uaw_id="rule_001",
            name="Test Rule",
            trigger_type=TriggerType.WEBHOOK,
            source="github",
            actions=[]
        )
        self.automation_engine.add_rule(rule)
        retrieved = self.automation_engine.get_rule("rule_001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.uaw_id, "rule_001")

    def test_get_workflow(self):
        """Test retrieving an automation workflow"""
        workflow = AutomationWorkflow(
            uaw_id="workflow_001",
            name="Test Workflow",
            triggers=[],
            rules=[]
        )
        self.automation_engine.add_workflow(workflow)
        retrieved = self.automation_engine.get_workflow("workflow_001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.uaw_id, "workflow_001")

    def test_remove_rule(self):
        """Test removing an automation rule"""
        rule = AutomationRule(
            uaw_id="rule_001",
            name="Test Rule",
            trigger_type=TriggerType.WEBHOOK,
            source="github",
            actions=[]
        )
        self.automation_engine.add_rule(rule)
        self.automation_engine.remove_rule("rule_001")
        self.assertEqual(len(self.automation_engine._rules), 0)

    def test_remove_workflow(self):
        """Test removing an automation workflow"""
        workflow = AutomationWorkflow(
            uaw_id="workflow_001",
            name="Test Workflow",
            triggers=[],
            rules=[]
        )
        self.automation_engine.add_workflow(workflow)
        self.automation_engine.remove_workflow("workflow_001")
        self.assertEqual(len(self.automation_engine._workflows), 0)

    def test_list_rules(self):
        """Test listing all automation rules"""
        rule1 = AutomationRule(
            uaw_id="rule_001",
            name="Rule 1",
            trigger_type=TriggerType.WEBHOOK,
            source="github",
            actions=[]
        )
        rule2 = AutomationRule(
            uaw_id="rule_002",
            name="Rule 2",
            trigger_type=TriggerType.SCHEDULED,
            source="cron",
            actions=[]
        )
        self.automation_engine.add_rule(rule1)
        self.automation_engine.add_rule(rule2)
        rules = self.automation_engine.list_rules()
        self.assertEqual(len(rules), 2)

    def test_list_workflows(self):
        """Test listing all automation workflows"""
        workflow1 = AutomationWorkflow(
            uaw_id="workflow_001",
            name="Workflow 1",
            triggers=[],
            rules=[]
        )
        workflow2 = AutomationWorkflow(
            uaw_id="workflow_002",
            name="Workflow 2",
            triggers=[],
            rules=[]
        )
        self.automation_engine.add_workflow(workflow1)
        self.automation_engine.add_workflow(workflow2)
        workflows = self.automation_engine.list_workflows()
        self.assertEqual(len(workflows), 2)

    def test_enable_disable_rule(self):
        """Test enabling and disabling a rule"""
        rule = AutomationRule(
            uaw_id="rule_001",
            name="Test Rule",
            trigger_type=TriggerType.WEBHOOK,
            source="github",
            is_active=True,
            actions=[]
        )
        self.automation_engine.add_rule(rule)
        
        self.automation_engine.disable_rule("rule_001")
        retrieved = self.automation_engine.get_rule("rule_001")
        self.assertFalse(retrieved.is_active)
        
        self.automation_engine.enable_rule("rule_001")
        retrieved = self.automation_engine.get_rule("rule_001")
        self.assertTrue(retrieved.is_active)

    def test_start_stop_engine(self):
        """Test starting and stopping the automation engine"""
        self.automation_engine.start()
        self.assertTrue(self.automation_engine._running)
        
        self.automation_engine.stop()
        self.assertFalse(self.automation_engine._running)


class TestAutomationIntegration(unittest.TestCase):
    """Integration tests for automation components working together"""

    def test_full_automation_flow(self):
        """Test a complete automation flow from event to action"""
        # Setup
        event_manager = EventManager()
        trigger_manager = TriggerManager()
        automation_engine = AutomationEngine()
        
        automation_engine.event_manager = event_manager
        automation_engine.trigger_manager = trigger_manager
        
        # Create a trigger
        trigger = Trigger(
            uaw_id="trigger_001",
            name="GitHub Issue Trigger",
            trigger_type=TriggerType.WEBHOOK,
            source="github",
            event_type="issues",
            conditions=[
                TriggerCondition(
                    field="action",
                    operator="equals",
                    value="opened"
                )
            ]
        )
        trigger_manager.register_trigger(trigger)
        
        # Create an automation rule
        rule = AutomationRule(
            uaw_id="rule_001",
            name="Create Linear Task",
            trigger_type=TriggerType.WEBHOOK,
            source="github",
            event_type="issues",
            conditions=[
                {"field": "action", "operator": "equals", "value": "opened"}
            ],
            actions=[
                {"type": "linear", "action": "create_issue", "title": "New GitHub Issue"}
            ]
        )
        automation_engine.add_rule(rule)
        
        # Add an event
        event = Event(
            uaw_id="event_001",
            event_type=EventType.GITHUB_ISSUE_CREATED,
            resource_type="issue",
            resource_id="issue_123",
            source="github",
            payload={"action": "opened", "issue": {"number": 123}}
        )
        event_manager.add_event(event)
        
        # Verify event was added
        self.assertEqual(len(event_manager._events), 1)
        
        # Verify trigger matches
        matching_triggers = trigger_manager.find_matching_triggers({
            "source": "github",
            "event_type": "issues",
            "payload": {"action": "opened"}
        })
        self.assertEqual(len(matching_triggers), 1)
        
        # Verify rule exists
        self.assertEqual(len(automation_engine._rules), 1)


if __name__ == '__main__':
    unittest.main()
