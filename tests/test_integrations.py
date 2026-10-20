"""
Tests for UAW Integrations
"""

import unittest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from uaw.integrations.base import BaseIntegration, IntegrationConfig, IntegrationResult
from uaw.integrations.registry import IntegrationRegistry
from uaw.integrations.github_integration import GitHubIntegration
from uaw.integrations.asana_integration import AsanaIntegration
from uaw.integrations.linear_integration import LinearIntegration
from uaw.integrations.calendar_integration import CalendarIntegration
from uaw.integrations.netlify_integration import NetlifyIntegration
from uaw.integrations.box_integration import BoxIntegration
from uaw.integrations.notion_integration import NotionIntegration
from uaw.integrations.slack_integration import SlackIntegration
from uaw.integrations.document_library_integration import DocumentLibraryIntegration

from uaw.models.integration import Integration, IntegrationStatus, IntegrationCapability


class TestBaseIntegration(unittest.TestCase):
    """Tests for BaseIntegration class"""

    def setUp(self):
        self.config = IntegrationConfig(
            integration_id="test-integration",
            name="Test Integration",
            service="test",
            base_url="https://api.test.com",
            api_key=None,
            access_token=None,
            rate_limit=100,
            timeout=30,
        )
        self.integration = BaseIntegration(self.config)

    def test_initialization(self):
        """Test BaseIntegration initialization"""
        self.assertEqual(self.integration.name, "Test Integration")
        self.assertEqual(self.integration.service, "test")
        self.assertEqual(self.integration.base_url, "https://api.test.com")

    def test_health_check(self):
        """Test health check"""
        # В реальности это проверял бы подключение к API
        # Для теста просто проверяем, что метод существует
        self.assertTrue(hasattr(self.integration, 'check_health'))

    def test_get_capabilities(self):
        """Test getting capabilities"""
        capabilities = self.integration.get_capabilities()
        self.assertIsInstance(capabilities, list)

    def test_get_rate_limits(self):
        """Test getting rate limits"""
        limits = self.integration.get_rate_limits()
        self.assertIsInstance(limits, list)


class TestIntegrationRegistry(unittest.TestCase):
    """Tests for IntegrationRegistry class"""

    def setUp(self):
        self.registry = IntegrationRegistry()

    def test_register_integration(self):
        """Test registering an integration"""
        config = IntegrationConfig(
            integration_id="test-1",
            name="Test 1",
            service="test1",
        )
        integration = BaseIntegration(config)
        
        self.registry.register_integration(integration)
        
        retrieved = self.registry.get_integration("test1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test 1")

    def test_get_integration_by_service(self):
        """Test getting integration by service"""
        config = IntegrationConfig(
            integration_id="test-2",
            name="Test 2",
            service="test2",
        )
        integration = BaseIntegration(config)
        self.registry.register_integration(integration)
        
        retrieved = self.registry.get_integration_by_service("test2")
        self.assertIsNotNone(retrieved)

    def test_list_integrations(self):
        """Test listing all integrations"""
        configs = [
            IntegrationConfig(integration_id=f"test-{i}", name=f"Test {i}", service=f"test{i}")
            for i in range(3)
        ]
        
        for config in configs:
            self.registry.register_integration(BaseIntegration(config))
        
        all_integrations = self.registry.list_integrations()
        self.assertEqual(len(all_integrations), 3)

    def test_list_integrations_by_status(self):
        """Test listing integrations by status"""
        # Создаем интеграции с разными статусами
        config1 = IntegrationConfig(integration_id="test-1", name="Test 1", service="test1")
        config1.status = IntegrationStatus.CONNECTED
        
        config2 = IntegrationConfig(integration_id="test-2", name="Test 2", service="test2")
        config2.status = IntegrationStatus.DISCONNECTED
        
        self.registry.register_integration(BaseIntegration(config1))
        self.registry.register_integration(BaseIntegration(config2))
        
        connected = self.registry.list_integrations_by_status(IntegrationStatus.CONNECTED)
        self.assertEqual(len(connected), 1)


class TestGitHubIntegration(unittest.TestCase):
    """Tests for GitHubIntegration class"""

    def setUp(self):
        self.github = GitHubIntegration()

    def test_initialization(self):
        """Test GitHubIntegration initialization"""
        self.assertEqual(self.github.name, "GitHub")
        self.assertEqual(self.github.service, "github")

    def test_get_capabilities(self):
        """Test getting GitHub capabilities"""
        capabilities = self.github.get_capabilities()
        self.assertGreater(len(capabilities), 0)
        
        # Проверяем, что есть нужные возможности
        capability_names = [cap.name for cap in capabilities]
        self.assertIn("list_repositories", capability_names)
        self.assertIn("create_issue", capability_names)

    def test_get_rate_limits(self):
        """Test getting GitHub rate limits"""
        limits = self.github.get_rate_limits()
        self.assertGreater(len(limits), 0)

    def test_get_integration_by_service(self):
        """Test getting GitHub integration by service"""
        registry = IntegrationRegistry()
        registry.register_integration(self.github)
        
        retrieved = registry.get_integration_by_service("github")
        self.assertIsNotNone(retrieved)


class TestAsanaIntegration(unittest.TestCase):
    """Tests for AsanaIntegration class"""

    def setUp(self):
        self.asana = AsanaIntegration()

    def test_initialization(self):
        """Test AsanaIntegration initialization"""
        self.assertEqual(self.asana.name, "Asana")
        self.assertEqual(self.asana.service, "asana")

    def test_get_capabilities(self):
        """Test getting Asana capabilities"""
        capabilities = self.asana.get_capabilities()
        self.assertGreater(len(capabilities), 0)
        
        capability_names = [cap.name for cap in capabilities]
        self.assertIn("list_tasks", capability_names)
        self.assertIn("create_task", capability_names)


class TestLinearIntegration(unittest.TestCase):
    """Tests for LinearIntegration class"""

    def setUp(self):
        self.linear = LinearIntegration()

    def test_initialization(self):
        """Test LinearIntegration initialization"""
        self.assertEqual(self.linear.name, "Linear")
        self.assertEqual(self.linear.service, "linear")

    def test_get_capabilities(self):
        """Test getting Linear capabilities"""
        capabilities = self.linear.get_capabilities()
        self.assertGreater(len(capabilities), 0)


class TestCalendarIntegration(unittest.TestCase):
    """Tests for CalendarIntegration class"""

    def setUp(self):
        self.calendar = CalendarIntegration()

    def test_initialization(self):
        """Test CalendarIntegration initialization"""
        self.assertEqual(self.calendar.name, "Calendar")

    def test_get_capabilities(self):
        """Test getting Calendar capabilities"""
        capabilities = self.calendar.get_capabilities()
        self.assertGreater(len(capabilities), 0)


class TestIntegrationResult(unittest.TestCase):
    """Tests for IntegrationResult class"""

    def test_success_result(self):
        """Test successful integration result"""
        result = IntegrationResult(
            success=True,
            data={"id": "123", "name": "Test"},
            message="Operation successful",
            status_code=200,
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["id"], "123")
        self.assertEqual(result.message, "Operation successful")

    def test_failed_result(self):
        """Test failed integration result"""
        result = IntegrationResult(
            success=False,
            data={},
            message="Operation failed",
            status_code=400,
            error="Invalid parameters",
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Invalid parameters")

    def test_to_dict(self):
        """Test IntegrationResult to_dict"""
        result = IntegrationResult(
            success=True,
            data={"key": "value"},
            message="OK",
            status_code=200,
        )
        
        data = result.to_dict()
        self.assertIn("success", data)
        self.assertIn("data", data)
        self.assertIn("message", data)


class TestIntegrationModels(unittest.TestCase):
    """Tests for Integration models"""

    def test_integration_creation(self):
        """Test Integration creation"""
        integration = Integration(
            uaw_id="integration:123",
            name="GitHub",
            service="github",
            status=IntegrationStatus.CONNECTED,
            base_url="https://api.github.com",
        )
        
        self.assertEqual(integration.name, "GitHub")
        self.assertEqual(integration.service, "github")
        self.assertEqual(integration.status, IntegrationStatus.CONNECTED)

    def test_integration_to_dict(self):
        """Test Integration to_dict"""
        integration = Integration(
            uaw_id="integration:123",
            name="GitHub",
            service="github",
            status=IntegrationStatus.CONNECTED,
        )
        
        data = integration.to_dict()
        self.assertIn("uaw_id", data)
        self.assertIn("name", data)
        self.assertIn("service", data)

    def test_integration_capability_creation(self):
        """Test IntegrationCapability creation"""
        capability = IntegrationCapability(
            capability_id="cap:123",
            integration_id="integration:1",
            name="list_repositories",
            description="List all repositories",
            method="GET",
            endpoint="/user/repos",
            is_available=True,
        )
        
        self.assertEqual(capability.name, "list_repositories")
        self.assertEqual(capability.method, "GET")


if __name__ == "__main__":
    unittest.main()
