"""
Document Library Integration for UAW
Интеграция с Document Library через MCP
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from .base import (
    BaseIntegration, IntegrationConfig, IntegrationResult,
    IntegrationStatus, IntegrationCapability, IntegrationError
)


class DocumentLibraryConfig(IntegrationConfig):
    """Configuration for Document Library integration"""
    
    def __init__(self):
        super().__init__(
            name="document_library",
            display_name="Document Library",
            description="Document Library integration for document management and search",
            integration_type="mcp",
            base_url=None,
            api_version="v1",
            timeout=30,
            max_retries=3,
            rate_limit=None,  # No rate limit for internal operations
            auth_method="none",
            requires_auth=False,
            supports_read=True,
            supports_write=True,
            supports_webhooks=False,
            supports_search=True,
            max_page_size=1000,
            icon_url=None,
            documentation_url=None
        )
        self._capabilities = [
            # Document operations
            IntegrationCapability(
                name="list_documents",
                description="List all documents",
                operation="read",
                parameters=["query", "limit", "offset", "tags", "created_after", "created_before"],
                returns="List of documents"
            ),
            IntegrationCapability(
                name="get_document",
                description="Get document details",
                operation="read",
                parameters=["document_id", "include_content"],
                returns="Document details"
            ),
            IntegrationCapability(
                name="create_document",
                description="Create a new document",
                operation="write",
                parameters=["title", "content", "tags", "metadata"],
                returns="Created document"
            ),
            IntegrationCapability(
                name="update_document",
                description="Update a document",
                operation="write",
                parameters=["document_id", "title", "content", "tags", "metadata"],
                returns="Updated document"
            ),
            IntegrationCapability(
                name="delete_document",
                description="Delete a document",
                operation="delete",
                parameters=["document_id"],
                returns="Success status"
            ),
            # Search
            IntegrationCapability(
                name="search",
                description="Search for documents",
                operation="read",
                parameters=["query", "tags", "limit", "offset", "created_after", "created_before"],
                returns="Search results"
            ),
            # Content operations
            IntegrationCapability(
                name="extract_text",
                description="Extract text from a document",
                operation="read",
                parameters=["document_id", "page_range"],
                returns="Extracted text"
            ),
            IntegrationCapability(
                name="summarize",
                description="Summarize a document",
                operation="read",
                parameters=["document_id", "max_length", "include_key_points"],
                returns="Document summary"
            ),
            IntegrationCapability(
                name="analyze",
                description="Analyze document content",
                operation="read",
                parameters=["document_id", "analysis_type", "options"],
                returns="Analysis results"
            ),
            # Metadata
            IntegrationCapability(
                name="get_metadata",
                description="Get document metadata",
                operation="read",
                parameters=["document_id"],
                returns="Document metadata"
            ),
            IntegrationCapability(
                name="set_metadata",
                description="Set document metadata",
                operation="write",
                parameters=["document_id", "metadata"],
                returns="Updated metadata"
            ),
            # Versioning
            IntegrationCapability(
                name="list_versions",
                description="List document versions",
                operation="read",
                parameters=["document_id", "limit", "offset"],
                returns="List of versions"
            ),
            IntegrationCapability(
                name="get_version",
                description="Get a specific version",
                operation="read",
                parameters=["document_id", "version_id"],
                returns="Version details"
            ),
            IntegrationCapability(
                name="restore_version",
                description="Restore a document version",
                operation="write",
                parameters=["document_id", "version_id"],
                returns="Restored version"
            ),
            # Organization
            IntegrationCapability(
                name="list_collections",
                description="List document collections",
                operation="read",
                parameters=["limit", "offset"],
                returns="List of collections"
            ),
            IntegrationCapability(
                name="create_collection",
                description="Create a new collection",
                operation="write",
                parameters=["name", "description"],
                returns="Created collection"
            ),
            IntegrationCapability(
                name="delete_collection",
                description="Delete a collection",
                operation="delete",
                parameters=["collection_id"],
                returns="Success status"
            ),
            # Tags
            IntegrationCapability(
                name="list_tags",
                description="List all tags",
                operation="read",
                parameters=["limit", "offset", "query"],
                returns="List of tags"
            ),
            IntegrationCapability(
                name="create_tag",
                description="Create a new tag",
                operation="write",
                parameters=["name", "color"],
                returns="Created tag"
            ),
            IntegrationCapability(
                name="delete_tag",
                description="Delete a tag",
                operation="delete",
                parameters=["tag_id"],
                returns="Success status"
            ),
            # Import/Export
            IntegrationCapability(
                name="import_document",
                description="Import a document",
                operation="write",
                parameters=["file_path", "title", "tags"],
                returns="Imported document"
            ),
            IntegrationCapability(
                name="export_document",
                description="Export a document",
                operation="read",
                parameters=["document_id", "format", "include_metadata"],
                returns="Exported document"
            ),
            # Statistics
            IntegrationCapability(
                name="get_statistics",
                description="Get document library statistics",
                operation="read",
                parameters=["time_range"],
                returns="Library statistics"
            ),
        ]


class DocumentLibraryIntegration(BaseIntegration):
    """
    Document Library integration implementation.
    Uses MCP tools for document management operations.
    """
    
    def __init__(self, config: Optional[DocumentLibraryConfig] = None):
        self.config = config or DocumentLibraryConfig()
        super().__init__(self.config)
        self.capabilities = self.config._capabilities
        self.status = IntegrationStatus.CONNECTED  # Always connected for internal
        
        # Action to tool mapping
        self.action_mappings = {
            # Document operations
            "list_documents": "document_library_list_documents",
            "get_document": "document_library_get_document",
            "create_document": "document_library_create_document",
            "update_document": "document_library_update_document",
            "delete_document": "document_library_delete_document",
            
            # Search
            "search": "document_library_search",
            
            # Content operations
            "extract_text": "document_library_extract_text",
            "summarize": "document_library_summarize",
            "analyze": "document_library_analyze",
            
            # Metadata
            "get_metadata": "document_library_get_metadata",
            "set_metadata": "document_library_set_metadata",
            
            # Versioning
            "list_versions": "document_library_list_versions",
            "get_version": "document_library_get_version",
            "restore_version": "document_library_restore_version",
            
            # Organization
            "list_collections": "document_library_list_collections",
            "create_collection": "document_library_create_collection",
            "delete_collection": "document_library_delete_collection",
            
            # Tags
            "list_tags": "document_library_list_tags",
            "create_tag": "document_library_create_tag",
            "delete_tag": "document_library_delete_tag",
            
            # Import/Export
            "import_document": "document_library_import_document",
            "export_document": "document_library_export_document",
            
            # Statistics
            "get_statistics": "document_library_get_statistics",
        }
    
    async def initialize(self) -> bool:
        """Initialize Document Library integration"""
        self.status = IntegrationStatus.CONNECTED
        return True
    
    async def check_status(self) -> IntegrationStatus:
        """Check current status"""
        return self.status
    
    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> IntegrationResult:
        """
        Execute a Document Library action.
        
        Args:
            action: Action to execute
            parameters: Action parameters
            
        Returns:
            IntegrationResult with success status and data
        """
        if parameters is None:
            parameters = {}
        
        # Check if action is supported
        if action not in self.action_mappings:
            return IntegrationResult(
                success=False,
                error=f"Action '{action}' is not supported by Document Library integration",
                status_code=400
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
    
    async def list_documents(
        self,
        query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        tags: Optional[List[str]] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None
    ) -> IntegrationResult:
        """List all documents"""
        params = {"limit": limit, "offset": offset}
        if query:
            params["query"] = query
        if tags:
            params["tags"] = tags
        if created_after:
            params["created_after"] = created_after
        if created_before:
            params["created_before"] = created_before
        return await self.execute("list_documents", params)
    
    async def get_document(self, document_id: str, include_content: bool = True) -> IntegrationResult:
        """Get document details"""
        return await self.execute("get_document", {
            "document_id": document_id,
            "include_content": include_content
        })
    
    async def create_document(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IntegrationResult:
        """Create a new document"""
        params = {
            "title": title,
            "content": content
        }
        if tags:
            params["tags"] = tags
        if metadata:
            params["metadata"] = metadata
        return await self.execute("create_document", params)
    
    async def update_document(
        self,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IntegrationResult:
        """Update a document"""
        params = {"document_id": document_id}
        if title:
            params["title"] = title
        if content:
            params["content"] = content
        if tags:
            params["tags"] = tags
        if metadata:
            params["metadata"] = metadata
        return await self.execute("update_document", params)
    
    async def delete_document(self, document_id: str) -> IntegrationResult:
        """Delete a document"""
        return await self.execute("delete_document", {"document_id": document_id})
    
    async def search(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None
    ) -> IntegrationResult:
        """Search for documents"""
        params = {
            "query": query,
            "limit": limit,
            "offset": offset
        }
        if tags:
            params["tags"] = tags
        if created_after:
            params["created_after"] = created_after
        if created_before:
            params["created_before"] = created_before
        return await self.execute("search", params)
    
    async def extract_text(self, document_id: str, page_range: Optional[str] = None) -> IntegrationResult:
        """Extract text from a document"""
        params = {"document_id": document_id}
        if page_range:
            params["page_range"] = page_range
        return await self.execute("extract_text", params)
    
    async def summarize(
        self,
        document_id: str,
        max_length: int = 1000,
        include_key_points: bool = True
    ) -> IntegrationResult:
        """Summarize a document"""
        return await self.execute("summarize", {
            "document_id": document_id,
            "max_length": max_length,
            "include_key_points": include_key_points
        })
    
    async def analyze(
        self,
        document_id: str,
        analysis_type: str = "full",
        options: Optional[Dict[str, Any]] = None
    ) -> IntegrationResult:
        """Analyze document content"""
        params = {
            "document_id": document_id,
            "analysis_type": analysis_type
        }
        if options:
            params["options"] = options
        return await self.execute("analyze", params)
    
    async def get_metadata(self, document_id: str) -> IntegrationResult:
        """Get document metadata"""
        return await self.execute("get_metadata", {"document_id": document_id})
    
    async def set_metadata(self, document_id: str, metadata: Dict[str, Any]) -> IntegrationResult:
        """Set document metadata"""
        return await self.execute("set_metadata", {
            "document_id": document_id,
            "metadata": metadata
        })


# Singleton instance
document_library_integration = DocumentLibraryIntegration()
