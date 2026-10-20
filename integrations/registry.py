"""
Integration Registry for UAW
Реестр всех интеграций системы
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union
from enum import Enum
import importlib
import json
from pathlib import Path

from .base import BaseIntegration, IntegrationConfig, IntegrationStatus, IntegrationResult


class IntegrationCategory(Enum):
    """Categories of integrations"""
    DEVELOPMENT = "development"  # GitHub, GitLab, etc.
    PROJECT_MANAGEMENT = "project_management"  # Asana, Linear, etc.
    COMMUNICATION = "communication"  # Slack, Teams, etc.
    CALENDAR = "calendar"  # Google Calendar, Outlook, etc.
    DOCUMENTS = "documents"  # Notion, Box, Google Drive, etc.
    DEPLOYMENT = "deployment"  # Vercel, Netlify, etc.
    BUSINESS = "business"  # Wix, etc.
    AUTOMATION = "automation"  # Automations, etc.
    OTHER = "other"


@dataclass
class IntegrationInfo:
    """Information about a registered integration"""
    name: str
    display_name: str
    description: str
    category: IntegrationCategory
    config: IntegrationConfig
    integration_class: Type[BaseIntegration]
    instance: Optional[BaseIntegration] = None
    status: IntegrationStatus = IntegrationStatus.UNAVAILABLE
    priority: int = 0  # Higher priority integrations are preferred
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category.value,
            "config": self.config.to_dict(),
            "status": self.status.value,
            "priority": self.priority
        }


class IntegrationRegistry:
    """
    Registry of all available integrations.
    Manages initialization, status checking, and routing of integration calls.
    """
    
    def __init__(self):
        self._integrations: Dict[str, IntegrationInfo] = {}
        self._initialized = False
        self._default_integrations_loaded = False
    
    def register(
        self,
        name: str,
        display_name: str,
        description: str,
        category: IntegrationCategory,
        integration_class: Type[BaseIntegration],
        config: Optional[IntegrationConfig] = None,
        priority: int = 0
    ) -> None:
        """
        Register an integration.
        
        Args:
            name: Unique name
            display_name: Display name
            description: Description
            category: Category
            integration_class: Integration class
            config: Optional configuration
            priority: Priority (higher = preferred)
        """
        if config is None:
            config = IntegrationConfig(
                name=name,
                display_name=display_name,
                description=description
            )
        
        info = IntegrationInfo(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            config=config,
            integration_class=integration_class,
            priority=priority
        )
        
        self._integrations[name] = info
    
    def register_instance(self, integration: BaseIntegration, priority: int = 0) -> None:
        """
        Register an already instantiated integration.
        
        Args:
            integration: Integration instance
            priority: Priority
        """
        info = IntegrationInfo(
            name=integration.name,
            display_name=integration.display_name,
            description=integration.description,
            category=self._get_category(integration.name),
            config=integration.config,
            integration_class=type(integration),
            instance=integration,
            priority=priority
        )
        
        self._integrations[integration.name] = info
    
    def _get_category(self, name: str) -> IntegrationCategory:
        """Determine category from integration name"""
        name_lower = name.lower()
        
        if any(x in name_lower for x in ["github", "gitlab", "bitbucket"]):
            return IntegrationCategory.DEVELOPMENT
        elif any(x in name_lower for x in ["asana", "linear", "jira", "monday"]):
            return IntegrationCategory.PROJECT_MANAGEMENT
        elif any(x in name_lower for x in ["slack", "teams", "discord"]):
            return IntegrationCategory.COMMUNICATION
        elif any(x in name_lower for x in ["calendar", "outlook", "google_calendar"]):
            return IntegrationCategory.CALENDAR
        elif any(x in name_lower for x in ["notion", "box", "drive", "sharepoint"]):
            return IntegrationCategory.DOCUMENTS
        elif any(x in name_lower for x in ["vercel", "netlify", "heroku"]):
            return IntegrationCategory.DEPLOYMENT
        elif any(x in name_lower for x in ["wix", "shopify"]):
            return IntegrationCategory.BUSINESS
        else:
            return IntegrationCategory.OTHER
    
    def get(self, name: str) -> Optional[BaseIntegration]:
        """
        Get an integration instance by name.
        Initializes the integration if not already initialized.
        
        Args:
            name: Integration name
            
        Returns:
            Integration instance or None
        """
        info = self._integrations.get(name)
        if not info:
            return None
        
        # Initialize if needed
        if not info.instance:
            try:
                info.instance = info.integration_class(info.config)
            except Exception as e:
                print(f"Error initializing integration {name}: {e}")
                return None
        
        return info.instance
    
    def get_info(self, name: str) -> Optional[IntegrationInfo]:
        """Get integration info by name"""
        return self._integrations.get(name)
    
    def list(self, category: Optional[IntegrationCategory] = None) -> List[IntegrationInfo]:
        """
        List all registered integrations.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of integration infos
        """
        if category:
            return [
                info for info in self._integrations.values()
                if info.category == category
            ]
        return list(self._integrations.values())
    
    def list_by_priority(self) -> List[IntegrationInfo]:
        """List integrations sorted by priority (highest first)"""
        return sorted(
            self._integrations.values(),
            key=lambda x: x.priority,
            reverse=True
        )
    
    def list_available(self) -> List[IntegrationInfo]:
        """List only available integrations"""
        return [
            info for info in self._integrations.values()
            if info.instance and info.instance.is_available()
        ]
    
    def list_connected(self) -> List[IntegrationInfo]:
        """List only connected integrations"""
        return [
            info for info in self._integrations.values()
            if info.instance and info.instance.status == IntegrationStatus.CONNECTED
        ]
    
    async def initialize_all(self) -> Dict[str, bool]:
        """
        Initialize all registered integrations.
        
        Returns:
            Dict of integration names to success status
        """
        results = {}
        
        for name, info in self._integrations.items():
            if not info.instance:
                try:
                    info.instance = info.integration_class(info.config)
                except Exception as e:
                    results[name] = False
                    continue
            
            try:
                success = await info.instance.initialize()
                results[name] = success
                if success:
                    info.status = await info.instance.check_status()
            except Exception as e:
                results[name] = False
        
        return results
    
    async def check_all_statuses(self) -> Dict[str, IntegrationStatus]:
        """
        Check status of all integrations.
        
        Returns:
            Dict of integration names to status
        """
        statuses = {}
        
        for name, info in self._integrations.items():
            if info.instance:
                try:
                    status = await info.instance.check_status()
                    info.status = status
                    statuses[name] = status
                except Exception:
                    statuses[name] = IntegrationStatus.ERROR
            else:
                statuses[name] = IntegrationStatus.UNAVAILABLE
        
        return statuses
    
    async def execute(
        self,
        integration_name: str,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> IntegrationResult:
        """
        Execute an action on a specific integration.
        
        Args:
            integration_name: Name of integration
            action: Action to execute
            parameters: Action parameters
            
        Returns:
            IntegrationResult
        """
        integration = self.get(integration_name)
        if not integration:
            return IntegrationResult(
                success=False,
                error=f"Integration {integration_name} not found"
            )
        
        if not integration.is_available():
            return IntegrationResult(
                success=False,
                error=f"Integration {integration_name} is not available (status: {integration.status.value})"
            )
        
        try:
            return await integration.execute(action, parameters)
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=str(e)
            )
    
    async def execute_any(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None,
        category: Optional[IntegrationCategory] = None
    ) -> IntegrationResult:
        """
        Execute an action on any available integration that supports it.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            category: Optional category filter
            
        Returns:
            IntegrationResult from the first successful integration
        """
        # Try integrations in priority order
        for info in self.list_by_priority():
            if category and info.category != category:
                continue
            
            if not info.instance or not info.instance.is_available():
                continue
            
            if info.instance.has_capability(action):
                try:
                    return await info.instance.execute(action, parameters)
                except Exception:
                    continue
        
        return IntegrationResult(
            success=False,
            error=f"No available integration supports action: {action}"
        )
    
    def get_status(self) -> Dict[str, IntegrationStatus]:
        """
        Get status of all integrations.
        
        Returns:
            Dict of integration names to status
        """
        return {
            name: info.status.value if info.instance else IntegrationStatus.UNAVAILABLE.value
            for name, info in self._integrations.items()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        categories = {cat.value: 0 for cat in IntegrationCategory}
        statuses = {status.value: 0 for status in IntegrationStatus}
        
        for info in self._integrations.values():
            categories[info.category.value] += 1
            
            if info.instance:
                status = info.instance.status.value
            else:
                status = IntegrationStatus.UNAVAILABLE.value
            statuses[status] += 1
        
        return {
            "total": len(self._integrations),
            "by_category": categories,
            "by_status": statuses
        }
    
    def unregister(self, name: str) -> bool:
        """Unregister an integration"""
        if name in self._integrations:
            info = self._integrations[name]
            if info.instance:
                # Clean up instance if needed
                pass
            del self._integrations[name]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all registrations"""
        self._integrations.clear()
    
    def load_default_integrations(self) -> None:
        """Load default integrations from the integrations module"""
        if self._default_integrations_loaded:
            return
        
        # Import and register default integrations
        try:
            from .github_integration import GitHubIntegration, GitHubConfig
            self.register(
                "github",
                "GitHub",
                "GitHub integration for repositories, issues, and pull requests",
                IntegrationCategory.DEVELOPMENT,
                GitHubIntegration,
                GitHubConfig()
            )
        except Exception:
            pass
        
        try:
            from .asana_integration import AsanaIntegration, AsanaConfig
            self.register(
                "asana",
                "Asana",
                "Asana integration for tasks, projects, and teams",
                IntegrationCategory.PROJECT_MANAGEMENT,
                AsanaIntegration,
                AsanaConfig()
            )
        except Exception:
            pass
        
        try:
            from .slack_integration import SlackIntegration, SlackConfig
            self.register(
                "slack",
                "Slack",
                "Slack integration for messages and channels",
                IntegrationCategory.COMMUNICATION,
                SlackIntegration,
                SlackConfig()
            )
        except Exception:
            pass
        
        try:
            from .calendar_integration import CalendarIntegration, CalendarConfig
            self.register(
                "calendar",
                "Calendar",
                "Calendar integration for events and scheduling",
                IntegrationCategory.CALENDAR,
                CalendarIntegration,
                CalendarConfig()
            )
        except Exception:
            pass
        
        try:
            from .netlify_integration import NetlifyIntegration, NetlifyConfig
            self.register(
                "netlify",
                "Netlify",
                "Netlify integration for deployments",
                IntegrationCategory.DEPLOYMENT,
                NetlifyIntegration,
                NetlifyConfig()
            )
        except Exception:
            pass
        
        try:
            from .notion_integration import NotionIntegration, NotionConfig
            self.register(
                "notion",
                "Notion",
                "Notion integration for documents and databases",
                IntegrationCategory.DOCUMENTS,
                NotionIntegration,
                NotionConfig()
            )
        except Exception:
            pass
        
        try:
            from .box_integration import BoxIntegration, BoxConfig
            self.register(
                "box",
                "Box",
                "Box integration for files and folders",
                IntegrationCategory.DOCUMENTS,
                BoxIntegration,
                BoxConfig()
            )
        except Exception:
            pass
        
        try:
            from .linear_integration import LinearIntegration, LinearConfig
            self.register(
                "linear",
                "Linear",
                "Linear integration for issues and projects",
                IntegrationCategory.PROJECT_MANAGEMENT,
                LinearIntegration,
                LinearConfig()
            )
        except Exception:
            pass
        
        try:
            from .document_library_integration import DocumentLibraryIntegration, DocumentLibraryConfig
            self.register(
                "document_library",
                "Document Library",
                "Document Library integration for document search and retrieval",
                IntegrationCategory.DOCUMENTS,
                DocumentLibraryIntegration,
                DocumentLibraryConfig()
            )
        except Exception:
            pass
        
        self._default_integrations_loaded = True
    
    def save_to_file(self, path: Union[str, Path]) -> None:
        """Save registry to file"""
        path = Path(path)
        data = {
            "integrations": [
                info.to_dict() for info in self._integrations.values()
            ]
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, path: Union[str, Path]) -> None:
        """Load registry from file"""
        path = Path(path)
        if not path.exists():
            return
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for info_data in data.get("integrations", []):
            # This is a simplified load - full implementation would need
            # to reconstruct integration classes
            pass


# Global registry instance
registry = IntegrationRegistry()
