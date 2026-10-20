"""
Adapter Registry for UAW
Реестр всех адаптеров для недоступных интеграций
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Union
from enum import Enum
import json
from pathlib import Path

from .base import BaseAdapter, AdapterConfig, AdapterResult, AdapterStatus


class AdapterCategory(Enum):
    """Categories of adapters"""
    DEVELOPMENT = "development"
    PROJECT_MANAGEMENT = "project_management"
    COMMUNICATION = "communication"
    CALENDAR = "calendar"
    DOCUMENTS = "documents"
    DEPLOYMENT = "deployment"
    BUSINESS = "business"
    DESIGN = "design"
    OTHER = "other"


@dataclass
class AdapterInfo:
    """Information about a registered adapter"""
    name: str
    display_name: str
    description: str
    category: AdapterCategory
    config: AdapterConfig
    adapter_class: Type[BaseAdapter]
    instance: Optional[BaseAdapter] = None
    status: AdapterStatus = AdapterStatus.UNAVAILABLE
    priority: int = 0
    
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


class AdapterRegistry:
    """
    Registry of all available adapters.
    Manages initialization, status checking, and routing of adapter calls.
    """
    
    def __init__(self):
        self._adapters: Dict[str, AdapterInfo] = {}
        self._initialized = False
        self._default_adapters_loaded = False
    
    def register(
        self,
        name: str,
        display_name: str,
        description: str,
        category: AdapterCategory,
        adapter_class: Type[BaseAdapter],
        config: Optional[AdapterConfig] = None,
        priority: int = 0
    ) -> None:
        """
        Register an adapter.
        
        Args:
            name: Unique name
            display_name: Display name
            description: Description
            category: Category
            adapter_class: Adapter class
            config: Optional configuration
            priority: Priority (higher = preferred)
        """
        if config is None:
            config = AdapterConfig(
                name=name,
                display_name=display_name,
                description=description,
                base_url=""
            )
        
        info = AdapterInfo(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            config=config,
            adapter_class=adapter_class,
            priority=priority
        )
        
        self._adapters[name] = info
    
    def register_instance(self, adapter: BaseAdapter, priority: int = 0) -> None:
        """
        Register an already instantiated adapter.
        
        Args:
            adapter: Adapter instance
            priority: Priority
        """
        info = AdapterInfo(
            name=adapter.name,
            display_name=adapter.display_name,
            description=adapter.description,
            category=self._get_category(adapter.name),
            config=adapter.config,
            adapter_class=type(adapter),
            instance=adapter,
            priority=priority
        )
        
        self._adapters[adapter.name] = info
    
    def _get_category(self, name: str) -> AdapterCategory:
        """Determine category from adapter name"""
        name_lower = name.lower()
        
        if any(x in name_lower for x in ["github", "gitlab", "bitbucket", "vercel"]):
            return AdapterCategory.DEVELOPMENT
        elif any(x in name_lower for x in ["asana", "linear", "jira"]):
            return AdapterCategory.PROJECT_MANAGEMENT
        elif any(x in name_lower for x in ["teams", "slack", "discord"]):
            return AdapterCategory.COMMUNICATION
        elif any(x in name_lower for x in ["calendly", "calendar"]):
            return AdapterCategory.CALENDAR
        elif any(x in name_lower for x in ["notion", "box", "drive"]):
            return AdapterCategory.DOCUMENTS
        elif any(x in name_lower for x in ["netlify", "heroku"]):
            return AdapterCategory.DEPLOYMENT
        elif any(x in name_lower for x in ["wix", "shopify"]):
            return AdapterCategory.BUSINESS
        elif any(x in name_lower for x in ["gamma", "canva", "excalidraw", "figma"]):
            return AdapterCategory.DESIGN
        else:
            return AdapterCategory.OTHER
    
    def get(self, name: str) -> Optional[BaseAdapter]:
        """
        Get an adapter instance by name.
        Initializes the adapter if not already initialized.
        
        Args:
            name: Adapter name
            
        Returns:
            Adapter instance or None
        """
        info = self._adapters.get(name)
        if not info:
            return None
        
        # Initialize if needed
        if not info.instance:
            try:
                info.instance = info.adapter_class(info.config)
            except Exception as e:
                print(f"Error initializing adapter {name}: {e}")
                return None
        
        return info.instance
    
    def get_info(self, name: str) -> Optional[AdapterInfo]:
        """Get adapter info by name"""
        return self._adapters.get(name)
    
    def list(self, category: Optional[AdapterCategory] = None) -> List[AdapterInfo]:
        """
        List all registered adapters.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of adapter infos
        """
        if category:
            return [
                info for info in self._adapters.values()
                if info.category == category
            ]
        return list(self._adapters.values())
    
    def list_by_priority(self) -> List[AdapterInfo]:
        """List adapters sorted by priority (highest first)"""
        return sorted(
            self._adapters.values(),
            key=lambda x: x.priority,
            reverse=True
        )
    
    def list_available(self) -> List[AdapterInfo]:
        """List only available adapters"""
        return [
            info for info in self._adapters.values()
            if info.instance and info.instance.is_available()
        ]
    
    def list_configured(self) -> List[AdapterInfo]:
        """List only configured adapters"""
        return [
            info for info in self._adapters.values()
            if info.instance and info.instance.status == AdapterStatus.CONFIGURED
        ]
    
    async def initialize_all(self) -> Dict[str, bool]:
        """
        Initialize all registered adapters.
        
        Returns:
            Dict of adapter names to success status
        """
        results = {}
        
        for name, info in self._adapters.items():
            if not info.instance:
                try:
                    info.instance = info.adapter_class(info.config)
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
    
    async def check_all_statuses(self) -> Dict[str, AdapterStatus]:
        """
        Check status of all adapters.
        
        Returns:
            Dict of adapter names to status
        """
        statuses = {}
        
        for name, info in self._adapters.items():
            if info.instance:
                try:
                    status = await info.instance.check_status()
                    info.status = status
                    statuses[name] = status
                except Exception:
                    statuses[name] = AdapterStatus.ERROR
            else:
                statuses[name] = AdapterStatus.UNAVAILABLE
        
        return statuses
    
    async def execute(
        self,
        adapter_name: str,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """
        Execute an action on a specific adapter.
        
        Args:
            adapter_name: Name of adapter
            action: Action to execute
            parameters: Action parameters
            
        Returns:
            AdapterResult
        """
        adapter = self.get(adapter_name)
        if not adapter:
            return AdapterResult(
                success=False,
                error=f"Adapter {adapter_name} not found"
            )
        
        if not adapter.is_available():
            return AdapterResult(
                success=False,
                error=f"Adapter {adapter_name} is not available (status: {adapter.status.value})"
            )
        
        try:
            return await adapter.execute(action, parameters)
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )
    
    async def execute_any(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None,
        category: Optional[AdapterCategory] = None
    ) -> AdapterResult:
        """
        Execute an action on any available adapter that supports it.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            category: Optional category filter
            
        Returns:
            AdapterResult from the first successful adapter
        """
        # Try adapters in priority order
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
        
        return AdapterResult(
            success=False,
            error=f"No available adapter supports action: {action}"
        )
    
    def get_status(self) -> Dict[str, AdapterStatus]:
        """
        Get status of all adapters.
        
        Returns:
            Dict of adapter names to status
        """
        return {
            name: info.status.value if info.instance else AdapterStatus.UNAVAILABLE.value
            for name, info in self._adapters.items()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        categories = {cat.value: 0 for cat in AdapterCategory}
        statuses = {status.value: 0 for status in AdapterStatus}
        
        for info in self._adapters.values():
            categories[info.category.value] += 1
            
            if info.instance:
                status = info.instance.status.value
            else:
                status = AdapterStatus.UNAVAILABLE.value
            statuses[status] += 1
        
        return {
            "total": len(self._adapters),
            "by_category": categories,
            "by_status": statuses
        }
    
    def unregister(self, name: str) -> bool:
        """Unregister an adapter"""
        if name in self._adapters:
            info = self._adapters[name]
            if info.instance:
                # Clean up instance if needed
                pass
            del self._adapters[name]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all registrations"""
        self._adapters.clear()
    
    def load_default_adapters(self) -> None:
        """Load default adapters"""
        if self._default_adapters_loaded:
            return
        
        # Import and register default adapters
        try:
            from .teams_adapter import MicrosoftTeamsAdapter, TeamsConfig
            self.register(
                "microsoft_teams",
                "Microsoft Teams",
                "Microsoft Teams adapter for messages, teams, and meetings",
                AdapterCategory.COMMUNICATION,
                MicrosoftTeamsAdapter,
                TeamsConfig()
            )
        except Exception:
            pass
        
        try:
            from .calendly_adapter import CalendlyAdapter, CalendlyConfig
            self.register(
                "calendly",
                "Calendly",
                "Calendly adapter for scheduling and availability",
                AdapterCategory.CALENDAR,
                CalendlyAdapter,
                CalendlyConfig()
            )
        except Exception:
            pass
        
        try:
            from .vercel_adapter import VercelAdapter, VercelConfig
            self.register(
                "vercel",
                "Vercel",
                "Vercel adapter for deployments and projects",
                AdapterCategory.DEPLOYMENT,
                VercelAdapter,
                VercelConfig()
            )
        except Exception:
            pass
        
        self._default_adapters_loaded = True
    
    def save_to_file(self, path: Union[str, Path]) -> None:
        """Save registry to file"""
        path = Path(path)
        data = {
            "adapters": [
                info.to_dict() for info in self._adapters.values()
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
        
        for info_data in data.get("adapters", []):
            # This is a simplified load - full implementation would need
            # to reconstruct adapter classes
            pass


# Global registry instance
registry = AdapterRegistry()
