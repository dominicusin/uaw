"""Lightweight observability: counters, timings, structured logs and alerts."""
import json
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


SECRET_HINTS = ("secret", "token", "password", "api_key", "authorization", "gitleaks", "license_key")


def redact(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Never write secrets into logs, even when a caller passes them."""
    return {k: ("***" if any(h in k.lower() for h in SECRET_HINTS) else v)
            for k, v in payload.items()}


@dataclass
class Metric:
    name: str
    value: float = 0.0
    count: int = 0
    labels: Dict[str, str] = field(default_factory=dict)


class Observability:
    def __init__(self, alert_threshold: float = 1.0):
        self._lock = threading.RLock()
        self._metrics: Dict[str, Metric] = {}
        self._logs: List[Dict[str, Any]] = []
        self._alerts: List[Dict[str, Any]] = []
        self.alert_threshold = alert_threshold

    def counter(self, name: str, value: float = 1.0, **labels) -> None:
        with self._lock:
            key = name + ":" + json.dumps(labels, sort_keys=True)
            m = self._metrics.setdefault(key, Metric(name, labels=labels))
            m.value += value
            m.count += 1

    @contextmanager
    def timer(self, name: str, **labels):
        started = time.monotonic()
        try:
            yield
        finally:
            self.counter(name, time.monotonic() - started, **labels)

    def log(self, event: str, **payload: Any) -> None:
        with self._lock:
            self._logs.append({"event": event, "payload": redact(payload)})

    def check_alerts(self, name: str) -> List[Dict[str, Any]]:
        with self._lock:
            triggered = [{"metric": m.name, "value": m.value}
                         for m in self._metrics.values()
                         if m.name == name and m.value > self.alert_threshold]
            self._alerts.extend(triggered)
            return triggered

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "metrics": {k: {"value": m.value, "count": m.count}
                            for k, m in self._metrics.items()},
                "log_count": len(self._logs),
                "alerts": list(self._alerts),
            }
