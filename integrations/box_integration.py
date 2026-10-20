"""
Box Integration for UAW
Интеграция с Box через MCP
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from .base import (
    BaseIntegration, IntegrationConfig, IntegrationResult,
    IntegrationStatus, IntegrationCapability, IntegrationError
)


class BoxConfig(IntegrationConfig):
    """Configuration for Box integration"""
    
    def __init__(self):
        super().__init__(
            name="box",
            display_name="Box",
            description="Box integration for file storage, sharing, and collaboration",
            integration_type="mcp",
            base_url="https://api.box.com/2.0",
            api_version="v2",
            timeout=30,
            max_retries=3,
            rate_limit=1000,  # Box API rate limit per hour
            auth_method="oauth2",
            requires_auth=True,
            supports_read=True,
            supports_write=True,
            supports_webhooks=True,
            supports_search=True,
            max_page_size=1000,
            icon_url="https://cdn.worldvectorlogo.com/logos/box-2.svg",
            documentation_url="https://developer.box.com/reference/"
        )
        self._capabilities = [
            # File operations
            IntegrationCapability(
                name="list_files",
                description="List files in a folder",
                operation="read",
                parameters=["folder_id", "fields", "limit", "offset"],
                returns="List of files"
            ),
            IntegrationCapability(
                name="get_file",
                description="Get file details",
                operation="read",
                parameters=["file_id", "fields"],
                returns="File details"
            ),
            IntegrationCapability(
                name="download_file",
                description="Download a file",
                operation="read",
                parameters=["file_id", "version_id"],
                returns="File content"
            ),
            IntegrationCapability(
                name="upload_file",
                description="Upload a file",
                operation="write",
                parameters=["folder_id", "file_name", "file_content", "content_type"],
                returns="Uploaded file"
            ),
            IntegrationCapability(
                name="create_folder",
                description="Create a new folder",
                operation="write",
                parameters=["parent_folder_id", "name", "description"],
                returns="Created folder"
            ),
            IntegrationCapability(
                name="delete_file",
                description="Delete a file",
                operation="delete",
                parameters=["file_id", "recursive"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="delete_folder",
                description="Delete a folder",
                operation="delete",
                parameters=["folder_id", "recursive"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="copy_file",
                description="Copy a file",
                operation="write",
                parameters=["file_id", "parent_folder_id", "name"],
                returns="Copied file"
            ),
            IntegrationCapability(
                name="move_file",
                description="Move a file",
                operation="write",
                parameters=["file_id", "parent_folder_id", "name"],
                returns="Moved file"
            ),
            IntegrationCapability(
                name="rename_file",
                description="Rename a file",
                operation="write",
                parameters=["file_id", "name"],
                returns="Renamed file"
            ),
            # Search
            IntegrationCapability(
                name="search",
                description="Search for files and folders",
                operation="read",
                parameters=["query", "type", "fields", "limit", "offset"],
                returns="Search results"
            ),
            # Sharing
            IntegrationCapability(
                name="create_shared_link",
                description="Create a shared link for a file",
                operation="write",
                parameters=["file_id", "access", "password", "unshared_at"],
                returns="Shared link"
            ),
            IntegrationCapability(
                name="get_shared_link",
                description="Get shared link for a file",
                operation="read",
                parameters=["file_id"],
                returns="Shared link"
            ),
            IntegrationCapability(
                name="remove_shared_link",
                description="Remove shared link from a file",
                operation="write",
                parameters=["file_id"],
                returns="Success status"
            ),
            # Comments
            IntegrationCapability(
                name="list_comments",
                description="List comments on a file",
                operation="read",
                parameters=["file_id", "fields", "limit", "offset"],
                returns="List of comments"
            ),
            IntegrationCapability(
                name="create_comment",
                description="Create a comment on a file",
                operation="write",
                parameters=["file_id", "message", "tagged_message"],
                returns="Created comment"
            ),
            IntegrationCapability(
                name="delete_comment",
                description="Delete a comment",
                operation="delete",
                parameters=["comment_id"],
                returns="Success status"
            ),
            # Versions
            IntegrationCapability(
                name="list_file_versions",
                description="List versions of a file",
                operation="read",
                parameters=["file_id", "fields", "limit", "offset"],
                returns="List of file versions"
            ),
            IntegrationCapability(
                name="get_file_version",
                description="Get a specific file version",
                operation="read",
                parameters=["file_id", "version_id", "fields"],
                returns="File version details"
            ),
            IntegrationCapability(
                name="promote_version",
                description="Promote a file version",
                operation="write",
                parameters=["file_id", "version_id"],
                returns="Promoted version"
            ),
            # Metadata
            IntegrationCapability(
                name="get_metadata",
                description="Get file metadata",
                operation="read",
                parameters=["file_id", "scope", "template_key"],
                returns="File metadata"
            ),
            IntegrationCapability(
                name="set_metadata",
                description="Set file metadata",
                operation="write",
                parameters=["file_id", "scope", "data"],
                returns="Updated metadata"
            ),
            # Trash
            IntegrationCapability(
                name="get_trash_items",
                description="List items in trash",
                operation="read",
                parameters=["fields", "limit", "offset"],
                returns="List of trash items"
            ),
            IntegrationCapability(
                name="restore_from_trash",
                description="Restore an item from trash",
                operation="write",
                parameters=["file_id", "name", "parent_folder_id"],
                returns="Restored item"
            ),
            IntegrationCapability(
                name="permanently_delete",
                description="Permanently delete an item",
                operation="delete",
                parameters=["file_id"],
                returns="Success status"
            ),
            # User operations
            IntegrationCapability(
                name="get_user",
                description="Get user details",
                operation="read",
                parameters=["user_id", "fields"],
                returns="User details"
            ),
            IntegrationCapability(
                name="get_current_user",
                description="Get current user details",
                operation="read",
                parameters=["fields"],
                returns="Current user details"
            ),
            # Collaborations
            IntegrationCapability(
                name="list_collaborations",
                description="List collaborations for a folder",
                operation="read",
                parameters=["folder_id", "fields", "limit", "offset"],
                returns="List of collaborations"
            ),
            IntegrationCapability(
                name="create_collaboration",
                description="Create a collaboration",
                operation="write",
                parameters=["folder_id", "user_id", "role", "access_level"],
                returns="Created collaboration"
            ),
            IntegrationCapability(
                name="delete_collaboration",
                description="Delete a collaboration",
                operation="delete",
                parameters=["collaboration_id"],
                returns="Success status"
            ),
            # Webhooks
            IntegrationCapability(
                name="list_webhooks",
                description="List webhooks",
                operation="read",
                parameters=["fields", "limit", "offset"],
                returns="List of webhooks"
            ),
            IntegrationCapability(
                name="create_webhook",
                description="Create a webhook",
                operation="write",
                parameters=["target_id", "target_type", "address", "triggers"],
                returns="Created webhook"
            ),
            IntegrationCapability(
                name="delete_webhook",
                description="Delete a webhook",
                operation="delete",
                parameters=["webhook_id"],
                returns="Success status"
            ),
        ]


class BoxIntegration(BaseIntegration):
    """
    Box integration implementation.
    Uses MCP tools for Box API operations.
    """
    
    def __init__(self, config: Optional[BoxConfig] = None):
        self.config = config or BoxConfig()
        super().__init__(self.config)
        self.capabilities = self.config._capabilities
        
        # Action to tool mapping
        self.action_mappings = {
            # File operations
            "list_files": "box_list_files",
            "get_file": "box_get_file",
            "download_file": "box_download_file",
            "upload_file": "box_upload_file",
            "create_folder": "box_create_folder",
            "delete_file": "box_delete_file",
            "delete_folder": "box_delete_folder",
            "copy_file": "box_copy_file",
            "move_file": "box_move_file",
            "rename_file": "box_rename_file",
            
            # Search
            "search": "box_search",
            
            # Sharing
            "create_shared_link": "box_create_shared_link",
            "get_shared_link": "box_get_shared_link",
            "remove_shared_link": "box_remove_shared_link",
            
            # Comments
            "list_comments": "box_list_comments",
            "create_comment": "box_create_comment",
            "delete_comment": "box_delete_comment",
            
            # Versions
            "list_file_versions": "box_list_file_versions",
            "get_file_version": "box_get_file_version",
            "promote_version": "box_promote_version",
            
            # Metadata
            "get_metadata": "box_get_metadata",
            "set_metadata": "box_set_metadata",
            
            # Trash
            "get_trash_items": "box_get_trash_items",
            "restore_from_trash": "box_restore_from_trash",
            "permanently_delete": "box_permanently_delete",
            
            # Users
            "get_user": "box_get_user",
            "get_current_user": "box_get_current_user",
            
            # Collaborations
            "list_collaborations": "box_list_collaborations",
            "create_collaboration": "box_create_collaboration",
            "delete_collaboration": "box_delete_collaboration",
            
            # Webhooks
            "list_webhooks": "box_list_webhooks",
            "create_webhook": "box_create_webhook",
            "delete_webhook": "box_delete_webhook",
        }
    
    async def initialize(self) -> bool:
        """Initialize Box integration"""
        try:
            # Check if box MCP connector is available
            self.status = IntegrationStatus.UNAUTHORISED
            return True
        except Exception as e:
            self.last_error = str(e)
            self.status = IntegrationStatus.ERROR
            return False
    
    async def check_status(self) -> IntegrationStatus:
        """Check current status"""
        return self.status
    
    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> IntegrationResult:
        """
        Execute a Box action.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            
        Returns:
            IntegrationResult with success status and data
        """
        if parameters is None:
            parameters = {}
        
        # Check if we're authenticated
        if self.status == IntegrationStatus.UNAUTHORISED:
            return IntegrationResult(
                success=False,
                error="Box integration requires authentication",
                status_code=401
            )
        
        # Check if action is supported
        if action not in self.action_mappings:
            return IntegrationResult(
                success=False,
                error=f"Action '{action}' is not supported by Box integration",
                status_code=400
            )
        
        # Check rate limit
        if not await self.check_rate_limit():
            return IntegrationResult(
                success=False,
                error="Rate limit exceeded",
                status_code=429
            )
        
        try:
            # Get tool name
            tool_name = self.action_mappings.get(action, action)
            
            # Execute via MCP
            result = await self._execute_tool(tool_name, parameters)
            
            return IntegrationResult(
                success=result.get("success", True),
                data=result.get("data"),
                error=result.get("error"),
                status_code=result.get("status_code", 200)
            )
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=str(e),
                status_code=500
            )
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool"""
        # This would be implemented with actual MCP tool execution
        # For now, return a mock response
        return {
            "success": True,
            "data": {"message": f"Executed {tool_name} with params: {parameters}"}
        }
    
    # Convenience methods for common operations
    
    async def list_files(
        self,
        folder_id: str = "0",
        fields: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> IntegrationResult:
        """List files in a folder"""
        params = {
            "folder_id": folder_id,
            "limit": limit,
            "offset": offset
        }
        if fields:
            params["fields"] = ",".join(fields)
        return await self.execute("list_files", params)
    
    async def get_file(self, file_id: str, fields: Optional[List[str]] = None) -> IntegrationResult:
        """Get file details"""
        params = {"file_id": file_id}
        if fields:
            params["fields"] = ",".join(fields)
        return await self.execute("get_file", params)
    
    async def upload_file(
        self,
        folder_id: str,
        file_name: str,
        file_content: bytes,
        content_type: Optional[str] = None
    ) -> IntegrationResult:
        """Upload a file"""
        params = {
            "folder_id": folder_id,
            "file_name": file_name,
            "file_content": file_content.hex(),  # Encode bytes as hex for JSON
            "content_type": content_type or "application/octet-stream"
        }
        return await self.execute("upload_file", params)
    
    async def create_folder(
        self,
        parent_folder_id: str = "0",
        name: str = "New Folder",
        description: Optional[str] = None
    ) -> IntegrationResult:
        """Create a new folder"""
        params = {
            "parent_folder_id": parent_folder_id,
            "name": name
        }
        if description:
            params["description"] = description
        return await self.execute("create_folder", params)
    
    async def search(
        self,
        query: str,
        type: str = "file",
        fields: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> IntegrationResult:
        """Search for files and folders"""
        params = {
            "query": query,
            "type": type,
            "limit": limit,
            "offset": offset
        }
        if fields:
            params["fields"] = ",".join(fields)
        return await self.execute("search", params)
    
    async def create_shared_link(
        self,
        file_id: str,
        access: str = "open",
        password: Optional[str] = None,
        unshared_at: Optional[str] = None
    ) -> IntegrationResult:
        """Create a shared link for a file"""
        params = {
            "file_id": file_id,
            "access": access
        }
        if password:
            params["password"] = password
        if unshared_at:
            params["unshared_at"] = unshared_at
        return await self.execute("create_shared_link", params)
    
    async def get_current_user(self, fields: Optional[List[str]] = None) -> IntegrationResult:
        """Get current user details"""
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        return await self.execute("get_current_user", params)


# Singleton instance
box_integration = BoxIntegration()
