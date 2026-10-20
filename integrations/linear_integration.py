"""
Linear Integration for UAW
Интеграция с Linear через MCP
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from .base import (
    BaseIntegration, IntegrationConfig, IntegrationResult,
    IntegrationStatus, IntegrationCapability, IntegrationError
)


class LinearConfig(IntegrationConfig):
    """Configuration for Linear integration"""
    
    def __init__(self):
        super().__init__(
            name="linear",
            display_name="Linear",
            description="Linear integration for issues, projects, teams, and more",
            integration_type="mcp",
            base_url="https://api.linear.app/graphql",
            api_version="v1",
            timeout=30,
            max_retries=3,
            rate_limit=100,  # Linear API rate limit per minute
            auth_method="api_key",
            requires_auth=True,
            supports_read=True,
            supports_write=True,
            supports_webhooks=True,
            supports_search=True,
            max_page_size=100,
            icon_url="https://linear.app/favicon.ico",
            documentation_url="https://developers.linear.app/docs"
        )
        self._capabilities = [
            # Issue operations
            IntegrationCapability(
                name="list_issues",
                description="List issues",
                operation="read",
                parameters=["team", "project", "assignee", "state", "labels", "limit", "cursor"],
                returns="List of issues"
            ),
            IntegrationCapability(
                name="get_issue",
                description="Get issue details",
                operation="read",
                parameters=["id", "include"],
                returns="Issue details"
            ),
            IntegrationCapability(
                name="create_issue",
                description="Create a new issue",
                operation="write",
                parameters=["title", "description", "team", "project", "assignee", "labels", "priority", "state"],
                returns="Created issue"
            ),
            IntegrationCapability(
                name="update_issue",
                description="Update an issue",
                operation="write",
                parameters=["id", "title", "description", "team", "project", "assignee", "labels", "priority", "state"],
                returns="Updated issue"
            ),
            IntegrationCapability(
                name="delete_issue",
                description="Delete an issue",
                operation="delete",
                parameters=["id"],
                returns="Success status"
            ),
            # Comment operations
            IntegrationCapability(
                name="list_comments",
                description="List comments on an issue",
                operation="read",
                parameters=["issue_id", "limit", "cursor"],
                returns="List of comments"
            ),
            IntegrationCapability(
                name="create_comment",
                description="Create a comment on an issue",
                operation="write",
                parameters=["issue_id", "body", "parent_id"],
                returns="Created comment"
            ),
            IntegrationCapability(
                name="update_comment",
                description="Update a comment",
                operation="write",
                parameters=["id", "body"],
                returns="Updated comment"
            ),
            IntegrationCapability(
                name="delete_comment",
                description="Delete a comment",
                operation="delete",
                parameters=["id"],
                returns="Success status"
            ),
            # Team operations
            IntegrationCapability(
                name="list_teams",
                description="List teams",
                operation="read",
                parameters=["limit", "cursor", "query"],
                returns="List of teams"
            ),
            IntegrationCapability(
                name="get_team",
                description="Get team details",
                operation="read",
                parameters=["id", "include"],
                returns="Team details"
            ),
            IntegrationCapability(
                name="create_team",
                description="Create a new team",
                operation="write",
                parameters=["name", "description", "key"],
                returns="Created team"
            ),
            IntegrationCapability(
                name="update_team",
                description="Update a team",
                operation="write",
                parameters=["id", "name", "description", "key"],
                returns="Updated team"
            ),
            IntegrationCapability(
                name="delete_team",
                description="Delete a team",
                operation="delete",
                parameters=["id"],
                returns="Success status"
            ),
            # Project operations
            IntegrationCapability(
                name="list_projects",
                description="List projects",
                operation="read",
                parameters=["team", "state", "query", "limit", "cursor"],
                returns="List of projects"
            ),
            IntegrationCapability(
                name="get_project",
                description="Get project details",
                operation="read",
                parameters=["id", "include"],
                returns="Project details"
            ),
            IntegrationCapability(
                name="create_project",
                description="Create a new project",
                operation="write",
                parameters=["name", "description", "team", "state", "start_date", "target_date", "color"],
                returns="Created project"
            ),
            IntegrationCapability(
                name="update_project",
                description="Update a project",
                operation="write",
                parameters=["id", "name", "description", "team", "state", "start_date", "target_date", "color"],
                returns="Updated project"
            ),
            IntegrationCapability(
                name="delete_project",
                description="Delete a project",
                operation="delete",
                parameters=["id"],
                returns="Success status"
            ),
            # User operations
            IntegrationCapability(
                name="list_users",
                description="List users",
                operation="read",
                parameters=["query", "limit", "cursor"],
                returns="List of users"
            ),
            IntegrationCapability(
                name="get_user",
                description="Get user details",
                operation="read",
                parameters=["id", "include"],
                returns="User details"
            ),
            IntegrationCapability(
                name="get_me",
                description="Get current user details",
                operation="read",
                parameters=[],
                returns="Current user details"
            ),
            # Label operations
            IntegrationCapability(
                name="list_labels",
                description="List labels",
                operation="read",
                parameters=["team", "query", "limit", "cursor"],
                returns="List of labels"
            ),
            IntegrationCapability(
                name="get_label",
                description="Get label details",
                operation="read",
                parameters=["id"],
                returns="Label details"
            ),
            IntegrationCapability(
                name="create_label",
                description="Create a new label",
                operation="write",
                parameters=["name", "description", "color", "team"],
                returns="Created label"
            ),
            IntegrationCapability(
                name="update_label",
                description="Update a label",
                operation="write",
                parameters=["id", "name", "description", "color"],
                returns="Updated label"
            ),
            IntegrationCapability(
                name="delete_label",
                description="Delete a label",
                operation="delete",
                parameters=["id"],
                returns="Success status"
            ),
            # State operations
            IntegrationCapability(
                name="list_states",
                description="List states for a team",
                operation="read",
                parameters=["team_id", "type"],
                returns="List of states"
            ),
            IntegrationCapability(
                name="get_state",
                description="Get state details",
                operation="read",
                parameters=["id"],
                returns="State details"
            ),
            # Search
            IntegrationCapability(
                name="search",
                description="Search for issues, projects, users, etc.",
                operation="read",
                parameters=["query", "type", "limit", "cursor"],
                returns="Search results"
            ),
            # Webhooks
            IntegrationCapability(
                name="list_webhooks",
                description="List webhooks",
                operation="read",
                parameters=["limit", "cursor"],
                returns="List of webhooks"
            ),
            IntegrationCapability(
                name="create_webhook",
                description="Create a webhook",
                operation="write",
                parameters=["url", "resource_types", "event_types", "team_ids"],
                returns="Created webhook"
            ),
            IntegrationCapability(
                name="delete_webhook",
                description="Delete a webhook",
                operation="delete",
                parameters=["id"],
                returns="Success status"
            ),
            # Attachments
            IntegrationCapability(
                name="list_attachments",
                description="List attachments for an issue",
                operation="read",
                parameters=["issue_id"],
                returns="List of attachments"
            ),
            IntegrationCapability(
                name="create_attachment",
                description="Create an attachment",
                operation="write",
                parameters=["issue_id", "url", "title"],
                returns="Created attachment"
            ),
            # Issue status operations
            IntegrationCapability(
                name="list_issue_statuses",
                description="List issue statuses for a team",
                operation="read",
                parameters=["team_id"],
                returns="List of issue statuses"
            ),
            # Priority operations
            IntegrationCapability(
                name="list_priorities",
                description="List priorities for a team",
                operation="read",
                parameters=["team_id"],
                returns="List of priorities"
            ),
            # Custom views
            IntegrationCapability(
                name="get_roadmap",
                description="Get roadmap data",
                operation="read",
                parameters=["team_id", "project_id", "date_range"],
                returns="Roadmap data"
            ),
            IntegrationCapability(
                name="get_cycles",
                description="Get cycles for a team",
                operation="read",
                parameters=["team_id"],
                returns="List of cycles"
            ),
        ]


class LinearIntegration(BaseIntegration):
    """
    Linear integration implementation.
    Uses MCP tools for Linear API operations.
    """
    
    def __init__(self, config: Optional[LinearConfig] = None):
        self.config = config or LinearConfig()
        super().__init__(self.config)
        self.capabilities = self.config._capabilities
        
        # Action to tool mapping
        self.action_mappings = {
            # Issue operations
            "list_issues": "linear_list_issues",
            "get_issue": "linear_get_issue",
            "create_issue": "linear_create_issue",
            "update_issue": "linear_update_issue",
            "delete_issue": "linear_delete_issue",
            
            # Comment operations
            "list_comments": "linear_list_comments",
            "create_comment": "linear_create_comment",
            "update_comment": "linear_update_comment",
            "delete_comment": "linear_delete_comment",
            
            # Team operations
            "list_teams": "linear_list_teams",
            "get_team": "linear_get_team",
            "create_team": "linear_create_team",
            "update_team": "linear_update_team",
            "delete_team": "linear_delete_team",
            
            # Project operations
            "list_projects": "linear_list_projects",
            "get_project": "linear_get_project",
            "create_project": "linear_create_project",
            "update_project": "linear_update_project",
            "delete_project": "linear_delete_project",
            
            # User operations
            "list_users": "linear_list_users",
            "get_user": "linear_get_user",
            "get_me": "linear_get_me",
            
            # Label operations
            "list_labels": "linear_list_labels",
            "get_label": "linear_get_label",
            "create_label": "linear_create_label",
            "update_label": "linear_update_label",
            "delete_label": "linear_delete_label",
            
            # State operations
            "list_states": "linear_list_states",
            "get_state": "linear_get_state",
            
            # Search
            "search": "linear_search",
            
            # Webhooks
            "list_webhooks": "linear_list_webhooks",
            "create_webhook": "linear_create_webhook",
            "delete_webhook": "linear_delete_webhook",
            
            # Attachments
            "list_attachments": "linear_list_attachments",
            "create_attachment": "linear_create_attachment",
            
            # Issue status operations
            "list_issue_statuses": "linear_list_issue_statuses",
            
            # Priority operations
            "list_priorities": "linear_list_priorities",
            
            # Custom views
            "get_roadmap": "linear_get_roadmap",
            "get_cycles": "linear_get_cycles",
        }
    
    async def initialize(self) -> bool:
        """Initialize Linear integration"""
        try:
            # Check if linear MCP connector is available
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
        Execute a Linear action.
        
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
                error="Linear integration requires authentication",
                status_code=401
            )
        
        # Check if action is supported
        if action not in self.action_mappings:
            return IntegrationResult(
                success=False,
                error=f"Action '{action}' is not supported by Linear integration",
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
    
    async def list_issues(
        self,
        team: Optional[str] = None,
        project: Optional[str] = None,
        assignee: Optional[str] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
        limit: int = 50,
        cursor: Optional[str] = None
    ) -> IntegrationResult:
        """List issues"""
        params = {"limit": limit}
        if team:
            params["team"] = team
        if project:
            params["project"] = project
        if assignee:
            params["assignee"] = assignee
        if state:
            params["state"] = state
        if labels:
            params["labels"] = labels
        if cursor:
            params["cursor"] = cursor
        return await self.execute("list_issues", params)
    
    async def get_issue(self, issue_id: str, include: Optional[List[str]] = None) -> IntegrationResult:
        """Get issue details"""
        params = {"id": issue_id}
        if include:
            params["include"] = include
        return await self.execute("get_issue", params)
    
    async def create_issue(
        self,
        title: str,
        description: Optional[str] = None,
        team: Optional[str] = None,
        project: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        priority: Optional[int] = None,
        state: Optional[str] = None
    ) -> IntegrationResult:
        """Create a new issue"""
        params = {"title": title}
        if description:
            params["description"] = description
        if team:
            params["team"] = team
        if project:
            params["project"] = project
        if assignee:
            params["assignee"] = assignee
        if labels:
            params["labels"] = labels
        if priority:
            params["priority"] = priority
        if state:
            params["state"] = state
        return await self.execute("create_issue", params)
    
    async def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        team: Optional[str] = None,
        project: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        priority: Optional[int] = None,
        state: Optional[str] = None
    ) -> IntegrationResult:
        """Update an issue"""
        params = {"id": issue_id}
        if title:
            params["title"] = title
        if description:
            params["description"] = description
        if team:
            params["team"] = team
        if project:
            params["project"] = project
        if assignee:
            params["assignee"] = assignee
        if labels:
            params["labels"] = labels
        if priority:
            params["priority"] = priority
        if state:
            params["state"] = state
        return await self.execute("update_issue", params)
    
    async def search(
        self,
        query: str,
        type: str = "issue",
        limit: int = 50,
        cursor: Optional[str] = None
    ) -> IntegrationResult:
        """Search for issues, projects, users, etc."""
        params = {
            "query": query,
            "type": type,
            "limit": limit
        }
        if cursor:
            params["cursor"] = cursor
        return await self.execute("search", params)
    
    async def get_me(self) -> IntegrationResult:
        """Get current user details"""
        return await self.execute("get_me", {})
    
    async def get_team(self, team_id: str, include: Optional[List[str]] = None) -> IntegrationResult:
        """Get team details"""
        params = {"id": team_id}
        if include:
            params["include"] = include
        return await self.execute("get_team", params)
    
    async def get_project(self, project_id: str, include: Optional[List[str]] = None) -> IntegrationResult:
        """Get project details"""
        params = {"id": project_id}
        if include:
            params["include"] = include
        return await self.execute("get_project", params)


# Singleton instance
linear_integration = LinearIntegration()
