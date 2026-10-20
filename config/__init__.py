"""
UAW Configuration Module
Конфигурация для Unified Agentic Workspace
"""

from .config_manager import ConfigManager, ConfigValue
from .integration_config import IntegrationConfig, IntegrationSettings
from .automation_config import AutomationConfig, TriggerConfig, WebhookConfig
from .security_config import SecurityConfig, PermissionConfig

__all__ = [
    "ConfigManager",
    "ConfigValue",
    "IntegrationConfig",
    "IntegrationSettings",
    "AutomationConfig",
    "TriggerConfig",
    "WebhookConfig",
    "SecurityConfig",
    "PermissionConfig",
]
