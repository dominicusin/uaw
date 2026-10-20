"""
Asana Integration for UAW
Интеграция с Asana через доступные инструменты
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from .base import (
    BaseIntegration, IntegrationConfig, IntegrationResult,
    IntegrationStatus, IntegrationCapability, IntegrationError
)


class AsanaConfig(IntegrationConfig):
    """Configuration for Asana integration"""
    
    def __init__(self):
        super().__init__(
            name="asana",
            display_name="Asana",
            description="Asana integration for tasks, projects, teams, and goals",
            integration_type="mcp",
            base_url="https://app.asana.com/api/1.0",
            api_version="1.0",
            timeout=30,
            max_retries=3,
            rate_limit=100,  # Asana API rate limit: 100 requests/minute
            auth_method="oauth2",
            requires_auth=True,
            supports_read=True,
            supports_write=True,
            supports_webhooks=True,
            supports_search=True,
            max_page_size=100,
            icon_url="https://assets.asana.com/production/marketing/asana-logo-340x130.png",
            documentation_url="https://developers.asana.com/docs"
        )
        self._capabilities = [
            IntegrationCapability(
                name="list_workspaces",
                description="List all accessible workspaces",
                operation="read",
                parameters=["limit", "offset", "opt_fields"],
                returns="List of workspaces"
            ),
            IntegrationCapability(
                name="get_workspace",
                description="Get workspace details",
                operation="read",
                parameters=["workspace_gid", "opt_fields"],
                returns="Workspace details"
            ),
            IntegrationCapability(
                name="typeahead_search",
                description="Quick search across Asana objects",
                operation="read",
                parameters=["workspace_gid", "resource_type", "query", "count", "opt_fields"],
                returns="Search results"
            ),
            IntegrationCapability(
                name="get_user",
                description="Get user details",
                operation="read",
                parameters=["user_id", "opt_fields"],
                returns="User details"
            ),
            IntegrationCapability(
                name="get_workspace_users",
                description="Get all users in workspace",
                operation="read",
                parameters=["workspace", "opt_fields", "offset"],
                returns="List of users"
            ),
            IntegrationCapability(
                name="get_team_users",
                description="List all team members",
                operation="read",
                parameters=["team_id", "opt_fields", "offset"],
                returns="List of team members"
            ),
            IntegrationCapability(
                name="get_teams_for_workspace",
                description="List all teams in workspace",
                operation="read",
                parameters=["workspace_gid", "limit", "offset", "opt_fields"],
                returns="List of teams"
            ),
            IntegrationCapability(
                name="get_teams_for_user",
                description="Get teams user belongs to",
                operation="read",
                parameters=["user_gid", "organization", "limit", "offset", "opt_fields"],
                returns="List of teams"
            ),
            IntegrationCapability(
                name="get_projects",
                description="List projects filtered by workspace",
                operation="read",
                parameters=["workspace", "team", "archived", "opt_fields", "limit", "offset"],
                returns="List of projects"
            ),
            IntegrationCapability(
                name="get_projects_for_team",
                description="List all projects for a team",
                operation="read",
                parameters=["team_id", "opt_fields", "limit", "offset"],
                returns="List of projects"
            ),
            IntegrationCapability(
                name="get_projects_for_workspace",
                description="Get ALL projects in a workspace",
                operation="read",
                parameters=["workspace_gid", "opt_fields", "limit", "offset"],
                returns="List of projects"
            ),
            IntegrationCapability(
                name="get_project",
                description="Get detailed project data",
                operation="read",
                parameters=["project_gid", "opt_fields"],
                returns="Project details"
            ),
            IntegrationCapability(
                name="create_project",
                description="Create a new project",
                operation="write",
                parameters=["name", "workspace", "team", "notes", "is_public", "archived", "followers"],
                returns="Created project"
            ),
            IntegrationCapability(
                name="update_project",
                description="Update project properties",
                operation="write",
                parameters=["project_gid", "name", "notes", "archived", "followers", "opt_fields"],
                returns="Updated project"
            ),
            IntegrationCapability(
                name="delete_project",
                description="Delete a project",
                operation="delete",
                parameters=["project_gid"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="get_tasks",
                description="List tasks filtered by context",
                operation="read",
                parameters=["workspace", "project", "tag", "section", "user_task_list", "assignee", "completed_since", "modified_since", "opt_fields", "limit", "offset"],
                returns="List of tasks"
            ),
            IntegrationCapability(
                name="search_tasks",
                description="Advanced task search",
                operation="read",
                parameters=["workspace", "project", "portfolio", "team", "assignee", "tag", "text", "start_on", "due_on", "completed_on", "created_on", "modified_on", "is_subtask", "parent", "status", "limit", "offset", "opt_fields"],
                returns="Search results"
            ),
            IntegrationCapability(
                name="get_task",
                description="Get full task details",
                operation="read",
                parameters=["task_id", "opt_fields"],
                returns="Task details"
            ),
            IntegrationCapability(
                name="create_task",
                description="Create a new task",
                operation="write",
                parameters=["name", "workspace", "project", "parent", "assignee", "notes", "html_notes", "due_on", "start_on", "followers", "tags", "custom_fields", "opt_fields"],
                returns="Created task"
            ),
            IntegrationCapability(
                name="update_task",
                description="Update existing task properties",
                operation="write",
                parameters=["task_id", "name", "notes", "html_notes", "assignee", "completed", "due_on", "start_on", "followers", "tags", "custom_fields", "opt_fields"],
                returns="Updated task"
            ),
            IntegrationCapability(
                name="delete_task",
                description="Delete a task",
                operation="delete",
                parameters=["task_id"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="set_parent_for_task",
                description="Change task parent (convert to/from subtask)",
                operation="write",
                parameters=["task_id", "parent", "insert_before", "insert_after", "opt_fields"],
                returns="Updated task hierarchy"
            ),
            IntegrationCapability(
                name="set_task_dependencies",
                description="Set tasks this task depends on",
                operation="write",
                parameters=["task_id", "dependencies"],
                returns="Updated dependencies"
            ),
            IntegrationCapability(
                name="set_task_dependents",
                description="Set tasks blocked by this task",
                operation="write",
                parameters=["task_id", "dependents"],
                returns="Updated dependents"
            ),
            IntegrationCapability(
                name="add_task_followers",
                description="Add followers to task",
                operation="write",
                parameters=["task_id", "followers", "opt_fields"],
                returns="Updated followers"
            ),
            IntegrationCapability(
                name="remove_task_followers",
                description="Remove followers from task",
                operation="write",
                parameters=["task_id", "followers", "opt_fields"],
                returns="Updated followers"
            ),
            IntegrationCapability(
                name="create_task_story",
                description="Add comment to task",
                operation="write",
                parameters=["task_id", "text", "html_text", "is_pinned", "opt_fields"],
                returns="Created story"
            ),
            IntegrationCapability(
                name="get_stories_for_task",
                description="Get task activity history",
                operation="read",
                parameters=["task_id", "opt_fields", "limit", "offset"],
                returns="List of stories"
            ),
            IntegrationCapability(
                name="get_attachments_for_object",
                description="List all attachments for an object",
                operation="read",
                parameters=["parent", "opt_fields", "limit", "offset"],
                returns="List of attachments"
            ),
            IntegrationCapability(
                name="get_attachment",
                description="Get detailed attachment data",
                operation="read",
                parameters=["attachment_gid", "opt_fields"],
                returns="Attachment details"
            ),
            IntegrationCapability(
                name="get_goals",
                description="List goals filtered by context",
                operation="read",
                parameters=["workspace", "team", "portfolio", "project", "task", "time_periods", "is_workspace_level", "limit", "offset", "opt_fields"],
                returns="List of goals"
            ),
            IntegrationCapability(
                name="get_goal",
                description="Get detailed goal data",
                operation="read",
                parameters=["goal_gid", "opt_fields"],
                returns="Goal details"
            ),
            IntegrationCapability(
                name="create_goal",
                description="Create a new goal",
                operation="write",
                parameters=["name", "workspace", "team", "owner", "due_on", "start_on", "html_notes", "notes", "is_workspace_level", "liked", "followers", "time_period", "opt_fields"],
                returns="Created goal"
            ),
            IntegrationCapability(
                name="update_goal",
                description="Update goal properties",
                operation="write",
                parameters=["goal_gid", "name", "owner", "due_on", "start_on", "html_notes", "notes", "is_workspace_level", "liked", "team", "workspace", "time_period", "status", "opt_fields"],
                returns="Updated goal"
            ),
            IntegrationCapability(
                name="get_parent_goals_for_goal",
                description="List all parent goals for a specific goal",
                operation="read",
                parameters=["goal_gid", "opt_fields"],
                returns="List of parent goals"
            ),
            IntegrationCapability(
                name="get_time_periods",
                description="List available time periods in a workspace",
                operation="read",
                parameters=["workspace", "start_on", "end_on", "opt_fields", "limit", "offset"],
                returns="List of time periods"
            ),
            IntegrationCapability(
                name="get_time_period",
                description="Get detailed information about a time period",
                operation="read",
                parameters=["time_period_gid", "opt_fields"],
                returns="Time period details"
            ),
            IntegrationCapability(
                name="get_portfolios",
                description="List portfolios in workspace",
                operation="read",
                parameters=["workspace", "opt_fields", "limit", "offset"],
                returns="List of portfolios"
            ),
            IntegrationCapability(
                name="get_portfolio",
                description="Get detailed portfolio data",
                operation="read",
                parameters=["portfolio_gid", "opt_fields"],
                returns="Portfolio details"
            ),
            IntegrationCapability(
                name="get_items_for_portfolio",
                description="List projects, goals, and other items in a portfolio",
                operation="read",
                parameters=["portfolio_gid", "opt_fields", "limit", "offset"],
                returns="List of items"
            ),
            IntegrationCapability(
                name="get_project_sections",
                description="List all sections in a project",
                operation="read",
                parameters=["project_gid", "opt_fields", "limit", "offset"],
                returns="List of sections"
            ),
            IntegrationCapability(
                name="get_project_task_counts",
                description="Get task statistics for a project",
                operation="read",
                parameters=["project_gid", "opt_fields"],
                returns="Task counts"
            ),
            IntegrationCapability(
                name="create_project_status",
                description="Create project status update",
                operation="write",
                parameters=["project_gid", "color", "text", "html_text", "opt_fields"],
                returns="Created status"
            ),
            IntegrationCapability(
                name="get_project_statuses",
                description="List all status updates for a project",
                operation="read",
                parameters=["project_gid", "opt_fields", "limit", "offset"],
                returns="List of statuses"
            ),
            IntegrationCapability(
                name="get_project_status",
                description="Get single status update by ID",
                operation="read",
                parameters=["status_gid", "opt_fields"],
                returns="Status details"
            ),
            IntegrationCapability(
                name="get_allocations",
                description="List allocations filtered by context",
                operation="read",
                parameters=["workspace", "assignee", "parent", "limit", "offset", "opt_fields"],
                returns="List of allocations"
            ),
            IntegrationCapability(
                name="get_workspace_agents",
                description="List agents in workspace",
                operation="read",
                parameters=["workspace", "limit", "offset", "opt_fields"],
                returns="List of agents"
            ),
            IntegrationCapability(
                name="get_agent",
                description="Get agent details",
                operation="read",
                parameters=["agent_gid", "opt_fields"],
                returns="Agent details"
            ),
        ]
        self.capabilities = self._capabilities


class AsanaIntegration(BaseIntegration):
    """
    Asana integration using available MCP tools.
    Provides full access to Asana API through the asana connector.
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        if config is None:
            config = AsanaConfig()
        super().__init__(config)
        self.capabilities = config.capabilities if hasattr(config, 'capabilities') else []
        self._workspace_id: Optional[str] = None
    
    async def initialize(self) -> bool:
        """Initialize Asana integration"""
        try:
            # Check if we can access Asana API
            result = await self._execute_tool("list_workspaces", {})
            if result.success and result.data:
                # Store first workspace ID
                workspaces = result.data if isinstance(result.data, list) else []
                if workspaces:
                    self._workspace_id = workspaces[0].get("gid")
                self.status = IntegrationStatus.CONNECTED
                return True
            else:
                self.status = IntegrationStatus.UNAUTHORISED
                return False
        except Exception as e:
            self.status = IntegrationStatus.ERROR
            self.last_error = str(e)
            return False
    
    async def check_status(self) -> IntegrationStatus:
        """Check current status"""
        if self.status == IntegrationStatus.CONNECTED:
            # Verify connection
            result = await self._execute_tool("list_workspaces", {})
            if result.success:
                return IntegrationStatus.CONNECTED
        
        return self.status
    
    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> IntegrationResult:
        """Execute an Asana action"""
        if parameters is None:
            parameters = {}
        
        # Add workspace if needed
        if self._workspace_id and "workspace" not in parameters:
            # Only add workspace for actions that need it
            workspace_actions = [
                "get_projects", "get_projects_for_workspace", 
                "get_teams_for_workspace", "get_workspace_users",
                "get_time_periods", "get_goals", "get_portfolios"
            ]
            if any(action.startswith(a) for a in workspace_actions):
                parameters["workspace"] = self._workspace_id
        
        # Map action to tool name
        tool_name = self._map_action_to_tool(action)
        
        if not tool_name:
            return IntegrationResult(
                success=False,
                error=f"Unknown Asana action: {action}"
            )
        
        # Execute the tool
        try:
            result = await self._execute_tool(tool_name, parameters)
            return result
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=str(e)
            )
    
    def _map_action_to_tool(self, action: str) -> str:
        """Map action name to tool name"""
        # Direct mappings
        action_mappings = {
            "list_workspaces": "asana_list_workspaces",
            "get_workspace": "asana_get_workspace",
            "typeahead_search": "asana_typeahead_search",
            "get_user": "asana_get_user",
            "get_workspace_users": "asana_get_workspace_users",
            "get_team_users": "asana_get_team_users",
            "get_teams_for_workspace": "asana_get_teams_for_workspace",
            "get_teams_for_user": "asana_get_teams_for_user",
            "get_projects": "asana_get_projects",
            "get_projects_for_team": "asana_get_projects_for_team",
            "get_projects_for_workspace": "asana_get_projects_for_workspace",
            "get_project": "asana_get_project",
            "create_project": "asana_create_project",
            "update_project": "asana_update_project",
            "delete_project": "asana_delete_project",
            "get_tasks": "asana_get_tasks",
            "search_tasks": "asana_search_tasks",
            "get_task": "asana_get_task",
            "create_task": "asana_create_task",
            "update_task": "asana_update_task",
            "delete_task": "asana_delete_task",
            "set_parent_for_task": "asana_set_parent_for_task",
            "set_task_dependencies": "asana_set_task_dependencies",
            "set_task_dependents": "asana_set_task_dependents",
            "add_task_followers": "asana_add_task_followers",
            "remove_task_followers": "asana_remove_task_followers",
            "create_task_story": "asana_create_task_story",
            "get_stories_for_task": "asana_get_stories_for_task",
            "get_attachments_for_object": "asana_get_attachments_for_object",
            "get_attachment": "asana_get_attachment",
            "get_goals": "asana_get_goals",
            "get_goal": "asana_get_goal",
            "create_goal": "asana_create_goal",
            "update_goal": "asana_update_goal",
            "get_parent_goals_for_goal": "asana_get_parent_goals_for_goal",
            "get_time_periods": "asana_get_time_periods",
            "get_time_period": "asana_get_time_period",
            "get_portfolios": "asana_get_portfolios",
            "get_portfolio": "asana_get_portfolio",
            "get_items_for_portfolio": "asana_get_items_for_portfolio",
            "get_project_sections": "asana_get_project_sections",
            "get_project_task_counts": "asana_get_project_task_counts",
            "create_project_status": "asana_create_project_status",
            "get_project_statuses": "asana_get_project_statuses",
            "get_project_status": "asana_get_project_status",
            "get_allocations": "asana_get_allocations",
            "get_workspace_agents": "asana_get_workspace_agents",
            "get_agent": "asana_get_agent",
        }
        
        return action_mappings.get(action, action)
    
    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> IntegrationResult:
        """Execute an Asana MCP tool"""
        # Import the actual tool functions
        try:
            # Dynamic import of asana tools
            import sys
            asana_module = sys.modules.get('asana_asana')
            
            if not asana_module:
                # Try to import
                try:
                    import asana_asana as asana_module
                except ImportError:
                    raise IntegrationError(
                        "Asana integration tools not available",
                        data={"tool": tool_name}
                    )
            
            # Get the tool function
            tool_func = getattr(asana_module, tool_name, None)
            
            if not tool_func:
                raise IntegrationError(
                    f"Asana tool not found: {tool_name}",
                    data={"tool": tool_name}
                )
            
            # Execute the tool
            result = await tool_func(**parameters)
            
            # Process result
            if isinstance(result, dict):
                return IntegrationResult(
                    success=True,
                    data=result
                )
            else:
                return IntegrationResult(
                    success=True,
                    data={"result": result}
                )
                
        except IntegrationError:
            raise
        except Exception as e:
            raise IntegrationError(
                f"Asana tool execution failed: {str(e)}",
                data={"tool": tool_name, "parameters": parameters}
            )
    
    # Convenience methods for common operations
    
    async def list_workspaces(self) -> IntegrationResult:
        """List all accessible workspaces"""
        return await self.execute("list_workspaces", {})
    
    async def get_user(self, user_id: str = "me") -> IntegrationResult:
        """Get user details"""
        return await self.execute("get_user", {"user_id": user_id})
    
    async def search_tasks(
        self,
        query: str,
        workspace: Optional[str] = None
    ) -> IntegrationResult:
        """Search for tasks"""
        params = {"query": query}
        if workspace:
            params["workspace_gid"] = workspace
        else:
            params["workspace_gid"] = self._workspace_id
        return await self.execute("search_tasks", params)
    
    async def create_task(
        self,
        name: str,
        project: Optional[str] = None,
        assignee: Optional[str] = None,
        notes: Optional[str] = None,
        due_on: Optional[str] = None,
        workspace: Optional[str] = None
    ) -> IntegrationResult:
        """Create a new task"""
        params = {
            "name": name,
            "notes": notes or "",
        }
        if project:
            params["project"] = project
        if assignee:
            params["assignee"] = assignee
        if due_on:
            params["due_on"] = due_on
        if workspace:
            params["workspace"] = workspace
        elif self._workspace_id:
            params["workspace"] = self._workspace_id
        
        return await self.execute("create_task", params)
    
    async def update_task(
        self,
        task_id: str,
        name: Optional[str] = None,
        notes: Optional[str] = None,
        assignee: Optional[str] = None,
        completed: Optional[bool] = None
    ) -> IntegrationResult:
        """Update a task"""
        params = {"task_id": task_id}
        if name:
            params["name"] = name
        if notes:
            params["notes"] = notes
        if assignee:
            params["assignee"] = assignee
        if completed is not None:
            params["completed"] = completed
        
        return await self.execute("update_task", params)
    
    async def get_projects(self, workspace: Optional[str] = None) -> IntegrationResult:
        """Get all projects"""
        params = {}
        if workspace:
            params["workspace"] = workspace
        elif self._workspace_id:
            params["workspace"] = self._workspace_id
        
        return await self.execute("get_projects", params)
    
    async def create_project(
        self,
        name: str,
        workspace: Optional[str] = None,
        team: Optional[str] = None
    ) -> IntegrationResult:
        """Create a new project"""
        params = {"name": name}
        if workspace:
            params["workspace"] = workspace
        elif self._workspace_id:
            params["workspace"] = self._workspace_id
        if team:
            params["team"] = team
        
        return await self.execute("create_project", params)
