"""L0-L4 policy engine with approvals and side-effect-free dry runs."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class RiskLevel(Enum):
    L0_READ_ONLY = 0
    L1_PREPARE = 1
    L2_SUPERVISED = 2
    L3_AUTOMATION = 3
    L4_CRITICAL = 4


DANGEROUS_KINDS = {"delete", "send", "publish", "financial"}


@dataclass
class Operation:
    id: str
    kind: str
    level: RiskLevel = RiskLevel.L1_PREPARE
    payload: Dict[str, Any] = field(default_factory=dict)

    @property
    def dangerous(self) -> bool:
        return self.kind in DANGEROUS_KINDS or self.level == RiskLevel.L4_CRITICAL


@dataclass
class Decision:
    allowed: bool
    reason: str
    approvals: List[str] = field(default_factory=list)


class ApprovalMissing(RuntimeError):
    pass


class PolicyEngine:
    """Deny dangerous operations without an explicit approval token."""

    def __init__(self, max_autonomous_level: RiskLevel = RiskLevel.L2_SUPERVISED):
        self.max_autonomous_level = max_autonomous_level

    def authorize(self, op: Operation, approvals: Optional[List[str]] = None) -> Decision:
        approvals = list(approvals or [])
        if op.level == RiskLevel.L0_READ_ONLY:
            return Decision(True, "read-only", approvals)
        if op.dangerous:
            if op.id not in approvals:
                raise ApprovalMissing(f"approval required for {op.id} ({op.kind})")
            return Decision(True, "approved", approvals)
        if op.level.value > self.max_autonomous_level.value:
            return Decision(False, f"level {op.level.name} exceeds autonomy ceiling", approvals)
        return Decision(True, "within autonomy ceiling", approvals)

    def dry_run(self, steps: List[Operation], approvals: Optional[List[str]] = None) -> List[Decision]:
        """Evaluate every step without invoking any of them."""
        return [self.authorize(step, approvals) for step in steps]


def execute(engine: PolicyEngine, op: Operation, action: Callable[[], Any],
            approvals: Optional[List[str]] = None) -> Any:
    """Run an action only after policy authorization."""
    decision = engine.authorize(op, approvals)
    if not decision.allowed:
        raise PermissionError(decision.reason)
    return action()
