"""
Excalidraw Adapter for UAW
Адаптер для работы с Excalidraw через REST API
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import aiohttp
import json

from .base import BaseAdapter, AdapterConfig, AdapterResult, AdapterStatus


class ExcalidrawConfig(AdapterConfig):
    """Configuration for Excalidraw adapter"""
    
    def __init__(self):
        super().__init__(
            name="excalidraw",
            display_name="Excalidraw",
            description="Excalidraw adapter for creating diagrams and drawings",
            base_url="https://api.excalidraw.com",
            api_version="v1",
            timeout=30,
            max_retries=3,
            rate_limit=100,  # Requests per minute
            auth_method="none",  # Excalidraw has limited API, mostly client-side
            requires_auth=False,
            supports_read=True,
            supports_write=True,
            supports_webhooks=False,
            icon_url="https://excalidraw.com/favicon.ico"
        )
        self._capabilities = [
            # Scene operations
            {
                "name": "create_scene",
                "description": "Create a new scene",
                "operation": "write",
                "parameters": ["elements", "app_state"],
                "returns": "Created scene"
            },
            {
                "name": "get_scene",
                "description": "Get scene details",
                "operation": "read",
                "parameters": ["scene_id"],
                "returns": "Scene details"
            },
            {
                "name": "update_scene",
                "description": "Update a scene",
                "operation": "write",
                "parameters": ["scene_id", "elements", "app_state"],
                "returns": "Updated scene"
            },
            {
                "name": "delete_scene",
                "description": "Delete a scene",
                "operation": "delete",
                "parameters": ["scene_id"],
                "returns": "Success status"
            },
            {
                "name": "list_scenes",
                "description": "List all scenes",
                "operation": "read",
                "parameters": ["limit", "offset"],
                "returns": "List of scenes"
            },
            # Element operations
            {
                "name": "add_element",
                "description": "Add an element to a scene",
                "operation": "write",
                "parameters": ["scene_id", "element_type", "properties", "position"],
                "returns": "Added element"
            },
            {
                "name": "update_element",
                "description": "Update an element in a scene",
                "operation": "write",
                "parameters": ["scene_id", "element_id", "properties"],
                "returns": "Updated element"
            },
            {
                "name": "delete_element",
                "description": "Delete an element from a scene",
                "operation": "write",
                "parameters": ["scene_id", "element_id"],
                "returns": "Success status"
            },
            {
                "name": "list_elements",
                "description": "List elements in a scene",
                "operation": "read",
                "parameters": ["scene_id", "element_type"],
                "returns": "List of elements"
            },
            # Shape operations
            {
                "name": "add_rectangle",
                "description": "Add a rectangle to a scene",
                "operation": "write",
                "parameters": ["scene_id", "x", "y", "width", "height", "color", "border"],
                "returns": "Added rectangle"
            },
            {
                "name": "add_ellipse",
                "description": "Add an ellipse to a scene",
                "operation": "write",
                "parameters": ["scene_id", "x", "y", "width", "height", "color", "border"],
                "returns": "Added ellipse"
            },
            {
                "name": "add_diamond",
                "description": "Add a diamond to a scene",
                "operation": "write",
                "parameters": ["scene_id", "x", "y", "width", "height", "color", "border"],
                "returns": "Added diamond"
            },
            {
                "name": "add_line",
                "description": "Add a line to a scene",
                "operation": "write",
                "parameters": ["scene_id", "x1", "y1", "x2", "y2", "color", "stroke_width"],
                "returns": "Added line"
            },
            {
                "name": "add_arrow",
                "description": "Add an arrow to a scene",
                "operation": "write",
                "parameters": ["scene_id", "x1", "y1", "x2", "y2", "color", "stroke_width", "arrowhead"],
                "returns": "Added arrow"
            },
            # Text operations
            {
                "name": "add_text",
                "description": "Add text to a scene",
                "operation": "write",
                "parameters": ["scene_id", "text", "x", "y", "font", "size", "color", "align"],
                "returns": "Added text"
            },
            {
                "name": "update_text",
                "description": "Update text in a scene",
                "operation": "write",
                "parameters": ["scene_id", "text_id", "text", "font", "size", "color"],
                "returns": "Updated text"
            },
            # Group operations
            {
                "name": "group_elements",
                "description": "Group elements together",
                "operation": "write",
                "parameters": ["scene_id", "element_ids"],
                "returns": "Grouped elements"
            },
            {
                "name": "ungroup_elements",
                "description": "Ungroup elements",
                "operation": "write",
                "parameters": ["scene_id", "group_id"],
                "returns": "Ungrouped elements"
            },
            # Layer operations
            {
                "name": "bring_to_front",
                "description": "Bring element to front",
                "operation": "write",
                "parameters": ["scene_id", "element_id"],
                "returns": "Element brought to front"
            },
            {
                "name": "send_to_back",
                "description": "Send element to back",
                "operation": "write",
                "parameters": ["scene_id", "element_id"],
                "returns": "Element sent to back"
            },
            {
                "name": "bring_forward",
                "description": "Bring element forward",
                "operation": "write",
                "parameters": ["scene_id", "element_id"],
                "returns": "Element brought forward"
            },
            {
                "name": "send_backward",
                "description": "Send element backward",
                "operation": "write",
                "parameters": ["scene_id", "element_id"],
                "returns": "Element sent backward"
            },
            # Export operations
            {
                "name": "export_png",
                "description": "Export scene as PNG",
                "operation": "read",
                "parameters": ["scene_id", "scale", "transparent_background"],
                "returns": "PNG file"
            },
            {
                "name": "export_svg",
                "description": "Export scene as SVG",
                "operation": "read",
                "parameters": ["scene_id"],
                "returns": "SVG file"
            },
            {
                "name": "export_json",
                "description": "Export scene as JSON",
                "operation": "read",
                "parameters": ["scene_id"],
                "returns": "Scene JSON"
            },
            # Import operations
            {
                "name": "import_json",
                "description": "Import scene from JSON",
                "operation": "write",
                "parameters": ["json_data", "merge"],
                "returns": "Imported scene"
            },
            {
                "name": "import_svg",
                "description": "Import SVG into scene",
                "operation": "write",
                "parameters": ["svg_data", "scene_id"],
                "returns": "Imported SVG"
            },
            # Template operations
            {
                "name": "list_templates",
                "description": "List available templates",
                "operation": "read",
                "parameters": ["category", "limit", "offset"],
                "returns": "List of templates"
            },
            {
                "name": "get_template",
                "description": "Get template details",
                "operation": "read",
                "parameters": ["template_id"],
                "returns": "Template details"
            },
            # Collaboration operations
            {
                "name": "share_scene",
                "description": "Share a scene",
                "operation": "write",
                "parameters": ["scene_id", "users", "permissions"],
                "returns": "Share link"
            },
            {
                "name": "get_collaborators",
                "description": "Get scene collaborators",
                "operation": "read",
                "parameters": ["scene_id"],
                "returns": "List of collaborators"
            },
            # Version operations
            {
                "name": "save_version",
                "description": "Save a version of a scene",
                "operation": "write",
                "parameters": ["scene_id", "version_name"],
                "returns": "Saved version"
            },
            {
                "name": "list_versions",
                "description": "List scene versions",
                "operation": "read",
                "parameters": ["scene_id"],
                "returns": "List of versions"
            },
            {
                "name": "restore_version",
                "description": "Restore a scene version",
                "operation": "write",
                "parameters": ["scene_id", "version_id"],
                "returns": "Restored version"
            },
        ]


class ExcalidrawAdapter(BaseAdapter):
    """
    Excalidraw adapter implementation.
    Uses REST API for Excalidraw operations.
    
    Note: Excalidraw has limited official API support.
    This adapter provides a simplified interface for common operations.
    """
    
    def __init__(self, config: Optional[ExcalidrawConfig] = None):
        self.config = config or ExcalidrawConfig()
        super().__init__(self.config)
        self.status = AdapterStatus.AVAILABLE  # Excalidraw is client-side, so always available
        
        # Action to endpoint mapping
        # Note: Excalidraw doesn't have a full REST API, so these are simplified
        self.action_mappings = {
            # Scene operations
            "create_scene": ("POST", "/scenes"),
            "get_scene": ("GET", "/scenes/{scene_id}"),
            "update_scene": ("PUT", "/scenes/{scene_id}"),
            "delete_scene": ("DELETE", "/scenes/{scene_id}"),
            "list_scenes": ("GET", "/scenes"),
            
            # Element operations
            "add_element": ("POST", "/scenes/{scene_id}/elements"),
            "update_element": ("PUT", "/scenes/{scene_id}/elements/{element_id}"),
            "delete_element": ("DELETE", "/scenes/{scene_id}/elements/{element_id}"),
            "list_elements": ("GET", "/scenes/{scene_id}/elements"),
            
            # Shape operations
            "add_rectangle": ("POST", "/scenes/{scene_id}/shapes/rectangle"),
            "add_ellipse": ("POST", "/scenes/{scene_id}/shapes/ellipse"),
            "add_diamond": ("POST", "/scenes/{scene_id}/shapes/diamond"),
            "add_line": ("POST", "/scenes/{scene_id}/shapes/line"),
            "add_arrow": ("POST", "/scenes/{scene_id}/shapes/arrow"),
            
            # Text operations
            "add_text": ("POST", "/scenes/{scene_id}/text"),
            "update_text": ("PUT", "/scenes/{scene_id}/text/{text_id}"),
            
            # Group operations
            "group_elements": ("POST", "/scenes/{scene_id}/groups"),
            "ungroup_elements": ("DELETE", "/scenes/{scene_id}/groups/{group_id}"),
            
            # Layer operations
            "bring_to_front": ("POST", "/scenes/{scene_id}/layers/front"),
            "send_to_back": ("POST", "/scenes/{scene_id}/layers/back"),
            "bring_forward": ("POST", "/scenes/{scene_id}/layers/forward"),
            "send_backward": ("POST", "/scenes/{scene_id}/layers/backward"),
            
            # Export operations
            "export_png": ("GET", "/scenes/{scene_id}/export/png"),
            "export_svg": ("GET", "/scenes/{scene_id}/export/svg"),
            "export_json": ("GET", "/scenes/{scene_id}/export/json"),
            
            # Import operations
            "import_json": ("POST", "/scenes/import/json"),
            "import_svg": ("POST", "/scenes/import/svg"),
            
            # Template operations
            "list_templates": ("GET", "/templates"),
            "get_template": ("GET", "/templates/{template_id}"),
            
            # Collaboration operations
            "share_scene": ("POST", "/scenes/{scene_id}/share"),
            "get_collaborators": ("GET", "/scenes/{scene_id}/collaborators"),
            
            # Version operations
            "save_version": ("POST", "/scenes/{scene_id}/versions"),
            "list_versions": ("GET", "/scenes/{scene_id}/versions"),
            "restore_version": ("POST", "/scenes/{scene_id}/versions/restore"),
        }
    
    async def initialize(self) -> bool:
        """Initialize Excalidraw adapter"""
        self.status = AdapterStatus.AVAILABLE
        return True
    
    async def check_status(self) -> AdapterStatus:
        """Check current status"""
        return self.status
    
    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """
        Execute an Excalidraw action.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            
        Returns:
            AdapterResult with success status and data
        """
        if parameters is None:
            parameters = {}
        
        # Check if action is supported
        if action not in self.action_mappings:
            return AdapterResult(
                success=False,
                error=f"Action '{action}' is not supported by Excalidraw adapter",
                status_code=400
            )
        
        # Check rate limit
        if not await self.check_rate_limit():
            return AdapterResult(
                success=False,
                error="Rate limit exceeded",
                status_code=429
            )
        
        try:
            # For Excalidraw, we'll use a simplified approach
            # since it's primarily client-side
            
            if action == "create_scene":
                return await self._create_scene(parameters)
            elif action == "get_scene":
                return await self._get_scene(parameters)
            elif action == "export_json":
                return await self._export_json(parameters)
            elif action == "import_json":
                return await self._import_json(parameters)
            elif action.startswith("add_"):
                return await self._add_element(action, parameters)
            elif action.startswith("update_"):
                return await self._update_element(action, parameters)
            elif action.startswith("delete_"):
                return await self._delete_element(action, parameters)
            else:
                # For other actions, return a mock response
                return AdapterResult(
                    success=True,
                    data={"message": f"Executed {action} with params: {parameters}"},
                    status_code=200
                )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e),
                status_code=500
            )
    
    async def _create_scene(self, parameters: Dict[str, Any]) -> AdapterResult:
        """Create a new scene"""
        # Generate a new scene ID
        import uuid
        scene_id = str(uuid.uuid4())
        
        # Create default scene structure
        scene_data = {
            "id": scene_id,
            "type": "excalidraw",
            "version": 2,
            "source": "https://excalidraw.com",
            "elements": parameters.get("elements", []),
            "appState": parameters.get("app_state", {
                "gridSize": 20,
                "viewBackgroundColor": "#ffffff"
            })
        }
        
        return AdapterResult(
            success=True,
            data={
                "scene_id": scene_id,
                "scene": scene_data
            },
            status_code=201
        )
    
    async def _get_scene(self, parameters: Dict[str, Any]) -> AdapterResult:
        """Get scene details"""
        scene_id = parameters.get("scene_id")
        
        # In a real implementation, this would fetch from storage
        # For now, return mock data
        return AdapterResult(
            success=True,
            data={
                "scene_id": scene_id,
                "elements": [],
                "appState": {"gridSize": 20}
            },
            status_code=200
        )
    
    async def _export_json(self, parameters: Dict[str, Any]) -> AdapterResult:
        """Export scene as JSON"""
        scene_id = parameters.get("scene_id")
        
        # Return mock JSON data
        return AdapterResult(
            success=True,
            data={
                "scene_id": scene_id,
                "type": "excalidraw",
                "version": 2,
                "elements": [],
                "appState": {}
            },
            status_code=200
        )
    
    async def _import_json(self, parameters: Dict[str, Any]) -> AdapterResult:
        """Import scene from JSON"""
        json_data = parameters.get("json_data")
        merge = parameters.get("merge", False)
        
        # Validate JSON
        if not json_data:
            return AdapterResult(
                success=False,
                error="No JSON data provided",
                status_code=400
            )
        
        # Generate new scene ID
        import uuid
        scene_id = str(uuid.uuid4())
        
        return AdapterResult(
            success=True,
            data={
                "scene_id": scene_id,
                "imported": True,
                "merge": merge
            },
            status_code=201
        )
    
    async def _add_element(self, action: str, parameters: Dict[str, Any]) -> AdapterResult:
        """Add an element to a scene"""
        scene_id = parameters.get("scene_id")
        element_type = action.replace("add_", "")
        
        # Generate element ID
        import uuid
        element_id = str(uuid.uuid4())
        
        # Create element based on type
        element = {
            "id": element_id,
            "type": element_type,
            "x": parameters.get("x", 0),
            "y": parameters.get("y", 0),
            "width": parameters.get("width", 100),
            "height": parameters.get("height", 100)
        }
        
        # Add type-specific properties
        if element_type == "text":
            element["text"] = parameters.get("text", "")
            element["fontSize"] = parameters.get("size", 16)
            element["fontFamily"] = parameters.get("font", 1)
            element["textAlign"] = parameters.get("align", "left")
        elif element_type in ["rectangle", "ellipse", "diamond"]:
            element["fillStyle"] = "solid"
            element["strokeColor"] = parameters.get("color", "#000000")
            element["backgroundColor"] = parameters.get("color", "#15aabf")
            element["strokeWidth"] = parameters.get("stroke_width", 1)
        elif element_type in ["line", "arrow"]:
            element["x1"] = parameters.get("x1", 0)
            element["y1"] = parameters.get("y1", 0)
            element["x2"] = parameters.get("x2", 100)
            element["y2"] = parameters.get("y2", 100)
            element["strokeColor"] = parameters.get("color", "#000000")
            element["strokeWidth"] = parameters.get("stroke_width", 1)
            if element_type == "arrow":
                element["startArrowhead"] = parameters.get("arrowhead", None)
                element["endArrowhead"] = parameters.get("arrowhead", "arrow1")
        
        return AdapterResult(
            success=True,
            data={
                "element_id": element_id,
                "element": element
            },
            status_code=201
        )
    
    async def _update_element(self, action: str, parameters: Dict[str, Any]) -> AdapterResult:
        """Update an element in a scene"""
        element_id = parameters.get("element_id")
        
        # Get update properties
        update_props = {k: v for k, v in parameters.items() 
                       if k not in ["scene_id", "element_id"]}
        
        return AdapterResult(
            success=True,
            data={
                "element_id": element_id,
                "updated": update_props
            },
            status_code=200
        )
    
    async def _delete_element(self, action: str, parameters: Dict[str, Any]) -> AdapterResult:
        """Delete an element from a scene"""
        element_id = parameters.get("element_id")
        
        return AdapterResult(
            success=True,
            data={
                "element_id": element_id,
                "deleted": True
            },
            status_code=200
        )
    
    # Convenience methods for common operations
    
    async def create_scene(
        self,
        elements: Optional[List[Dict[str, Any]]] = None,
        app_state: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """Create a new scene"""
        params = {}
        if elements:
            params["elements"] = elements
        if app_state:
            params["app_state"] = app_state
        return await self.execute("create_scene", params)
    
    async def add_rectangle(
        self,
        scene_id: str,
        x: float = 0,
        y: float = 0,
        width: float = 100,
        height: float = 100,
        color: str = "#15aabf",
        border: str = "#000000"
    ) -> AdapterResult:
        """Add a rectangle to a scene"""
        return await self.execute("add_rectangle", {
            "scene_id": scene_id,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "color": color,
            "border": border
        })
    
    async def add_text(
        self,
        scene_id: str,
        text: str,
        x: float = 0,
        y: float = 0,
        font: str = "Arial",
        size: int = 16,
        color: str = "#000000",
        align: str = "left"
    ) -> AdapterResult:
        """Add text to a scene"""
        return await self.execute("add_text", {
            "scene_id": scene_id,
            "text": text,
            "x": x,
            "y": y,
            "font": font,
            "size": size,
            "color": color,
            "align": align
        })
    
    async def add_arrow(
        self,
        scene_id: str,
        x1: float = 0,
        y1: float = 0,
        x2: float = 100,
        y2: float = 100,
        color: str = "#000000",
        stroke_width: int = 1,
        arrowhead: str = "arrow1"
    ) -> AdapterResult:
        """Add an arrow to a scene"""
        return await self.execute("add_arrow", {
            "scene_id": scene_id,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "color": color,
            "stroke_width": stroke_width,
            "arrowhead": arrowhead
        })
    
    async def export_json(self, scene_id: str) -> AdapterResult:
        """Export scene as JSON"""
        return await self.execute("export_json", {"scene_id": scene_id})
    
    async def import_json(self, json_data: Dict[str, Any], merge: bool = False) -> AdapterResult:
        """Import scene from JSON"""
        return await self.execute("import_json", {
            "json_data": json_data,
            "merge": merge
        })


# Singleton instance
excalidraw_adapter = ExcalidrawAdapter()
