"""
Tests for UAW Adapters
"""

import unittest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from uaw.adapters.base import BaseAdapter, AdapterConfig, AdapterResult, AdapterStatus
from uaw.adapters.teams_adapter import MicrosoftTeamsAdapter
from uaw.adapters.vercel_adapter import VercelAdapter
from uaw.adapters.calendly_adapter import CalendlyAdapter
from uaw.adapters.gamma_adapter import GammaAdapter
from uaw.adapters.canva_adapter import CanvaAdapter
from uaw.adapters.excalidraw_adapter import ExcalidrawAdapter
from uaw.adapters.figma_adapter import FigmaAdapter
from uaw.adapters.wix_adapter import WixAdapter


class TestBaseAdapter(unittest.TestCase):
    """Tests for BaseAdapter class"""

    def setUp(self):
        self.config = AdapterConfig(
            adapter_id="test-adapter",
            name="Test Adapter",
            service="test",
            base_url="https://api.test.com",
            api_key=None,
            timeout=30,
        )
        self.adapter = BaseAdapter(self.config)

    def test_initialization(self):
        """Test BaseAdapter initialization"""
        self.assertEqual(self.adapter.name, "Test Adapter")
        self.assertEqual(self.adapter.service, "test")
        self.assertEqual(self.adapter.base_url, "https://api.test.com")

    def test_health_check(self):
        """Test health check"""
        # В реальности это проверял бы подключение к API
        # Для теста просто проверяем, что метод существует
        self.assertTrue(hasattr(self.adapter, 'check_health'))

    def test_get_capabilities(self):
        """Test getting capabilities"""
        capabilities = self.adapter.get_capabilities()
        self.assertIsInstance(capabilities, list)

    def test_get_rate_limits(self):
        """Test getting rate limits"""
        limits = self.adapter.get_rate_limits()
        self.assertIsInstance(limits, list)


class TestMicrosoftTeamsAdapter(unittest.TestCase):
    """Tests for MicrosoftTeamsAdapter class"""

    def setUp(self):
        self.teams = MicrosoftTeamsAdapter()

    def test_initialization(self):
        """Test TeamsAdapter initialization"""
        self.assertEqual(self.teams.name, "Microsoft Teams")
        self.assertEqual(self.teams.service, "teams")

    def test_get_capabilities(self):
        """Test getting Teams capabilities"""
        capabilities = self.teams.get_capabilities()
        self.assertGreater(len(capabilities), 0)
        
        # Проверяем, что есть нужные возможности
        capability_names = [cap.name for cap in capabilities]
        self.assertIn("send_message", capability_names)
        self.assertIn("create_channel", capability_names)

    def test_get_rate_limits(self):
        """Test getting Teams rate limits"""
        limits = self.teams.get_rate_limits()
        self.assertGreater(len(limits), 0)


class TestVercelAdapter(unittest.TestCase):
    """Tests for VercelAdapter class"""

    def setUp(self):
        self.vercel = VercelAdapter()

    def test_initialization(self):
        """Test VercelAdapter initialization"""
        self.assertEqual(self.vercel.name, "Vercel")
        self.assertEqual(self.vercel.service, "vercel")

    def test_get_capabilities(self):
        """Test getting Vercel capabilities"""
        capabilities = self.vercel.get_capabilities()
        self.assertGreater(len(capabilities), 0)
        
        capability_names = [cap.name for cap in capabilities]
        self.assertIn("create_deployment", capability_names)
        self.assertIn("list_projects", capability_names)

    def test_get_rate_limits(self):
        """Test getting Vercel rate limits"""
        limits = self.vercel.get_rate_limits()
        self.assertGreater(len(limits), 0)


class TestCalendlyAdapter(unittest.TestCase):
    """Tests for CalendlyAdapter class"""

    def setUp(self):
        self.calendly = CalendlyAdapter()

    def test_initialization(self):
        """Test CalendlyAdapter initialization"""
        self.assertEqual(self.calendly.name, "Calendly")
        self.assertEqual(self.calendly.service, "calendly")

    def test_get_capabilities(self):
        """Test getting Calendly capabilities"""
        capabilities = self.calendly.get_capabilities()
        self.assertGreater(len(capabilities), 0)
        
        capability_names = [cap.name for cap in capabilities]
        self.assertIn("create_event", capability_names)
        self.assertIn("list_event_types", capability_names)


class TestGammaAdapter(unittest.TestCase):
    """Tests for GammaAdapter class"""

    def setUp(self):
        self.gamma = GammaAdapter()

    def test_initialization(self):
        """Test GammaAdapter initialization"""
        self.assertEqual(self.gamma.name, "Gamma")
        self.assertEqual(self.gamma.service, "gamma")

    def test_get_capabilities(self):
        """Test getting Gamma capabilities"""
        capabilities = self.gamma.get_capabilities()
        self.assertGreater(len(capabilities), 0)
        
        capability_names = [cap.name for cap in capabilities]
        self.assertIn("create_presentation", capability_names)


class TestCanvaAdapter(unittest.TestCase):
    """Tests for CanvaAdapter class"""

    def setUp(self):
        self.canva = CanvaAdapter()

    def test_initialization(self):
        """Test CanvaAdapter initialization"""
        self.assertEqual(self.canva.name, "Canva")
        self.assertEqual(self.canva.service, "canva")

    def test_get_capabilities(self):
        """Test getting Canva capabilities"""
        capabilities = self.canva.get_capabilities()
        self.assertGreater(len(capabilities), 0)
        
        capability_names = [cap.name for cap in capabilities]
        self.assertIn("create_design", capability_names)


class TestExcalidrawAdapter(unittest.TestCase):
    """Tests for ExcalidrawAdapter class"""

    def setUp(self):
        self.excalidraw = ExcalidrawAdapter()

    def test_initialization(self):
        """Test ExcalidrawAdapter initialization"""
        self.assertEqual(self.excalidraw.name, "Excalidraw")
        self.assertEqual(self.excalidraw.service, "excalidraw")

    def test_get_capabilities(self):
        """Test getting Excalidraw capabilities"""
        capabilities = self.excalidraw.get_capabilities()
        self.assertGreater(len(capabilities), 0)
        
        capability_names = [cap.name for cap in capabilities]
        self.assertIn("create_diagram", capability_names)


class TestFigmaAdapter(unittest.TestCase):
    """Tests for FigmaAdapter class"""

    def setUp(self):
        self.figma = FigmaAdapter()

    def test_initialization(self):
        """Test FigmaAdapter initialization"""
        self.assertEqual(self.figma.name, "Figma")
        self.assertEqual(self.figma.service, "figma")

    def test_get_capabilities(self):
        """Test getting Figma capabilities"""
        capabilities = self.figma.get_capabilities()
        self.assertGreater(len(capabilities), 0)
        
        capability_names = [cap.name for cap in capabilities]
        self.assertIn("get_file", capability_names)


class TestWixAdapter(unittest.TestCase):
    """Tests for WixAdapter class"""

    def setUp(self):
        self.wix = WixAdapter()

    def test_initialization(self):
        """Test WixAdapter initialization"""
        self.assertEqual(self.wix.name, "Wix")
        self.assertEqual(self.wix.service, "wix")

    def test_get_capabilities(self):
        """Test getting Wix capabilities"""
        capabilities = self.wix.get_capabilities()
        self.assertGreater(len(capabilities), 0)
        
        capability_names = [cap.name for cap in capabilities]
        self.assertIn("list_sites", capability_names)


class TestAdapterResult(unittest.TestCase):
    """Tests for AdapterResult class"""

    def test_success_result(self):
        """Test successful adapter result"""
        result = AdapterResult(
            success=True,
            data={"id": "123", "name": "Test"},
            message="Operation successful",
            status_code=200,
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["id"], "123")

    def test_failed_result(self):
        """Test failed adapter result"""
        result = AdapterResult(
            success=False,
            data={},
            message="Operation failed",
            status_code=400,
            error="Invalid parameters",
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Invalid parameters")

    def test_to_dict(self):
        """Test AdapterResult to_dict"""
        result = AdapterResult(
            success=True,
            data={"key": "value"},
            message="OK",
            status_code=200,
        )
        
        data = result.to_dict()
        self.assertIn("success", data)
        self.assertIn("data", data)
        self.assertIn("message", data)


class TestAdapterStatus(unittest.TestCase):
    """Tests for AdapterStatus enum"""

    def test_status_values(self):
        """Test AdapterStatus values"""
        self.assertEqual(AdapterStatus.AVAILABLE.value, "available")
        self.assertEqual(AdapterStatus.CONFIGURED.value, "configured")
        self.assertEqual(AdapterStatus.NOT_CONFIGURED.value, "not_configured")
        self.assertEqual(AdapterStatus.UNAVAILABLE.value, "unavailable")


if __name__ == "__main__":
    unittest.main()
