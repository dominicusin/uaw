"""Policy (UAW-005) and result-verification (UAW-006) tests."""
import tempfile
import unittest

from uaw.core.policy import (
    ApprovalMissing, Decision, Operation, PolicyEngine, RiskLevel, execute,
)
from uaw.core.verification import VerificationFailed, execute_and_verify, verify


class TestPolicyEngine(unittest.TestCase):
    def setUp(self):
        self.engine = PolicyEngine()

    def test_read_only_is_allowed(self):
        decision = self.engine.authorize(Operation("r1", "read", RiskLevel.L0_READ_ONLY))
        self.assertTrue(decision.allowed)

    def test_destructive_operation_requires_approval(self):
        op = Operation("del1", "delete", RiskLevel.L3_AUTOMATION)
        with self.assertRaises(ApprovalMissing):
            self.engine.authorize(op)
        self.assertTrue(self.engine.authorize(op, ["del1"]).allowed)

    def test_publish_and_financial_require_approval(self):
        for kind in ("publish", "financial", "send"):
            with self.assertRaises(ApprovalMissing):
                self.engine.authorize(Operation(kind + ":1", kind))
            self.assertTrue(self.engine.authorize(Operation(kind + ":1", kind), [kind + ":1"]).allowed)

    def test_autonomy_ceiling_is_enforced(self):
        strict = PolicyEngine(max_autonomous_level=RiskLevel.L0_READ_ONLY)
        decision = strict.authorize(Operation("prepare", "prepare", RiskLevel.L1_PREPARE))
        self.assertFalse(decision.allowed)
        self.assertIn("ceiling", decision.reason)

    def test_critical_requires_approval(self):
        op = Operation("crit", "deploy", RiskLevel.L4_CRITICAL)
        with self.assertRaises(ApprovalMissing):
            self.engine.authorize(op)

    def test_dry_run_has_no_side_effects(self):
        calls = []
        steps = [Operation("a", "read", RiskLevel.L0_READ_ONLY),
                 Operation("b", "delete", RiskLevel.L2_SUPERVISED)]
        decisions = self.engine.dry_run(steps, approvals=["b"])
        self.assertEqual(len(decisions), 2)
        self.assertEqual(calls, [])

    def test_execute_refuses_unapproved_action(self):
        calls = []
        op = Operation("pub", "publish")
        with self.assertRaises(ApprovalMissing):
            execute(self.engine, op, lambda: calls.append(1))
        self.assertEqual(calls, [])
        execute(self.engine, op, lambda: calls.append(1), approvals=["pub"])
        self.assertEqual(calls, [1])


class TestResultVerification(unittest.TestCase):
    def test_successful_call_with_wrong_result_is_failed(self):
        def action():
            return {"status": "ok", "count": 0}
        with self.assertRaises(VerificationFailed) as ctx:
            execute_and_verify(action, {"status": "ok", "count": 2})
        self.assertFalse(ctx.exception.result.ok)
        self.assertIn("count", ctx.exception.result.reason)

    def test_no_result_is_failure(self):
        self.assertFalse(verify({"id": 1}, None).ok)

    def test_matching_result_is_verified(self):
        result = execute_and_verify(lambda: {"id": 1, "state": "done"},
                                    {"id": 1, "state": "done"})
        self.assertTrue(result.ok)


if __name__ == "__main__":
    unittest.main()
