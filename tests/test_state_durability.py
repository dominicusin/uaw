"""Crash-recovery and transaction checks for the SQLite/WAL state manager."""
import json
import tempfile
import threading
import unittest
from pathlib import Path

from uaw.core.state_manager import StateManager, StateType


class TestStateDurability(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_survives_reopen_without_close(self):
        manager = StateManager(self.path)
        manager.set("workflow:1", {"step": 2}, StateType.WORKFLOW, ttl=3600)
        # Simulate a crash: no close(), no explicit checkpoint.
        reopened = StateManager(self.path)
        self.assertEqual(reopened.get("workflow:1"), {"step": 2})
        reopened.close()

    def test_legacy_json_is_migrated_without_deleting_source(self):
        legacy = self.path / "state.json"
        legacy.write_text(json.dumps({"entries": [{
            "key": "legacy:1", "value": {"ok": True},
            "state_type": "workflow",
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "ttl": None,
        }]}), encoding="utf-8")
        manager = StateManager(self.path)
        self.assertEqual(manager.get("legacy:1"), {"ok": True})
        self.assertTrue(legacy.exists())
        manager.close()

    def test_concurrent_writes_are_durable(self):
        manager = StateManager(self.path)
        def writer(offset):
            for i in range(20):
                manager.set(f"key:{offset}:{i}", i, StateType.EXECUTION_CONTEXT)
        threads = [threading.Thread(target=writer, args=(n,)) for n in range(4)]
        for t in threads: t.start()
        for t in threads: t.join()
        reopened = StateManager(self.path)
        self.assertEqual(reopened.get_stats()["total_entries"], 80)
        for n in range(4):
            self.assertEqual(reopened.get(f"key:{n}:19"), 19)
        reopened.close()

    def test_delete_is_transactional(self):
        manager = StateManager(self.path)
        manager.set("gone", 1)
        self.assertTrue(manager.delete("gone"))
        reopened = StateManager(self.path)
        self.assertIsNone(reopened.get("gone"))
        reopened.close()


if __name__ == "__main__":
    unittest.main()
