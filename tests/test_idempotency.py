"""Idempotency-key and lease-recovery tests."""
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from uaw.core.idempotency import (
    IdempotencyFailure, IdempotencyInProgress, IdempotencyStore,
)


class TestIdempotency(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = IdempotencyStore(self.tmp.name, lease_seconds=1)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_same_key_executes_once(self):
        calls = []
        def op():
            calls.append(1)
            return {"ok": True}
        first = self.store.run("sync:1", op)
        second = self.store.run("sync:1", lambda: self.fail("must not rerun"))
        self.assertEqual(first, second)
        self.assertEqual(len(calls), 1)

    def test_different_keys_execute_independently(self):
        self.assertEqual(self.store.run("a", lambda: 1), 1)
        self.assertEqual(self.store.run("b", lambda: 2), 2)

    def test_failure_is_recorded_and_replayed(self):
        def fail():
            raise ValueError("boom")
        with self.assertRaises(ValueError):
            self.store.run("bad", fail)
        rec = self.store.get("bad")
        self.assertEqual(rec.status, "failed")
        with self.assertRaises(IdempotencyFailure):
            self.store.run("bad", lambda: "ok")

    def _seed_in_progress(self, key, lease_delta):
        self.store.close()
        db = Path(self.tmp.name) / "idempotency.sqlite3"
        conn = sqlite3.connect(str(db))
        lease = (datetime.now(timezone.utc) + timedelta(seconds=lease_delta)).isoformat()
        conn.execute(
            """INSERT INTO idempotency(key,status,result,error,created_at,lease_until)
               VALUES (?, 'in_progress', NULL, NULL, ?, ?)""",
            (key, datetime.now(timezone.utc).isoformat(), lease),
        )
        conn.commit()
        conn.close()
        self.store = IdempotencyStore(self.tmp.name, lease_seconds=1)

    def test_in_progress_key_is_rejected_until_lease_expires(self):
        self._seed_in_progress("locked", 300)
        with self.assertRaises(IdempotencyInProgress):
            self.store.run("locked", lambda: "should never run")

    def test_expired_lease_is_recovered_after_reopen(self):
        self._seed_in_progress("crashed", -10)
        self.assertEqual(self.store.run("crashed", lambda: 42), 42)
        self.assertEqual(self.store.run("crashed", lambda: 0), 42)


if __name__ == "__main__":
    unittest.main()
