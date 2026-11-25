"""Observability and secret-safe logging tests (UAW-007)."""
import time
import unittest

from uaw.core.observability import Observability, redact


class TestObservability(unittest.TestCase):
    def test_counter_accumulates(self):
        o = Observability()
        o.counter("workflow.failed")
        o.counter("workflow.failed")
        self.assertEqual(o.snapshot()["metrics"]["workflow.failed:{}"]["count"], 2)

    def test_timer_records_duration(self):
        o = Observability()
        with o.timer("step.duration", step="a"):
            time.sleep(0.01)
        value = o.snapshot()["metrics"]["step.duration:{\"step\": \"a\"}"]["value"]
        self.assertGreater(value, 0)

    def test_logs_never_contain_secrets(self):
        o = Observability()
        o.log("call", api_key="super-secret", status="ok")
        entry = o.snapshot()["log_count"]
        self.assertEqual(entry, 1)
        self.assertEqual(o._logs[0]["payload"]["api_key"], "***")
        self.assertEqual(o._logs[0]["payload"]["status"], "ok")
        self.assertNotIn("super-secret", str(o._logs))

    def test_alert_triggers_over_threshold(self):
        o = Observability(alert_threshold=1.0)
        o.counter("workflow.failed", 2)
        alerts = o.check_alerts("workflow.failed")
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["value"], 2)

    def test_no_alert_below_threshold(self):
        o = Observability(alert_threshold=1.0)
        o.counter("workflow.failed", 0)
        self.assertEqual(o.check_alerts("workflow.failed"), [])

    def test_redact_handles_nested_names(self):
        clean = redact({"Authorization": "x", "GITLEAKS_LICENSE": "y", "ok": 1})
        self.assertEqual(clean["Authorization"], "***")
        self.assertEqual(clean["GITLEAKS_LICENSE"], "***")
        self.assertEqual(clean["ok"], 1)


if __name__ == "__main__":
    unittest.main()
