"""Verify operation results instead of trusting successful calls."""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass
class VerificationResult:
    ok: bool
    expected: Any
    actual: Any
    reason: str = ""


class VerificationFailed(RuntimeError):
    def __init__(self, result: VerificationResult):
        super().__init__(result.reason)
        self.result = result


def verify(expected: Dict[str, Any], actual: Optional[Dict[str, Any]]) -> VerificationResult:
    """A call can succeed while its result is wrong; compare explicitly."""
    if actual is None:
        return VerificationResult(False, expected, actual, "no result returned")
    mismatches = [k for k, v in expected.items() if actual.get(k) != v]
    if mismatches:
        return VerificationResult(False, expected, actual,
                                  "mismatched fields: " + ", ".join(mismatches))
    return VerificationResult(True, expected, actual, "verified")


def execute_and_verify(action: Callable[[], Optional[Dict[str, Any]]],
                       expected: Dict[str, Any]) -> VerificationResult:
    """Mark the operation failed when verification fails, even if action returned."""
    actual = action()
    result = verify(expected, actual)
    if not result.ok:
        raise VerificationFailed(result)
    return result
