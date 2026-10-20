"""
UAW Integrations Package
Модуль интеграций для Unified Agentic Workspace

Содержит все интеграции с внешними сервисами:
- BaseIntegration: Базовый класс интеграций
- GitHubIntegration: Интеграция с GitHub
- AsanaIntegration: Интеграция с Asana
- CalendarIntegration: Интеграция с календарями (Google/Outlook)
- SlackIntegration: Интеграция с Slack
- NetlifyIntegration: Интеграция с Netlify
- BoxIntegration: Интеграция с Box
- NotionIntegration: Интеграция с Notion
- LinearIntegration: Интеграция с Linear
- DocumentLibraryIntegration: Интеграция с Document Library
"""

from .base import (
    BaseIntegration,
    IntegrationConfig,
    IntegrationResult,
    IntegrationStatus,
    IntegrationType,
    IntegrationCapability,
    IntegrationError,
    IntegrationTimeoutError,
    IntegrationAuthError,
    IntegrationRateLimitError,
)

from .github_integration import GitHubIntegration, GitHubConfig
from .asana_integration import AsanaIntegration, AsanaConfig
from .calendar_integration import CalendarIntegration, CalendarConfig
from .slack_integration import SlackIntegration, SlackConfig
from .netlify_integration import NetlifyIntegration, NetlifyConfig
from .box_integration import BoxIntegration, BoxConfig
from .notion_integration import NotionIntegration, NotionConfig
from .linear_integration import LinearIntegration, LinearConfig
from .document_library_integration import DocumentLibraryIntegration, DocumentLibraryConfig

# Singleton instances
github_integration = GitHubIntegration()
asana_integration = AsanaIntegration()
calendar_integration = CalendarIntegration()
slack_integration = SlackIntegration()
netlify_integration = NetlifyIntegration()
box_integration = BoxIntegration()
notion_integration = NotionIntegration()
linear_integration = LinearIntegration()
document_library_integration = DocumentLibraryIntegration()

# All integrations
INTEGRATIONS = {
    "github": github_integration,
    "asana": asana_integration,
    "calendar": calendar_integration,
    "slack": slack_integration,
    "netlify": netlify_integration,
    "box": box_integration,
    "notion": notion_integration,
    "linear": linear_integration,
    "document_library": document_library_integration,
}

# Available integrations (connected or available)
AVAILABLE_INTEGRATIONS = {
    "github": github_integration,
    "asana": asana_integration,
    "document_library": document_library_integration,
    "google_calendar": calendar_integration,
    "outlook_calendar": calendar_integration,
    "box": box_integration,
    "notion": notion_integration,
    "linear": linear_integration,
    "netlify": netlify_integration,
    "slack": slack_integration,
}

# Unavailable integrations (require adapters)
UNAVAILABLE_INTEGRATIONS = [
    "microsoft_teams",
    "calendly",
    "vercel",
    "gamma",
    "canva",
    "excalidraw",
    "figma",
    "wix",
]

__all__ = [
    # Base
    "BaseIntegration",
    "IntegrationConfig",
    "IntegrationResult",
    "IntegrationStatus",
    "IntegrationType",
    "IntegrationCapability",
    "IntegrationError",
    "IntegrationTimeoutError",
    "IntegrationAuthError",
    "IntegrationRateLimitError",
    
    # Config classes
    "GitHubConfig",
    "AsanaConfig",
    "CalendarConfig",
    "SlackConfig",
    "NetlifyConfig",
    "BoxConfig",
    "NotionConfig",
    "LinearConfig",
    "DocumentLibraryConfig",
    
    # Integration classes
    "GitHubIntegration",
    "AsanaIntegration",
    "CalendarIntegration",
    "SlackIntegration",
    "NetlifyIntegration",
    "BoxIntegration",
    "NotionIntegration",
    "LinearIntegration",
    "DocumentLibraryIntegration",
    
    # Singleton instances
    "github_integration",
    "asana_integration",
    "calendar_integration",
    "slack_integration",
    "netlify_integration",
    "box_integration",
    "notion_integration",
    "linear_integration",
    "document_library_integration",
    
    # Collections
    "INTEGRATIONS",
    "AVAILABLE_INTEGRATIONS",
    "UNAVAILABLE_INTEGRATIONS",
]
