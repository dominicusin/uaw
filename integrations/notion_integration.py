"""
Notion Integration for UAW
Интеграция с Notion через MCP
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from .base import (
    BaseIntegration, IntegrationConfig, IntegrationResult,
    IntegrationStatus, IntegrationCapability, IntegrationError
)


class NotionConfig(IntegrationConfig):
    """Configuration for Notion integration"""
    
    def __init__(self):
        super().__init__(
            name="notion",
            display_name="Notion",
            description="Notion integration for pages, databases, blocks, and more",
            integration_type="mcp",
            base_url="https://api.notion.com/v1",
            api_version="v1",
            timeout=30,
            max_retries=3,
            rate_limit=60,  # Notion API rate limit per minute
            auth_method="bearer_token",
            requires_auth=True,
            supports_read=True,
            supports_write=True,
            supports_webhooks=False,
            supports_search=True,
            max_page_size=100,
            icon_url="https://www.notion.so/images/meta/notion-og.png",
            documentation_url="https://developers.notion.com/reference/intro"
        )
        self._capabilities = [
            # Page operations
            IntegrationCapability(
                name="list_pages",
                description="List pages in a database or workspace",
                operation="read",
                parameters=["database_id", "page_size", "cursor", "filter", "sorts"],
                returns="List of pages"
            ),
            IntegrationCapability(
                name="get_page",
                description="Get page details",
                operation="read",
                parameters=["page_id"],
                returns="Page details"
            ),
            IntegrationCapability(
                name="create_page",
                description="Create a new page",
                operation="write",
                parameters=["parent_page_id", "parent_database_id", "properties", "children"],
                returns="Created page"
            ),
            IntegrationCapability(
                name="update_page",
                description="Update a page",
                operation="write",
                parameters=["page_id", "properties", "archived"],
                returns="Updated page"
            ),
            IntegrationCapability(
                name="delete_page",
                description="Delete a page",
                operation="delete",
                parameters=["page_id"],
                returns="Success status"
            ),
            # Database operations
            IntegrationCapability(
                name="list_databases",
                description="List databases",
                operation="read",
                parameters=["page_size", "cursor", "filter", "sorts"],
                returns="List of databases"
            ),
            IntegrationCapability(
                name="get_database",
                description="Get database details",
                operation="read",
                parameters=["database_id"],
                returns="Database details"
            ),
            IntegrationCapability(
                name="create_database",
                description="Create a new database",
                operation="write",
                parameters=["parent_page_id", "title", "properties", "icon", "cover"],
                returns="Created database"
            ),
            IntegrationCapability(
                name="update_database",
                description="Update a database",
                operation="write",
                parameters=["database_id", "properties", "title", "description", "icon", "cover"],
                returns="Updated database"
            ),
            IntegrationCapability(
                name="query_database",
                description="Query a database",
                operation="read",
                parameters=["database_id", "filter", "sorts", "page_size", "cursor"],
                returns="Query results"
            ),
            # Block operations
            IntegrationCapability(
                name="get_blocks",
                description="Get block children",
                operation="read",
                parameters=["block_id", "page_size", "cursor"],
                returns="List of blocks"
            ),
            IntegrationCapability(
                name="append_blocks",
                description="Append blocks to a page",
                operation="write",
                parameters=["page_id", "children", "after"],
                returns="Appended blocks"
            ),
            IntegrationCapability(
                name="update_block",
                description="Update a block",
                operation="write",
                parameters=["block_id", "block"],
                returns="Updated block"
            ),
            IntegrationCapability(
                name="delete_block",
                description="Delete a block",
                operation="delete",
                parameters=["block_id"],
                returns="Success status"
            ),
            # Search
            IntegrationCapability(
                name="search",
                description="Search for pages and databases",
                operation="read",
                parameters=["query", "filter", "sort", "page_size", "cursor"],
                returns="Search results"
            ),
            # Comments
            IntegrationCapability(
                name="list_comments",
                description="List comments on a page",
                operation="read",
                parameters=["block_id", "page_size", "cursor"],
                returns="List of comments"
            ),
            IntegrationCapability(
                name="create_comment",
                description="Create a comment on a page",
                operation="write",
                parameters=["page_id", "discussion_id", "rich_text"],
                returns="Created comment"
            ),
            # Users
            IntegrationCapability(
                name="list_users",
                description="List users",
                operation="read",
                parameters=["page_size", "cursor"],
                returns="List of users"
            ),
            IntegrationCapability(
                name="get_user",
                description="Get user details",
                operation="read",
                parameters=["user_id"],
                returns="User details"
            ),
            IntegrationCapability(
                name="get_me",
                description="Get current user details",
                operation="read",
                parameters=[],
                returns="Current user details"
            ),
            # Rich text and content
            IntegrationCapability(
                name="create_paragraph",
                description="Create a paragraph block",
                operation="write",
                parameters=["text", "color", "background_color"],
                returns="Paragraph block"
            ),
            IntegrationCapability(
                name="create_heading",
                description="Create a heading block",
                operation="write",
                parameters=["text", "level", "color", "background_color"],
                returns="Heading block"
            ),
            IntegrationCapability(
                name="create_text",
                description="Create a text block",
                operation="write",
                parameters=["text", "link"],
                returns="Text block"
            ),
            IntegrationCapability(
                name="create_bulleted_list",
                description="Create a bulleted list block",
                operation="write",
                parameters=["children", "color", "background_color"],
                returns="Bulleted list block"
            ),
            IntegrationCapability(
                name="create_numbered_list",
                description="Create a numbered list block",
                operation="write",
                parameters=["children", "color", "background_color"],
                returns="Numbered list block"
            ),
            IntegrationCapability(
                name="create_to_do",
                description="Create a to-do list block",
                operation="write",
                parameters=["children", "color", "background_color"],
                returns="To-do list block"
            ),
            IntegrationCapability(
                name="create_toggle",
                description="Create a toggle block",
                operation="write",
                parameters=["text", "children", "color", "background_color"],
                returns="Toggle block"
            ),
            IntegrationCapability(
                name="create_code",
                description="Create a code block",
                operation="write",
                parameters=["text", "language"],
                returns="Code block"
            ),
            IntegrationCapability(
                name="create_quote",
                description="Create a quote block",
                operation="write",
                parameters=["text", "color", "background_color"],
                returns="Quote block"
            ),
            IntegrationCapability(
                name="create_callout",
                description="Create a callout block",
                operation="write",
                parameters=["text", "icon", "color", "background_color"],
                returns="Callout block"
            ),
            # Media
            IntegrationCapability(
                name="create_image",
                description="Create an image block",
                operation="write",
                parameters=["url", "caption"],
                returns="Image block"
            ),
            IntegrationCapability(
                name="create_video",
                description="Create a video block",
                operation="write",
                parameters=["url", "caption"],
                returns="Video block"
            ),
            IntegrationCapability(
                name="create_audio",
                description="Create an audio block",
                operation="write",
                parameters=["url", "caption"],
                returns="Audio block"
            ),
            IntegrationCapability(
                name="create_file",
                description="Create a file block",
                operation="write",
                parameters=["url", "caption"],
                returns="File block"
            ),
            IntegrationCapability(
                name="create_pdf",
                description="Create a PDF block",
                operation="write",
                parameters=["url", "caption"],
                returns="PDF block"
            ),
            # Embeds
            IntegrationCapability(
                name="create_embed",
                description="Create an embed block",
                operation="write",
                parameters=["url"],
                returns="Embed block"
            ),
            IntegrationCapability(
                name="create_bookmark",
                description="Create a bookmark block",
                operation="write",
                parameters=["url", "caption"],
                returns="Bookmark block"
            ),
            IntegrationCapability(
                name="create_link_preview",
                description="Create a link preview block",
                operation="write",
                parameters=["url"],
                returns="Link preview block"
            ),
            # Advanced
            IntegrationCapability(
                name="create_table",
                description="Create a table block",
                operation="write",
                parameters=["table_width", "has_column_header", "has_row_header", "children"],
                returns="Table block"
            ),
            IntegrationCapability(
                name="create_board",
                description="Create a board block",
                operation="write",
                parameters=["columns", "children"],
                returns="Board block"
            ),
            IntegrationCapability(
                name="create_column",
                description="Create a column block",
                operation="write",
                parameters=["children"],
                returns="Column block"
            ),
            IntegrationCapability(
                name="create_divider",
                description="Create a divider block",
                operation="write",
                parameters=[],
                returns="Divider block"
            ),
            IntegrationCapability(
                name="create_equation",
                description="Create an equation block",
                operation="write",
                parameters=["expression"],
                returns="Equation block"
            ),
        ]


class NotionIntegration(BaseIntegration):
    """
    Notion integration implementation.
    Uses MCP tools for Notion API operations.
    """
    
    def __init__(self, config: Optional[NotionConfig] = None):
        self.config = config or NotionConfig()
        super().__init__(self.config)
        self.capabilities = self.config._capabilities
        
        # Action to tool mapping
        self.action_mappings = {
            # Page operations
            "list_pages": "notion_list_pages",
            "get_page": "notion_get_page",
            "create_page": "notion_create_page",
            "update_page": "notion_update_page",
            "delete_page": "notion_delete_page",
            
            # Database operations
            "list_databases": "notion_list_databases",
            "get_database": "notion_get_database",
            "create_database": "notion_create_database",
            "update_database": "notion_update_database",
            "query_database": "notion_query_database",
            
            # Block operations
            "get_blocks": "notion_get_blocks",
            "append_blocks": "notion_append_blocks",
            "update_block": "notion_update_block",
            "delete_block": "notion_delete_block",
            
            # Search
            "search": "notion_search",
            
            # Comments
            "list_comments": "notion_list_comments",
            "create_comment": "notion_create_comment",
            
            # Users
            "list_users": "notion_list_users",
            "get_user": "notion_get_user",
            "get_me": "notion_get_me",
            
            # Rich text blocks
            "create_paragraph": "notion_create_paragraph",
            "create_heading": "notion_create_heading",
            "create_text": "notion_create_text",
            "create_bulleted_list": "notion_create_bulleted_list",
            "create_numbered_list": "notion_create_numbered_list",
            "create_to_do": "notion_create_to_do",
            "create_toggle": "notion_create_toggle",
            "create_code": "notion_create_code",
            "create_quote": "notion_create_quote",
            "create_callout": "notion_create_callout",
            
            # Media blocks
            "create_image": "notion_create_image",
            "create_video": "notion_create_video",
            "create_audio": "notion_create_audio",
            "create_file": "notion_create_file",
            "create_pdf": "notion_create_pdf",
            
            # Embed blocks
            "create_embed": "notion_create_embed",
            "create_bookmark": "notion_create_bookmark",
            "create_link_preview": "notion_create_link_preview",
            
            # Advanced blocks
            "create_table": "notion_create_table",
            "create_board": "notion_create_board",
            "create_column": "notion_create_column",
            "create_divider": "notion_create_divider",
            "create_equation": "notion_create_equation",
        }
    
    async def initialize(self) -> bool:
        """Initialize Notion integration"""
        try:
            # Check if notion MCP connector is available
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
        Execute a Notion action.
        
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
                error="Notion integration requires authentication",
                status_code=401
            )
        
        # Check if action is supported
        if action not in self.action_mappings:
            return IntegrationResult(
                success=False,
                error=f"Action '{action}' is not supported by Notion integration",
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
    
    async def get_page(self, page_id: str) -> IntegrationResult:
        """Get page details"""
        return await self.execute("get_page", {"page_id": page_id})
    
    async def create_page(
        self,
        parent_page_id: Optional[str] = None,
        parent_database_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        children: Optional[List[Dict[str, Any]]] = None
    ) -> IntegrationResult:
        """Create a new page"""
        params = {}
        if parent_page_id:
            params["parent_page_id"] = parent_page_id
        if parent_database_id:
            params["parent_database_id"] = parent_database_id
        if properties:
            params["properties"] = properties
        if children:
            params["children"] = children
        return await self.execute("create_page", params)
    
    async def update_page(
        self,
        page_id: str,
        properties: Optional[Dict[str, Any]] = None,
        archived: Optional[bool] = None
    ) -> IntegrationResult:
        """Update a page"""
        params = {"page_id": page_id}
        if properties:
            params["properties"] = properties
        if archived is not None:
            params["archived"] = archived
        return await self.execute("update_page", params)
    
    async def query_database(
        self,
        database_id: str,
        filter: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 100,
        cursor: Optional[str] = None
    ) -> IntegrationResult:
        """Query a database"""
        params = {
            "database_id": database_id,
            "page_size": page_size
        }
        if filter:
            params["filter"] = filter
        if sorts:
            params["sorts"] = sorts
        if cursor:
            params["cursor"] = cursor
        return await self.execute("query_database", params)
    
    async def search(
        self,
        query: str,
        filter: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, Any]] = None,
        page_size: int = 100,
        cursor: Optional[str] = None
    ) -> IntegrationResult:
        """Search for pages and databases"""
        params = {
            "query": query,
            "page_size": page_size
        }
        if filter:
            params["filter"] = filter
        if sort:
            params["sort"] = sort
        if cursor:
            params["cursor"] = cursor
        return await self.execute("search", params)
    
    async def get_me(self) -> IntegrationResult:
        """Get current user details"""
        return await self.execute("get_me", {})
    
    # Helper methods for creating rich content
    
    async def create_rich_page(
        self,
        title: str,
        content: List[Dict[str, Any]],
        parent_page_id: Optional[str] = None,
        parent_database_id: Optional[str] = None,
        icon: Optional[str] = None,
        cover: Optional[str] = None
    ) -> IntegrationResult:
        """Create a page with rich content"""
        properties = {
            "title": {
                "title": [{"text": {"content": title}}]
            }
        }
        
        if icon:
            properties["icon"] = {"icon": {"type": "emoji", "emoji": icon}}
        if cover:
            properties["cover"] = {"cover": {"type": "external", "external": {"url": cover}}}
        
        params = {
            "properties": properties,
            "children": content
        }
        
        if parent_page_id:
            params["parent_page_id"] = parent_page_id
        if parent_database_id:
            params["parent_database_id"] = parent_database_id
        
        return await self.execute("create_page", params)
    
    async def append_content(
        self,
        page_id: str,
        content: List[Dict[str, Any]],
        after: Optional[str] = None
    ) -> IntegrationResult:
        """Append content to a page"""
        params = {
            "page_id": page_id,
            "children": content
        }
        if after:
            params["after"] = after
        return await self.execute("append_blocks", params)


# Singleton instance
notion_integration = NotionIntegration()
