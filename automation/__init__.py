"""
UAW Automation Module
Event-driven automation for Unified Agentic Workspace
"""

from .event_manager import (
    EventManager,
    EventType,
    EventSource,
    Event,
    EventHandler,
)
from .webhook_server import (
    WebhookServer,
    WebhookConfig,
    WebhookHandler,
)
from .trigger import (
    Trigger,
    TriggerType,
    TriggerCondition,
    TriggerAction,
)
from .automation_engine import (
    AutomationEngine,
    AutomationRule,
    AutomationStatus,
)

__all__ = [
    "EventManager",
    "EventType",
    "EventSource",
    "Event",
    "EventHandler",
    "WebhookServer",
    "WebhookConfig",
    "WebhookHandler",
    "Trigger",
    "TriggerType",
    "TriggerCondition",
    "TriggerAction",
    "AutomationEngine",
    "AutomationRule",
    "AutomationStatus",
]
