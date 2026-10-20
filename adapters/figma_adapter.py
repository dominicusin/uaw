"""
Figma Adapter for UAW
Адаптер для работы с Figma через REST API
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import aiohttp
import json

from .base import BaseAdapter, AdapterConfig, AdapterResult, AdapterStatus


class FigmaConfig(AdapterConfig):
    """Configuration for Figma adapter"""
    
    def __init__(self):
        super().__init__(
            name="figma",
            display_name="Figma",
            description="Figma adapter for design files, components, and collaboration",
            base_url="https://api.figma.com/v1",
            api_version="v1",
            timeout=30,
            max_retries=3,
            rate_limit=120,  # Figma API rate limit per minute
            auth_method="bearer_token",
            requires_auth=True,
            supports_read=True,
            supports_write=True,
            supports_webhooks=True,
            icon_url="https://www.figma.com/file/favicon.png"
        )
        self._capabilities = [
            # File operations
            {
                "name": "list_files",
                "description": "List files accessible to the user",
                "operation": "read",
                "parameters": ["team_id", "limit", "cursor"],
                "returns": "List of files"
            },
            {
                "name": "get_file",
                "description": "Get file details",
                "operation": "read",
                "parameters": ["file_key", "depth", "geometry", "plugin_data"],
                "returns": "File details"
            },
            {
                "name": "get_file_nodes",
                "description": "Get specific nodes from a file",
                "operation": "read",
                "parameters": ["file_key", "node_ids", "depth", "geometry"],
                "returns": "File nodes"
            },
            {
                "name": "create_file",
                "description": "Create a new file",
                "operation": "write",
                "parameters": ["name", "team_id", "description", "thumbnail"],
                "returns": "Created file"
            },
            {
                "name": "delete_file",
                "description": "Delete a file",
                "operation": "delete",
                "parameters": ["file_key"],
                "returns": "Success status"
            },
            # Node operations
            {
                "name": "get_node",
                "description": "Get a specific node",
                "operation": "read",
                "parameters": ["file_key", "node_id", "depth", "geometry"],
                "returns": "Node details"
            },
            {
                "name": "get_node_children",
                "description": "Get children of a node",
                "operation": "read",
                "parameters": ["file_key", "node_id", "depth"],
                "returns": "Node children"
            },
            # Component operations
            {
                "name": "list_components",
                "description": "List components in a file",
                "operation": "read",
                "parameters": ["file_key", "limit", "cursor"],
                "returns": "List of components"
            },
            {
                "name": "get_component",
                "description": "Get component details",
                "operation": "read",
                "parameters": ["file_key", "component_id"],
                "returns": "Component details"
            },
            {
                "name": "create_component",
                "description": "Create a new component",
                "operation": "write",
                "parameters": ["file_key", "name", "description", "node_ids"],
                "returns": "Created component"
            },
            {
                "name": "delete_component",
                "description": "Delete a component",
                "operation": "delete",
                "parameters": ["file_key", "component_id"],
                "returns": "Success status"
            },
            # Style operations
            {
                "name": "list_styles",
                "description": "List styles in a file",
                "operation": "read",
                "parameters": ["file_key", "style_type"],
                "returns": "List of styles"
            },
            {
                "name": "get_style",
                "description": "Get style details",
                "operation": "read",
                "parameters": ["file_key", "style_id"],
                "returns": "Style details"
            },
            {
                "name": "create_style",
                "description": "Create a new style",
                "operation": "write",
                "parameters": ["file_key", "name", "style_type", "properties"],
                "returns": "Created style"
            },
            {
                "name": "delete_style",
                "description": "Delete a style",
                "operation": "delete",
                "parameters": ["file_key", "style_id"],
                "returns": "Success status"
            },
            # Page operations
            {
                "name": "list_pages",
                "description": "List pages in a file",
                "operation": "read",
                "parameters": ["file_key"],
                "returns": "List of pages"
            },
            {
                "name": "get_page",
                "description": "Get page details",
                "operation": "read",
                "parameters": ["file_key", "page_id"],
                "returns": "Page details"
            },
            {
                "name": "create_page",
                "description": "Create a new page",
                "operation": "write",
                "parameters": ["file_key", "name", "position"],
                "returns": "Created page"
            },
            {
                "name": "delete_page",
                "description": "Delete a page",
                "operation": "delete",
                "parameters": ["file_key", "page_id"],
                "returns": "Success status"
            },
            # Image operations
            {
                "name": "list_images",
                "description": "List images in a file",
                "operation": "read",
                "parameters": ["file_key", "limit", "cursor"],
                "returns": "List of images"
            },
            {
                "name": "get_image",
                "description": "Get image details",
                "operation": "read",
                "parameters": ["file_key", "image_id"],
                "returns": "Image details"
            },
            {
                "name": "get_image_fills",
                "description": "Get image fills for a file",
                "operation": "read",
                "parameters": ["file_key"],
                "returns": "Image fills"
            },
            {
                "name": "upload_image",
                "description": "Upload an image",
                "operation": "write",
                "parameters": ["file_key", "image_data"],
                "returns": "Uploaded image"
            },
            # Export operations
            {
                "name": "export_frames",
                "description": "Export frames as images",
                "operation": "read",
                "parameters": ["file_key", "node_ids", "format", "scale", "suffix", "constrain_proportions"],
                "returns": "Export URLs"
            },
            {
                "name": "export_page",
                "description": "Export a page as images",
                "operation": "read",
                "parameters": ["file_key", "page_id", "format", "scale"],
                "returns": "Export URLs"
            },
            {
                "name": "export_component",
                "description": "Export a component as images",
                "operation": "read",
                "parameters": ["file_key", "component_id", "format", "scale"],
                "returns": "Export URLs"
            },
            {
                "name": "export_component_set",
                "description": "Export a component set",
                "operation": "read",
                "parameters": ["file_key", "component_set_id", "format", "scale"],
                "returns": "Export URLs"
            },
            # Comment operations
            {
                "name": "list_comments",
                "description": "List comments in a file",
                "operation": "read",
                "parameters": ["file_key", "limit", "cursor"],
                "returns": "List of comments"
            },
            {
                "name": "get_comment",
                "description": "Get comment details",
                "operation": "read",
                "parameters": ["file_key", "comment_id"],
                "returns": "Comment details"
            },
            {
                "name": "create_comment",
                "description": "Create a comment",
                "operation": "write",
                "parameters": ["file_key", "node_id", "message", "client_meta"],
                "returns": "Created comment"
            },
            {
                "name": "delete_comment",
                "description": "Delete a comment",
                "operation": "delete",
                "parameters": ["file_key", "comment_id"],
                "returns": "Success status"
            },
            # Version operations
            {
                "name": "list_versions",
                "description": "List file versions",
                "operation": "read",
                "parameters": ["file_key", "limit", "cursor"],
                "returns": "List of versions"
            },
            {
                "name": "get_version",
                "description": "Get version details",
                "operation": "read",
                "parameters": ["file_key", "version_id"],
                "returns": "Version details"
            },
            {
                "name": "restore_version",
                "description": "Restore a file version",
                "operation": "write",
                "parameters": ["file_key", "version_id"],
                "returns": "Restored version"
            },
            # Team operations
            {
                "name": "list_teams",
                "description": "List teams the user belongs to",
                "operation": "read",
                "parameters": ["limit", "cursor"],
                "returns": "List of teams"
            },
            {
                "name": "get_team",
                "description": "Get team details",
                "operation": "read",
                "parameters": ["team_id"],
                "returns": "Team details"
            },
            {
                "name": "list_team_files",
                "description": "List files in a team",
                "operation": "read",
                "parameters": ["team_id", "limit", "cursor"],
                "returns": "List of team files"
            },
            # Project operations
            {
                "name": "list_projects",
                "description": "List projects in a team",
                "operation": "read",
                "parameters": ["team_id", "limit", "cursor"],
                "returns": "List of projects"
            },
            {
                "name": "get_project",
                "description": "Get project details",
                "operation": "read",
                "parameters": ["project_id"],
                "returns": "Project details"
            },
            {
                "name": "create_project",
                "description": "Create a new project",
                "operation": "write",
                "parameters": ["team_id", "name", "description", "color"],
                "returns": "Created project"
            },
            {
                "name": "delete_project",
                "description": "Delete a project",
                "operation": "delete",
                "parameters": ["project_id"],
                "returns": "Success status"
            },
            # User operations
            {
                "name": "get_me",
                "description": "Get current user details",
                "operation": "read",
                "parameters": [],
                "returns": "Current user details"
            },
            {
                "name": "get_user",
                "description": "Get user details",
                "operation": "read",
                "parameters": ["user_id"],
                "returns": "User details"
            },
            # Webhook operations
            {
                "name": "list_webhooks",
                "description": "List webhooks",
                "operation": "read",
                "parameters": ["team_id", "limit", "cursor"],
                "returns": "List of webhooks"
            },
            {
                "name": "create_webhook",
                "description": "Create a webhook",
                "operation": "write",
                "parameters": ["team_id", "url", "events", "passphrase"],
                "returns": "Created webhook"
            },
            {
                "name": "delete_webhook",
                "description": "Delete a webhook",
                "operation": "delete",
                "parameters": ["webhook_id"],
                "returns": "Success status"
            },
        ]


class FigmaAdapter(BaseAdapter):
    """
    Figma adapter implementation.
    Uses REST API for Figma operations.
    """
    
    def __init__(self, config: Optional[FigmaConfig] = None):
        self.config = config or FigmaConfig()
        super().__init__(self.config)
        self.status = AdapterStatus.UNAUTHORISED
        
        # Action to endpoint mapping
        self.action_mappings = {
            # File operations
            "list_files": ("GET", "/files"),
            "get_file": ("GET", "/files/{file_key}"),
            "get_file_nodes": ("GET", "/files/{file_key}/nodes"),
            "create_file": ("POST", "/files"),
            "delete_file": ("DELETE", "/files/{file_key}"),
            
            # Node operations
            "get_node": ("GET", "/files/{file_key}/nodes/{node_id}"),
            "get_node_children": ("GET", "/files/{file_key}/nodes/{node_id}/children"),
            
            # Component operations
            "list_components": ("GET", "/files/{file_key}/components"),
            "get_component": ("GET", "/files/{file_key}/components/{component_id}"),
            "create_component": ("POST", "/files/{file_key}/components"),
            "delete_component": ("DELETE", "/files/{file_key}/components/{component_id}"),
            
            # Style operations
            "list_styles": ("GET", "/files/{file_key}/styles"),
            "get_style": ("GET", "/files/{file_key}/styles/{style_id}"),
            "create_style": ("POST", "/files/{file_key}/styles"),
            "delete_style": ("DELETE", "/files/{file_key}/styles/{style_id}"),
            
            # Page operations
            "list_pages": ("GET", "/files/{file_key}/pages"),
            "get_page": ("GET", "/files/{file_key}/pages/{page_id}"),
            "create_page": ("POST", "/files/{file_key}/pages"),
            "delete_page": ("DELETE", "/files/{file_key}/pages/{page_id}"),
            
            # Image operations
            "list_images": ("GET", "/files/{file_key}/images"),
            "get_image": ("GET", "/files/{file_key}/images/{image_id}"),
            "get_image_fills": ("GET", "/files/{file_key}/images/fills"),
            "upload_image": ("POST", "/files/{file_key}/images"),
            
            # Export operations
            "export_frames": ("GET", "/files/{file_key}/export"),
            "export_page": ("GET", "/files/{file_key}/pages/{page_id}/export"),
            "export_component": ("GET", "/files/{file_key}/components/{component_id}/export"),
            "export_component_set": ("GET", "/files/{file_key}/component_sets/{component_set_id}/export"),
            
            # Comment operations
            "list_comments": ("GET", "/files/{file_key}/comments"),
            "get_comment": ("GET", "/files/{file_key}/comments/{comment_id}"),
            "create_comment": ("POST", "/files/{file_key}/comments"),
            "delete_comment": ("DELETE", "/files/{file_key}/comments/{comment_id}"),
            
            # Version operations
            "list_versions": ("GET", "/files/{file_key}/versions"),
            "get_version": ("GET", "/files/{file_key}/versions/{version_id}"),
            "restore_version": ("POST", "/files/{file_key}/versions/{version_id}/restore"),
            
            # Team operations
            "list_teams": ("GET", "/teams"),
            "get_team": ("GET", "/teams/{team_id}"),
            "list_team_files": ("GET", "/teams/{team_id}/files"),
            
            # Project operations
            "list_projects": ("GET", "/teams/{team_id}/projects"),
            "get_project": ("GET", "/projects/{project_id}"),
            "create_project": ("POST", "/teams/{team_id}/projects"),
            "delete_project": ("DELETE", "/projects/{project_id}"),
            
            # User operations
            "get_me": ("GET", "/me"),
            "get_user": ("GET", "/users/{user_id}"),
            
            # Webhook operations
            "list_webhooks": ("GET", "/teams/{team_id}/webhooks"),
            "create_webhook": ("POST", "/teams/{team_id}/webhooks"),
            "delete_webhook": ("DELETE", "/webhooks/{webhook_id}"),
        }
    
    async def initialize(self) -> bool:
        """Initialize Figma adapter"""
        try:
            # Test connection
            result = await self._make_request(
                method="GET",
                endpoint="/me"
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
        Execute a Figma action.
        
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
                error="Figma adapter requires authentication",
                status_code=401
            )
        
        # Check if action is supported
        if action not in self.action_mappings:
            return AdapterResult(
                success=False,
                error=f"Action '{action}' is not supported by Figma adapter",
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
        if action in ["create_file", "create_component", "create_style", "create_page",
                      "upload_image", "create_comment", "create_webhook", "create_project",
                      "restore_version"]:
            request_data["json"] = clean_params
        
        # For GET requests with query parameters
        elif action in ["list_files", "get_file", "get_file_nodes", "list_components",
                        "get_component", "list_styles", "get_style", "list_pages",
                        "get_page", "list_images", "get_image", "get_image_fills",
                        "export_frames", "export_page", "export_component",
                        "export_component_set", "list_comments", "get_comment",
                        "list_versions", "get_version", "list_teams", "get_team",
                        "list_team_files", "list_projects", "get_project",
                        "get_me", "get_user", "list_webhooks"]:
            request_data["params"] = clean_params
        
        return request_data
    
    # Convenience methods for common operations
    
    async def get_file(self, file_key: str, depth: int = 1, geometry: str = "paths") -> AdapterResult:
        """Get file details"""
        return await self.execute("get_file", {
            "file_key": file_key,
            "depth": depth,
            "geometry": geometry
        })
    
    async def list_files(self, team_id: Optional[str] = None, limit: int = 100) -> AdapterResult:
        """List files accessible to the user"""
        params = {"limit": limit}
        if team_id:
            params["team_id"] = team_id
        return await self.execute("list_files", params)
    
    async def get_node(self, file_key: str, node_id: str, depth: int = 1) -> AdapterResult:
        """Get a specific node"""
        return await self.execute("get_node", {
            "file_key": file_key,
            "node_id": node_id,
            "depth": depth
        })
    
    async def list_components(self, file_key: str, limit: int = 100) -> AdapterResult:
        """List components in a file"""
        return await self.execute("list_components", {
            "file_key": file_key,
            "limit": limit
        })
    
    async def export_frames(
        self,
        file_key: str,
        node_ids: Optional[List[str]] = None,
        format: str = "png",
        scale: float = 1.0,
        suffix: Optional[str] = None,
        constrain_proportions: bool = True
    ) -> AdapterResult:
        """Export frames as images"""
        params = {
            "file_key": file_key,
            "format": format,
            "scale": scale,
            "constrain_proportions": constrain_proportions
        }
        if node_ids:
            params["node_ids"] = ",".join(node_ids)
        if suffix:
            params["suffix"] = suffix
        return await self.execute("export_frames", params)
    
    async def get_me(self) -> AdapterResult:
        """Get current user details"""
        return await self.execute("get_me", {})
    
    async def list_teams(self, limit: int = 100) -> AdapterResult:
        """List teams the user belongs to"""
        return await self.execute("list_teams", {"limit": limit})
    
    async def create_comment(
        self,
        file_key: str,
        node_id: str,
        message: str,
        client_meta: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """Create a comment"""
        params = {
            "file_key": file_key,
            "node_id": node_id,
            "message": message
        }
        if client_meta:
            params["client_meta"] = client_meta
        return await self.execute("create_comment", params)


# Singleton instance
figma_adapter = FigmaAdapter()
