"""
Gamma Adapter for UAW
Адаптер для работы с Gamma через REST API
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import aiohttp
import json

from .base import BaseAdapter, AdapterConfig, AdapterResult, AdapterStatus


class GammaConfig(AdapterConfig):
    """Configuration for Gamma adapter"""
    
    def __init__(self):
        super().__init__(
            name="gamma",
            display_name="Gamma",
            description="Gamma adapter for creating presentations and graphics",
            base_url="https://gamma.app/api",
            api_version="v1",
            timeout=30,
            max_retries=3,
            rate_limit=60,  # Requests per minute
            auth_method="bearer_token",
            requires_auth=True,
            supports_read=True,
            supports_write=True,
            supports_webhooks=False,
            icon_url="https://gamma.app/favicon.ico"
        )
        self._capabilities = [
            # Presentation operations
            {
                "name": "create_presentation",
                "description": "Create a new presentation",
                "operation": "write",
                "parameters": ["title", "theme", "template"],
                "returns": "Created presentation"
            },
            {
                "name": "get_presentation",
                "description": "Get presentation details",
                "operation": "read",
                "parameters": ["presentation_id"],
                "returns": "Presentation details"
            },
            {
                "name": "update_presentation",
                "description": "Update a presentation",
                "operation": "write",
                "parameters": ["presentation_id", "title", "theme"],
                "returns": "Updated presentation"
            },
            {
                "name": "delete_presentation",
                "description": "Delete a presentation",
                "operation": "delete",
                "parameters": ["presentation_id"],
                "returns": "Success status"
            },
            {
                "name": "list_presentations",
                "description": "List all presentations",
                "operation": "read",
                "parameters": ["limit", "offset", "query"],
                "returns": "List of presentations"
            },
            # Slide operations
            {
                "name": "create_slide",
                "description": "Create a new slide",
                "operation": "write",
                "parameters": ["presentation_id", "title", "layout", "position"],
                "returns": "Created slide"
            },
            {
                "name": "get_slide",
                "description": "Get slide details",
                "operation": "read",
                "parameters": ["slide_id"],
                "returns": "Slide details"
            },
            {
                "name": "update_slide",
                "description": "Update a slide",
                "operation": "write",
                "parameters": ["slide_id", "title", "content", "layout"],
                "returns": "Updated slide"
            },
            {
                "name": "delete_slide",
                "description": "Delete a slide",
                "operation": "delete",
                "parameters": ["slide_id"],
                "returns": "Success status"
            },
            {
                "name": "list_slides",
                "description": "List slides in a presentation",
                "operation": "read",
                "parameters": ["presentation_id"],
                "returns": "List of slides"
            },
            # Content operations
            {
                "name": "add_text",
                "description": "Add text to a slide",
                "operation": "write",
                "parameters": ["slide_id", "text", "style", "position"],
                "returns": "Added text"
            },
            {
                "name": "add_image",
                "description": "Add an image to a slide",
                "operation": "write",
                "parameters": ["slide_id", "image_url", "position", "size"],
                "returns": "Added image"
            },
            {
                "name": "add_shape",
                "description": "Add a shape to a slide",
                "operation": "write",
                "parameters": ["slide_id", "shape_type", "position", "size", "color"],
                "returns": "Added shape"
            },
            {
                "name": "add_chart",
                "description": "Add a chart to a slide",
                "operation": "write",
                "parameters": ["slide_id", "chart_type", "data", "position"],
                "returns": "Added chart"
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
            # Theme operations
            {
                "name": "list_themes",
                "description": "List available themes",
                "operation": "read",
                "parameters": ["limit", "offset"],
                "returns": "List of themes"
            },
            {
                "name": "apply_theme",
                "description": "Apply a theme to a presentation",
                "operation": "write",
                "parameters": ["presentation_id", "theme_id"],
                "returns": "Applied theme"
            },
            # Export operations
            {
                "name": "export_pdf",
                "description": "Export presentation as PDF",
                "operation": "read",
                "parameters": ["presentation_id", "quality", "include_notes"],
                "returns": "PDF file"
            },
            {
                "name": "export_pptx",
                "description": "Export presentation as PowerPoint",
                "operation": "read",
                "parameters": ["presentation_id", "format"],
                "returns": "PPTX file"
            },
            {
                "name": "export_html",
                "description": "Export presentation as HTML",
                "operation": "read",
                "parameters": ["presentation_id", "include_assets"],
                "returns": "HTML file"
            },
            # Sharing operations
            {
                "name": "create_share_link",
                "description": "Create a share link for a presentation",
                "operation": "write",
                "parameters": ["presentation_id", "access_level", "expires_at"],
                "returns": "Share link"
            },
            {
                "name": "get_share_link",
                "description": "Get share link for a presentation",
                "operation": "read",
                "parameters": ["presentation_id"],
                "returns": "Share link"
            },
            {
                "name": "revoke_share_link",
                "description": "Revoke share link for a presentation",
                "operation": "write",
                "parameters": ["presentation_id"],
                "returns": "Success status"
            },
            # Collaboration operations
            {
                "name": "add_collaborator",
                "description": "Add a collaborator to a presentation",
                "operation": "write",
                "parameters": ["presentation_id", "user_email", "role"],
                "returns": "Added collaborator"
            },
            {
                "name": "remove_collaborator",
                "description": "Remove a collaborator from a presentation",
                "operation": "write",
                "parameters": ["presentation_id", "user_id"],
                "returns": "Success status"
            },
            {
                "name": "list_collaborators",
                "description": "List collaborators for a presentation",
                "operation": "read",
                "parameters": ["presentation_id"],
                "returns": "List of collaborators"
            },
        ]


class GammaAdapter(BaseAdapter):
    """
    Gamma adapter implementation.
    Uses REST API for Gamma operations.
    """
    
    def __init__(self, config: Optional[GammaConfig] = None):
        self.config = config or GammaConfig()
        super().__init__(self.config)
        self.status = AdapterStatus.UNAVAILABLE
        
        # Action to endpoint mapping
        self.action_mappings = {
            # Presentation operations
            "create_presentation": ("POST", "/presentations"),
            "get_presentation": ("GET", "/presentations/{presentation_id}"),
            "update_presentation": ("PUT", "/presentations/{presentation_id}"),
            "delete_presentation": ("DELETE", "/presentations/{presentation_id}"),
            "list_presentations": ("GET", "/presentations"),
            
            # Slide operations
            "create_slide": ("POST", "/presentations/{presentation_id}/slides"),
            "get_slide": ("GET", "/slides/{slide_id}"),
            "update_slide": ("PUT", "/slides/{slide_id}"),
            "delete_slide": ("DELETE", "/slides/{slide_id}"),
            "list_slides": ("GET", "/presentations/{presentation_id}/slides"),
            
            # Content operations
            "add_text": ("POST", "/slides/{slide_id}/text"),
            "add_image": ("POST", "/slides/{slide_id}/images"),
            "add_shape": ("POST", "/slides/{slide_id}/shapes"),
            "add_chart": ("POST", "/slides/{slide_id}/charts"),
            
            # Template operations
            "list_templates": ("GET", "/templates"),
            "get_template": ("GET", "/templates/{template_id}"),
            
            # Theme operations
            "list_themes": ("GET", "/themes"),
            "apply_theme": ("PUT", "/presentations/{presentation_id}/theme"),
            
            # Export operations
            "export_pdf": ("GET", "/presentations/{presentation_id}/export/pdf"),
            "export_pptx": ("GET", "/presentations/{presentation_id}/export/pptx"),
            "export_html": ("GET", "/presentations/{presentation_id}/export/html"),
            
            # Sharing operations
            "create_share_link": ("POST", "/presentations/{presentation_id}/share"),
            "get_share_link": ("GET", "/presentations/{presentation_id}/share"),
            "revoke_share_link": ("DELETE", "/presentations/{presentation_id}/share"),
            
            # Collaboration operations
            "add_collaborator": ("POST", "/presentations/{presentation_id}/collaborators"),
            "remove_collaborator": ("DELETE", "/presentations/{presentation_id}/collaborators/{user_id}"),
            "list_collaborators": ("GET", "/presentations/{presentation_id}/collaborators"),
        }
    
    async def initialize(self) -> bool:
        """Initialize Gamma adapter"""
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
        Execute a Gamma action.
        
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
                error="Gamma adapter requires authentication",
                status_code=401
            )
        
        # Check if action is supported
        if action not in self.action_mappings:
            return AdapterResult(
                success=False,
                error=f"Action '{action}' is not supported by Gamma adapter",
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
        if action in ["create_presentation", "update_presentation", "create_slide", 
                      "update_slide", "add_text", "add_image", "add_shape", 
                      "add_chart", "apply_theme", "create_share_link", "add_collaborator"]:
            request_data["json"] = clean_params
        
        # For GET, DELETE requests with query parameters
        elif action in ["list_presentations", "list_slides", "list_templates", 
                        "list_themes", "export_pdf", "export_pptx", "export_html"]:
            request_data["params"] = clean_params
        
        return request_data
    
    # Convenience methods for common operations
    
    async def create_presentation(
        self,
        title: str,
        theme: Optional[str] = None,
        template: Optional[str] = None
    ) -> AdapterResult:
        """Create a new presentation"""
        params = {"title": title}
        if theme:
            params["theme"] = theme
        if template:
            params["template"] = template
        return await self.execute("create_presentation", params)
    
    async def get_presentation(self, presentation_id: str) -> AdapterResult:
        """Get presentation details"""
        return await self.execute("get_presentation", {"presentation_id": presentation_id})
    
    async def list_presentations(
        self,
        limit: int = 100,
        offset: int = 0,
        query: Optional[str] = None
    ) -> AdapterResult:
        """List all presentations"""
        params = {"limit": limit, "offset": offset}
        if query:
            params["query"] = query
        return await self.execute("list_presentations", params)
    
    async def create_slide(
        self,
        presentation_id: str,
        title: str,
        layout: str = "title_and_content",
        position: Optional[int] = None
    ) -> AdapterResult:
        """Create a new slide"""
        params = {
            "presentation_id": presentation_id,
            "title": title,
            "layout": layout
        }
        if position is not None:
            params["position"] = position
        return await self.execute("create_slide", params)
    
    async def add_text(
        self,
        slide_id: str,
        text: str,
        style: Optional[Dict[str, Any]] = None,
        position: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """Add text to a slide"""
        params = {
            "slide_id": slide_id,
            "text": text
        }
        if style:
            params["style"] = style
        if position:
            params["position"] = position
        return await self.execute("add_text", params)
    
    async def add_image(
        self,
        slide_id: str,
        image_url: str,
        position: Optional[Dict[str, Any]] = None,
        size: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """Add an image to a slide"""
        params = {
            "slide_id": slide_id,
            "image_url": image_url
        }
        if position:
            params["position"] = position
        if size:
            params["size"] = size
        return await self.execute("add_image", params)
    
    async def export_pdf(
        self,
        presentation_id: str,
        quality: str = "high",
        include_notes: bool = False
    ) -> AdapterResult:
        """Export presentation as PDF"""
        params = {
            "presentation_id": presentation_id,
            "quality": quality,
            "include_notes": include_notes
        }
        return await self.execute("export_pdf", params)
    
    async def create_share_link(
        self,
        presentation_id: str,
        access_level: str = "view",
        expires_at: Optional[str] = None
    ) -> AdapterResult:
        """Create a share link for a presentation"""
        params = {
            "presentation_id": presentation_id,
            "access_level": access_level
        }
        if expires_at:
            params["expires_at"] = expires_at
        return await self.execute("create_share_link", params)


# Singleton instance
gamma_adapter = GammaAdapter()
