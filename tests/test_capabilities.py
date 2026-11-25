"""Capability discovery tests (UAW-004)."""
import unittest
from types import SimpleNamespace

from uaw.core.capabilities import CapabilityProbe, ConnectorUnavailable


class FakeRegistry:
    def __init__(self, infos):
        self._infos = infos

    def list(self):
        return self._infos


class TestCapabilities(unittest.TestCase):
    def setUp(self):
        self.probe = CapabilityProbe()

    def test_live_probe_overrides_declared_status(self):
        info = SimpleNamespace(name="github", instance=SimpleNamespace(is_available=lambda: True), config=None)
        cap = self.probe.require(FakeRegistry([info]), "github")
        self.assertTrue(cap.available)
        self.assertEqual(cap.reason, "connector probe")

    def test_failed_probe_is_unavailable_with_reason(self):
        def fail():
            raise RuntimeError("auth expired")
        info = SimpleNamespace(name="slack", instance=SimpleNamespace(is_available=fail), config=None)
        with self.assertRaises(ConnectorUnavailable) as ctx:
            self.probe.require(FakeRegistry([info]), "slack")
        self.assertIn("auth expired", str(ctx.exception))

    def test_missing_credentials_are_reported(self):
        info = SimpleNamespace(name="notion", instance=None,
                               config=SimpleNamespace(api_key=None, access_token=None,
                                                      client_id=None, username=None))
        with self.assertRaises(ConnectorUnavailable) as ctx:
            self.probe.require(FakeRegistry([info]), "notion")
        self.assertIn("no credentials", str(ctx.exception))

    def test_credentials_present_is_available(self):
        info = SimpleNamespace(name="linear", instance=None,
                               config=SimpleNamespace(api_key="token", access_token=None,
                                                      client_id=None, username=None))
        self.assertTrue(self.probe.require(FakeRegistry([info]), "linear").available)

    def test_unregistered_connector_is_rejected(self):
        with self.assertRaises(ConnectorUnavailable):
            self.probe.require(FakeRegistry([]), "missing")


if __name__ == "__main__":
    unittest.main()
