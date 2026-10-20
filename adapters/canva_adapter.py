"""
Canva Adapter for UAW
Адаптер для работы с Canva через REST API
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import aiohttp
import json

from .base import BaseAdapter, AdapterConfig, AdapterResult, AdapterStatus


class CanvaConfig(AdapterConfig):
    """Configuration for Canva adapter"""
    
    def __init__(self):
        super().__init__(
            name="canva",
            display_name="Canva",
            description="Canva adapter for creating graphics and designs",
            base_url="https://api.canva.com/rest/v1",
            api_version="v1",
            timeout=30,
            max_retries=3,
            rate_limit=100,  # Requests per minute
            auth_method="oauth2",
            requires_auth=True,
            supports_read=True,
            supports_write=True,
            supports_webhooks=False,
            icon_url="https://www.canva.com/favicon.ico"
        )
        self._capabilities = [
            # Design operations
            {
                "name": "create_design",
                "description": "Create a new design",
                "operation": "write",
                "parameters": ["design_type", "title", "template_id", "dimensions"],
                "returns": "Created design"
            },
            {
                "name": "get_design",
                "description": "Get design details",
                "operation": "read",
                "parameters": ["design_id", "include"],
                "returns": "Design details"
            },
            {
                "name": "update_design",
                "description": "Update a design",
                "operation": "write",
                "parameters": ["design_id", "title", "elements"],
                "returns": "Updated design"
            },
            {
                "name": "delete_design",
                "description": "Delete a design",
                "operation": "delete",
                "parameters": ["design_id"],
                "returns": "Success status"
            },
            {
                "name": "list_designs",
                "description": "List all designs",
                "operation": "read",
                "parameters": ["limit", "offset", "query", "design_type"],
                "returns": "List of designs"
            },
            # Element operations
            {
                "name": "add_element",
                "description": "Add an element to a design",
                "operation": "write",
                "parameters": ["design_id", "element_type", "properties", "position"],
                "returns": "Added element"
            },
            {
                "name": "update_element",
                "description": "Update an element in a design",
                "operation": "write",
                "parameters": ["design_id", "element_id", "properties"],
                "returns": "Updated element"
            },
            {
                "name": "delete_element",
                "description": "Delete an element from a design",
                "operation": "write",
                "parameters": ["design_id", "element_id"],
                "returns": "Success status"
            },
            {
                "name": "list_elements",
                "description": "List elements in a design",
                "operation": "read",
                "parameters": ["design_id", "element_type"],
                "returns": "List of elements"
            },
            # Text operations
            {
                "name": "add_text",
                "description": "Add text to a design",
                "operation": "write",
                "parameters": ["design_id", "text", "font", "size", "color", "position"],
                "returns": "Added text"
            },
            {
                "name": "update_text",
                "description": "Update text in a design",
                "operation": "write",
                "parameters": ["design_id", "text_id", "text", "font", "size", "color"],
                "returns": "Updated text"
            },
            # Image operations
            {
                "name": "add_image",
                "description": "Add an image to a design",
                "operation": "write",
                "parameters": ["design_id", "image_url", "position", "size", "crop"],
                "returns": "Added image"
            },
            {
                "name": "upload_image",
                "description": "Upload an image",
                "operation": "write",
                "parameters": ["design_id", "image_file", "position"],
                "returns": "Uploaded image"
            },
            {
                "name": "replace_image",
                "description": "Replace an image in a design",
                "operation": "write",
                "parameters": ["design_id", "image_id", "new_image_url"],
                "returns": "Replaced image"
            },
            # Shape operations
            {
                "name": "add_shape",
                "description": "Add a shape to a design",
                "operation": "write",
                "parameters": ["design_id", "shape_type", "position", "size", "color", "border"],
                "returns": "Added shape"
            },
            {
                "name": "update_shape",
                "description": "Update a shape in a design",
                "operation": "write",
                "parameters": ["design_id", "shape_id", "properties"],
                "returns": "Updated shape"
            },
            # Background operations
            {
                "name": "set_background",
                "description": "Set design background",
                "operation": "write",
                "parameters": ["design_id", "color", "image_url", "transparency"],
                "returns": "Set background"
            },
            {
                "name": "remove_background",
                "description": "Remove background from a design",
                "operation": "write",
                "parameters": ["design_id"],
                "returns": "Removed background"
            },
            # Template operations
            {
                "name": "list_templates",
                "description": "List available templates",
                "operation": "read",
                "parameters": ["category", "limit", "offset", "query"],
                "returns": "List of templates"
            },
            {
                "name": "get_template",
                "description": "Get template details",
                "operation": "read",
                "parameters": ["template_id"],
                "returns": "Template details"
            },
            {
                "name": "search_templates",
                "description": "Search for templates",
                "operation": "read",
                "parameters": ["query", "category", "limit"],
                "returns": "Search results"
            },
            # Export operations
            {
                "name": "export_png",
                "description": "Export design as PNG",
                "operation": "read",
                "parameters": ["design_id", "quality", "dpi", "transparent_background"],
                "returns": "PNG file"
            },
            {
                "name": "export_jpeg",
                "description": "Export design as JPEG",
                "operation": "read",
                "parameters": ["design_id", "quality", "dpi"],
                "returns": "JPEG file"
            },
            {
                "name": "export_pdf",
                "description": "Export design as PDF",
                "operation": "read",
                "parameters": ["design_id", "quality", "include_bleed", "crop_marks"],
                "returns": "PDF file"
            },
            {
                "name": "export_svg",
                "description": "Export design as SVG",
                "operation": "read",
                "parameters": ["design_id", "simplify"],
                "returns": "SVG file"
            },
            {
                "name": "export_video",
                "description": "Export design as video",
                "operation": "read",
                "parameters": ["design_id", "format", "duration", "fps"],
                "returns": "Video file"
            },
            # Sharing operations
            {
                "name": "create_share_link",
                "description": "Create a share link for a design",
                "operation": "write",
                "parameters": ["design_id", "access_level", "expires_at", "password"],
                "returns": "Share link"
            },
            {
                "name": "get_share_link",
                "description": "Get share link for a design",
                "operation": "read",
                "parameters": ["design_id"],
                "returns": "Share link"
            },
            {
                "name": "revoke_share_link",
                "description": "Revoke share link for a design",
                "operation": "write",
                "parameters": ["design_id"],
                "returns": "Success status"
            },
            # Folder operations
            {
                "name": "list_folders",
                "description": "List folders",
                "operation": "read",
                "parameters": ["parent_folder_id", "limit", "offset"],
                "returns": "List of folders"
            },
            {
                "name": "create_folder",
                "description": "Create a new folder",
                "operation": "write",
                "parameters": ["name", "parent_folder_id"],
                "returns": "Created folder"
            },
            {
                "name": "delete_folder",
                "description": "Delete a folder",
                "operation": "delete",
                "parameters": ["folder_id"],
                "returns": "Success status"
            },
            # Brand operations
            {
                "name": "get_brand",
                "description": "Get brand details",
                "operation": "read",
                "parameters": ["brand_id"],
                "returns": "Brand details"
            },
            {
                "name": "list_brands",
                "description": "List available brands",
                "operation": "read",
                "parameters": ["limit", "offset"],
                "returns": "List of brands"
            },
            # Team operations
            {
                "name": "list_teams",
                "description": "List teams",
                "operation": "read",
                "parameters": ["limit", "offset"],
                "returns": "List of teams"
            },
            {
                "name": "get_team",
                "description": "Get team details",
                "operation": "read",
                "parameters": ["team_id"],
                "returns": "Team details"
            },
            # Color palette operations
            {
                "name": "get_color_palette",
                "description": "Get color palette",
                "operation": "read",
                "parameters": ["palette_id"],
                "returns": "Color palette"
            },
            {
                "name": "list_color_palettes",
                "description": "List color palettes",
                "operation": "read",
                "parameters": ["limit", "offset"],
                "returns": "List of color palettes"
            },
        ]


class CanvaAdapter(BaseAdapter):
    """
    Canva adapter implementation.
    Uses REST API for Canva operations.
    """
    
    def __init__(self, config: Optional[CanvaConfig] = None):
        self.config = config or CanvaConfig()
        super().__init__(self.config)
        self.status = AdapterStatus.UNAVAILABLE
        
        # Action to endpoint mapping
        self.action_mappings = {
            # Design operations
            "create_design": ("POST", "/designs"),
            "get_design": ("GET", "/designs/{design_id}"),
            "update_design": ("PUT", "/designs/{design_id}"),
            "delete_design": ("DELETE", "/designs/{design_id}"),
            "list_designs": ("GET", "/designs"),
            
            # Element operations
            "add_element": ("POST", "/designs/{design_id}/elements"),
            "update_element": ("PUT", "/designs/{design_id}/elements/{element_id}"),
            "delete_element": ("DELETE", "/designs/{design_id}/elements/{element_id}"),
            "list_elements": ("GET", "/designs/{design_id}/elements"),
            
            # Text operations
            "add_text": ("POST", "/designs/{design_id}/text"),
            "update_text": ("PUT", "/designs/{design_id}/text/{text_id}"),
            
            # Image operations
            "add_image": ("POST", "/designs/{design_id}/images"),
            "upload_image": ("POST", "/designs/{design_id}/images/upload"),
            "replace_image": ("PUT", "/designs/{design_id}/images/{image_id}"),
            
            # Shape operations
            "add_shape": ("POST", "/designs/{design_id}/shapes"),
            "update_shape": ("PUT", "/designs/{design_id}/shapes/{shape_id}"),
            
            # Background operations
            "set_background": ("PUT", "/designs/{design_id}/background"),
            "remove_background": ("DELETE", "/designs/{design_id}/background"),
            
            # Template operations
            "list_templates": ("GET", "/templates"),
            "get_template": ("GET", "/templates/{template_id}"),
            "search_templates": ("GET", "/templates/search"),
            
            # Export operations
            "export_png": ("GET", "/designs/{design_id}/export/png"),
            "export_jpeg": ("GET", "/designs/{design_id}/export/jpeg"),
            "export_pdf": ("GET", "/designs/{design_id}/export/pdf"),
            "export_svg": ("GET", "/designs/{design_id}/export/svg"),
            "export_video": ("GET", "/designs/{design_id}/export/video"),
            
            # Sharing operations
            "create_share_link": ("POST", "/designs/{design_id}/share"),
            "get_share_link": ("GET", "/designs/{design_id}/share"),
            "revoke_share_link": ("DELETE", "/designs/{design_id}/share"),
            
            # Folder operations
            "list_folders": ("GET", "/folders"),
            "create_folder": ("POST", "/folders"),
            "delete_folder": ("DELETE", "/folders/{folder_id}"),
            
            # Brand operations
            "get_brand": ("GET", "/brands/{brand_id}"),
            "list_brands": ("GET", "/brands"),
            
            # Color palette operations
            "get_color_palette": ("GET", "/color-palettes/{palette_id}"),
            "list_color_palettes": ("GET", "/color-palettes"),
            
            # Team operations
            "list_teams": ("GET", "/teams"),
            "get_team": ("GET", "/teams/{team_id}"),
        }
    
    async def initialize(self) -> bool:
        """Initialize Canva adapter"""
        try:
            # Test connection
            result = await self._make_request(
                method="GET",
                endpoint="/health"
            )
            if result.get("success", False):
                self.status = AdapterStatus.AVAILABLE
                return True
            else:
                self.status = AdapterStatus.UNAUTHORISED
                return False
        except Exception as e:
            self.last_error = str(e)
            self.status = AdapterStatus.ERROR
            return False
    
    async def check_status(self) -> AdapterStatus:
        """Check current status"""
        return self.status
    
    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """
        Execute a Canva action.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            
        Returns:
            AdapterResult with success status and data
        """
        if parameters is None:
            parameters = {}
        
        # Check if we're authenticated
        if self.status == AdapterStatus.UNAUTHORISED:
            return AdapterResult(
                success=False,
                error="Canva adapter requires authentication",
                status_code=401
            )
        
        # Check if action is supported
        if action not in self.action_mappings:
            return AdapterResult(
                success=False,
                error=f"Action '{action}' is not supported by Canva adapter",
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
            # Get HTTP method and endpoint
            method, endpoint = self.action_mappings[action]
            
            # Format endpoint with parameters
            formatted_endpoint = self._format_endpoint(endpoint, parameters)
            
            # Prepare request data
            request_data = self._prepare_request_data(action, parameters)
            
            # Make request
            result = await self._make_request(
                method=method,
                endpoint=formatted_endpoint,
                json_data=request_data.get("json"),
                data=request_data.get("data"),
                headers=request_data.get("headers", {})
            )
            
            return AdapterResult(
                success=result.get("success", True),
                data=result.get("data"),
                error=result.get("error"),
                status_code=result.get("status_code", 200),
                metadata=result.get("metadata")
            )
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e),
                status_code=500
            )
    
    def _format_endpoint(self, endpoint: str, parameters: Dict[str, Any]) -> str:
        """Format endpoint with path parameters"""
        # Replace {param} with actual values
        for key, value in parameters.items():
            if isinstance(value, str):
                endpoint = endpoint.replace(f"{{{key}}}", value)
        return endpoint
    
    def _prepare_request_data(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data based on action"""
        request_data = {}
        
        # Remove path parameters from request data
        clean_params = {k: v for k, v in parameters.items() if not isinstance(v, str) or "{" not in v}
        
        # For POST, PUT, PATCH requests
        if action in ["create_design", "update_design", "add_element", "update_element",
                      "delete_element", "add_text", "update_text", "add_image",
                      "upload_image", "replace_image", "add_shape", "update_shape",
                      "set_background", "remove_background", "create_share_link",
                      "revoke_share_link", "create_folder", "delete_folder"]:
            request_data["json"] = clean_params
        
        # For GET, DELETE requests with query parameters
        elif action in ["list_designs", "list_elements", "list_templates", 
                        "get_template", "search_templates", "export_png", "export_jpeg",
                        "export_pdf", "export_svg", "export_video", "get_share_link",
                        "list_folders", "get_brand", "list_brands", "get_color_palette",
                        "list_color_palettes", "list_teams", "get_team"]:
            request_data["params"] = clean_params
        
        # For file upload
        if action == "upload_image":
            request_data["data"] = clean_params
        
        return request_data
    
    # Convenience methods for common operations
    
    async def create_design(
        self,
        design_type: str = "custom",
        title: str = "New Design",
        template_id: Optional[str] = None,
        dimensions: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """Create a new design"""
        params = {
            "design_type": design_type,
            "title": title
        }
        if template_id:
            params["template_id"] = template_id
        if dimensions:
            params["dimensions"] = dimensions
        return await self.execute("create_design", params)
    
    async def get_design(self, design_id: str, include: Optional[List[str]] = None) -> AdapterResult:
        """Get design details"""
        params = {"design_id": design_id}
        if include:
            params["include"] = ",".join(include)
        return await self.execute("get_design", params)
    
    async def list_designs(
        self,
        limit: int = 100,
        offset: int = 0,
        query: Optional[str] = None,
        design_type: Optional[str] = None
    ) -> AdapterResult:
        """List all designs"""
        params = {"limit": limit, "offset": offset}
        if query:
            params["query"] = query
        if design_type:
            params["design_type"] = design_type
        return await self.execute("list_designs", params)
    
    async def add_text(
        self,
        design_id: str,
        text: str,
        font: str = "Arial",
        size: int = 16,
        color: str = "#000000",
        position: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """Add text to a design"""
        params = {
            "design_id": design_id,
            "text": text,
            "font": font,
            "size": size,
            "color": color
        }
        if position:
            params["position"] = position
        return await self.execute("add_text", params)
    
    async def add_image(
        self,
        design_id: str,
        image_url: str,
        position: Optional[Dict[str, Any]] = None,
        size: Optional[Dict[str, Any]] = None,
        crop: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """Add an image to a design"""
        params = {
            "design_id": design_id,
            "image_url": image_url
        }
        if position:
            params["position"] = position
        if size:
            params["size"] = size
        if crop:
            params["crop"] = crop
        return await self.execute("add_image", params)
    
    async def export_png(
        self,
        design_id: str,
        quality: int = 100,
        dpi: int = 300,
        transparent_background: bool = False
    ) -> AdapterResult:
        """Export design as PNG"""
        params = {
            "design_id": design_id,
            "quality": quality,
            "dpi": dpi,
            "transparent_background": transparent_background
        }
        return await self.execute("export_png", params)
    
    async def export_pdf(
        self,
        design_id: str,
        quality: int = 100,
        include_bleed: bool = False,
        crop_marks: bool = False
    ) -> AdapterResult:
        """Export design as PDF"""
        params = {
            "design_id": design_id,
            "quality": quality,
            "include_bleed": include_bleed,
            "crop_marks": crop_marks
        }
        return await self.execute("export_pdf", params)
    
    async def create_share_link(
        self,
        design_id: str,
        access_level: str = "view",
        expires_at: Optional[str] = None,
        password: Optional[str] = None
    ) -> AdapterResult:
        """Create a share link for a design"""
        params = {
            "design_id": design_id,
            "access_level": access_level
        }
        if expires_at:
            params["expires_at"] = expires_at
        if password:
            params["password"] = password
        return await self.execute("create_share_link", params)
    
    async def search_templates(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 50
    ) -> AdapterResult:
        """Search for templates"""
        params = {
            "query": query,
            "limit": limit
        }
        if category:
            params["category"] = category
        return await self.execute("search_templates", params)


# Singleton instance
canva_adapter = CanvaAdapter()
