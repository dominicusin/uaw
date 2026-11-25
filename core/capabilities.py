"""Capability discovery with concrete connector availability checks (UAW-004)."""
from dataclasses import dataclass
from typing import Any, List


class ConnectorUnavailable(RuntimeError):
    pass


@dataclass
class Capability:
    name: str
    available: bool
    reason: str


class CapabilityProbe:
    """Ask each connector whether it can actually be used, not just declared."""

    CREDENTIAL_FIELDS = ("api_key", "access_token", "client_id", "username")

    def discover(self, registry: Any) -> List[Capability]:
        out = []
        for info in registry.list():
            instance = getattr(info, "instance", None)
            probe = getattr(instance, "is_available", None)
            if callable(probe):
                try:
                    available = bool(probe())
                    reason = "connector probe" if available else "connector probe returned false"
                except Exception as exc:
                    available, reason = False, f"probe failed: {exc}"
            else:
                config = getattr(info, "config", None)
                present = [f for f in self.CREDENTIAL_FIELDS
                           if getattr(config, f, None)]
                if present:
                    available, reason = True, "credentials present: " + ",".join(present)
                else:
                    available, reason = False, "no credentials configured"
            out.append(Capability(name=getattr(info, "name", "unknown"),
                                  available=available, reason=reason))
        return out

    def require(self, registry: Any, name: str) -> Capability:
        for cap in self.discover(registry):
            if cap.name == name:
                if not cap.available:
                    raise ConnectorUnavailable(f"{name}: {cap.reason}")
                return cap
        raise ConnectorUnavailable(f"{name}: not registered")
