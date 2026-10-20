"""
GitHub Integration for UAW
Интеграция с GitHub через доступные инструменты
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from .base import (
    BaseIntegration, IntegrationConfig, IntegrationResult,
    IntegrationStatus, IntegrationCapability, IntegrationError
)


class GitHubConfig(IntegrationConfig):
    """Configuration for GitHub integration"""
    
    def __init__(self):
        super().__init__(
            name="github",
            display_name="GitHub",
            description="GitHub integration for repositories, issues, pull requests, and more",
            integration_type="mcp",
            base_url="https://api.github.com",
            api_version="v3",
            timeout=30,
            max_retries=3,
            rate_limit=5000,  # GitHub API rate limit
            auth_method="oauth2",
            requires_auth=True,
            supports_read=True,
            supports_write=True,
            supports_webhooks=True,
            supports_search=True,
            max_page_size=100,
            icon_url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
            documentation_url="https://docs.github.com/en/rest"
        )
        self._capabilities = [
            IntegrationCapability(
                name="search_repositories",
                description="Search for repositories",
                operation="read",
                parameters=["query", "sort", "order", "page", "perPage"],
                returns="List of repositories"
            ),
            IntegrationCapability(
                name="get_repository",
                description="Get repository details",
                operation="read",
                parameters=["owner", "repo"],
                returns="Repository details"
            ),
            IntegrationCapability(
                name="list_repositories",
                description="List repositories for user or org",
                operation="read",
                parameters=["user", "org", "type", "sort", "direction"],
                returns="List of repositories"
            ),
            IntegrationCapability(
                name="create_repository",
                description="Create a new repository",
                operation="write",
                parameters=["name", "description", "private", "organization"],
                returns="Created repository"
            ),
            IntegrationCapability(
                name="delete_repository",
                description="Delete a repository",
                operation="delete",
                parameters=["owner", "repo"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="search_issues",
                description="Search for issues and pull requests",
                operation="read",
                parameters=["query", "sort", "order", "page", "perPage"],
                returns="List of issues/PRs"
            ),
            IntegrationCapability(
                name="get_issue",
                description="Get issue details",
                operation="read",
                parameters=["owner", "repo", "issue_number"],
                returns="Issue details"
            ),
            IntegrationCapability(
                name="create_issue",
                description="Create a new issue",
                operation="write",
                parameters=["owner", "repo", "title", "body", "labels", "assignees"],
                returns="Created issue"
            ),
            IntegrationCapability(
                name="update_issue",
                description="Update an issue",
                operation="write",
                parameters=["owner", "repo", "issue_number", "title", "body", "state", "labels"],
                returns="Updated issue"
            ),
            IntegrationCapability(
                name="delete_issue",
                description="Delete an issue",
                operation="delete",
                parameters=["owner", "repo", "issue_number"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="search_pull_requests",
                description="Search for pull requests",
                operation="read",
                parameters=["query", "sort", "order", "page", "perPage"],
                returns="List of pull requests"
            ),
            IntegrationCapability(
                name="get_pull_request",
                description="Get pull request details",
                operation="read",
                parameters=["owner", "repo", "pull_number"],
                returns="Pull request details"
            ),
            IntegrationCapability(
                name="create_pull_request",
                description="Create a new pull request",
                operation="write",
                parameters=["owner", "repo", "title", "head", "base", "body", "draft", "reviewers"],
                returns="Created pull request"
            ),
            IntegrationCapability(
                name="update_pull_request",
                description="Update a pull request",
                operation="write",
                parameters=["owner", "repo", "pull_number", "title", "body", "state", "draft"],
                returns="Updated pull request"
            ),
            IntegrationCapability(
                name="merge_pull_request",
                description="Merge a pull request",
                operation="write",
                parameters=["owner", "repo", "pull_number", "merge_method", "commit_title", "commit_message"],
                returns="Merge result"
            ),
            IntegrationCapability(
                name="list_branches",
                description="List repository branches",
                operation="read",
                parameters=["owner", "repo"],
                returns="List of branches"
            ),
            IntegrationCapability(
                name="create_branch",
                description="Create a new branch",
                operation="write",
                parameters=["owner", "repo", "branch", "from_branch"],
                returns="Created branch"
            ),
            IntegrationCapability(
                name="delete_branch",
                description="Delete a branch",
                operation="delete",
                parameters=["owner", "repo", "branch"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="get_file_contents",
                description="Get file contents",
                operation="read",
                parameters=["owner", "repo", "path", "ref"],
                returns="File contents"
            ),
            IntegrationCapability(
                name="create_or_update_file",
                description="Create or update a file",
                operation="write",
                parameters=["owner", "repo", "path", "content", "message", "branch", "sha"],
                returns="File operation result"
            ),
            IntegrationCapability(
                name="delete_file",
                description="Delete a file",
                operation="delete",
                parameters=["owner", "repo", "path", "message", "branch"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="search_code",
                description="Search code across repositories",
                operation="read",
                parameters=["query", "sort", "order", "page", "perPage"],
                returns="Search results"
            ),
            IntegrationCapability(
                name="list_commits",
                description="List commits",
                operation="read",
                parameters=["owner", "repo", "sha", "path", "since", "until", "author", "page", "perPage"],
                returns="List of commits"
            ),
            IntegrationCapability(
                name="get_commit",
                description="Get commit details",
                operation="read",
                parameters=["owner", "repo", "sha", "detail"],
                returns="Commit details"
            ),
            IntegrationCapability(
                name="get_me",
                description="Get authenticated user info",
                operation="read",
                parameters=[],
                returns="User info"
            ),
            IntegrationCapability(
                name="list_teams",
                description="List teams for authenticated user",
                operation="read",
                parameters=[],
                returns="List of teams"
            ),
            IntegrationCapability(
                name="get_team_members",
                description="Get team members",
                operation="read",
                parameters=["org", "team_slug"],
                returns="List of team members"
            ),
            IntegrationCapability(
                name="search_users",
                description="Search for users",
                operation="read",
                parameters=["query", "sort", "order", "page", "perPage"],
                returns="List of users"
            ),
            IntegrationCapability(
                name="add_issue_comment",
                description="Add comment to issue or PR",
                operation="write",
                parameters=["owner", "repo", "issue_number", "body", "comment_id", "reaction"],
                returns="Comment result"
            ),
            IntegrationCapability(
                name="create_pull_request_review",
                description="Create a pull request review",
                operation="write",
                parameters=["owner", "repo", "pull_number", "event", "body", "comments"],
                returns="Review result"
            ),
            IntegrationCapability(
                name="request_copilot_review",
                description="Request GitHub Copilot review",
                operation="write",
                parameters=["owner", "repo", "pull_number"],
                returns="Copilot review request"
            ),
            IntegrationCapability(
                name="run_secret_scanning",
                description="Run secret scanning",
                operation="read",
                parameters=["files", "content"],
                returns="Scan results"
            ),
            IntegrationCapability(
                name="get_latest_release",
                description="Get latest release",
                operation="read",
                parameters=["owner", "repo"],
                returns="Release info"
            ),
            IntegrationCapability(
                name="list_releases",
                description="List all releases",
                operation="read",
                parameters=["owner", "repo"],
                returns="List of releases"
            ),
            IntegrationCapability(
                name="create_release",
                description="Create a new release",
                operation="write",
                parameters=["owner", "repo", "tag_name", "name", "body", "draft", "prerelease"],
                returns="Created release"
            ),
            IntegrationCapability(
                name="fork_repository",
                description="Fork a repository",
                operation="write",
                parameters=["owner", "repo", "organization"],
                returns="Fork result"
            ),
        ]
        self.capabilities = self._capabilities


class GitHubIntegration(BaseIntegration):
    """
    GitHub integration using available MCP tools.
    Provides full access to GitHub API through the github_app connector.
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        if config is None:
            config = GitHubConfig()
        super().__init__(config)
        self.capabilities = config.capabilities if hasattr(config, 'capabilities') else []
    
    async def initialize(self) -> bool:
        """Initialize GitHub integration"""
        try:
            # Check if we can access GitHub API
            result = await self._execute_tool("get_me", {})
            if result.success:
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
            result = await self._execute_tool("get_me", {})
            if result.success:
                return IntegrationStatus.CONNECTED
        
        return self.status
    
    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> IntegrationResult:
        """Execute a GitHub action"""
        if parameters is None:
            parameters = {}
        
        # Map action to tool name
        tool_name = self._map_action_to_tool(action)
        
        if not tool_name:
            return IntegrationResult(
                success=False,
                error=f"Unknown GitHub action: {action}"
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
            "search_repositories": "search_repositories",
            "get_repository": "get_repository",  # Note: No direct tool, use search or list
            "list_repositories": "search_repositories",
            "create_repository": "create_repository",
            "delete_repository": "delete_repository",  # Note: No direct tool
            "search_issues": "search_issues",
            "get_issue": "issue_read",
            "create_issue": "issue_write",
            "update_issue": "issue_write",
            "delete_issue": "issue_write",  # Use with state=closed
            "search_pull_requests": "search_pull_requests",
            "get_pull_request": "pull_request_read",
            "create_pull_request": "create_pull_request",
            "update_pull_request": "update_pull_request",
            "merge_pull_request": "merge_pull_request",
            "list_branches": "list_branches",
            "create_branch": "create_branch",
            "delete_branch": "delete_branch",  # Note: No direct tool
            "get_file_contents": "get_file_contents",
            "create_or_update_file": "create_or_update_file",
            "delete_file": "delete_file",
            "search_code": "search_code",
            "list_commits": "list_commits",
            "get_commit": "get_commit",
            "get_me": "get_me",
            "list_teams": "get_teams",
            "get_team_members": "get_team_members",
            "search_users": "search_users",
            "add_issue_comment": "add_issue_comment",
            "create_pull_request_review": "pull_request_review_write",
            "request_copilot_review": "request_copilot_review",
            "run_secret_scanning": "run_secret_scanning",
            "get_latest_release": "get_latest_release",
            "list_releases": "list_releases",
            "create_release": "create_release",
            "fork_repository": "fork_repository",
            
            # Additional mappings
            "get_user": "get_me",
            "list_issues": "list_issues",
            "list_pull_requests": "list_pull_requests",
            "list_tags": "list_tags",
            "get_tag": "get_tag",
            "get_label": "get_label",
            "list_labels": "list_issue_fields",  # Note: Not exact
            "list_collaborators": "list_repository_collaborators",
            "update_pull_request_branch": "update_pull_request_branch",
            "push_files": "push_files",
            "sub_issue_write": "sub_issue_write",
            "update_issue_comment": "update_issue_comment",
            "add_reply_to_pull_request_comment": "add_reply_to_pull_request_comment",
            "add_comment_to_pending_review": "add_comment_to_pending_review",
        }
        
        return action_mappings.get(action, action)
    
    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> IntegrationResult:
        """Execute a GitHub MCP tool"""
        # Import the actual tool functions
        try:
            # Dynamic import of github_app tools
            import sys
            github_module = sys.modules.get('github_app')
            
            if not github_module:
                # Try to import
                try:
                    import github_app
                    github_module = github_app
                except ImportError:
                    raise IntegrationError(
                        "GitHub integration tools not available",
                        data={"tool": tool_name}
                    )
            
            # Get the tool function
            tool_func = getattr(github_module, tool_name, None)
            
            if not tool_func:
                raise IntegrationError(
                    f"GitHub tool not found: {tool_name}",
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
                f"GitHub tool execution failed: {str(e)}",
                data={"tool": tool_name, "parameters": parameters}
            )
    
    # Convenience methods for common operations
    
    async def search_repositories(
        self,
        query: str,
        sort: str = "best match",
        order: str = "desc",
        page: int = 1,
        per_page: int = 30
    ) -> IntegrationResult:
        """Search for repositories"""
        return await self.execute(
            "search_repositories",
            {
                "query": query,
                "sort": sort,
                "order": order,
                "page": page,
                "perPage": per_page
            }
        )
    
    async def get_user_info(self) -> IntegrationResult:
        """Get authenticated user info"""
        return await self.execute("get_me", {})
    
    async def list_repositories(self, user: Optional[str] = None) -> IntegrationResult:
        """List repositories for user"""
        params = {}
        if user:
            params["query"] = f"user:{user}"
        else:
            params["query"] = ""
        return await self.search_repositories(**params)
    
    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> IntegrationResult:
        """Create a new issue"""
        return await self.execute(
            "create_issue",
            {
                "owner": owner,
                "repo": repo,
                "title": title,
                "body": body or "",
                "labels": labels or [],
                "assignees": assignees or []
            }
        )
    
    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None,
        draft: bool = False,
        reviewers: Optional[List[str]] = None
    ) -> IntegrationResult:
        """Create a new pull request"""
        return await self.execute(
            "create_pull_request",
            {
                "owner": owner,
                "repo": repo,
                "title": title,
                "head": head,
                "base": base,
                "body": body or "",
                "draft": draft,
                "reviewers": reviewers or []
            }
        )
    
    async def create_branch(
        self,
        owner: str,
        repo: str,
        branch: str,
        from_branch: Optional[str] = None
    ) -> IntegrationResult:
        """Create a new branch"""
        params = {
            "owner": owner,
            "repo": repo,
            "branch": branch
        }
        if from_branch:
            params["from_branch"] = from_branch
        
        return await self.execute("create_branch", params)
    
    async def update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str,
        sha: Optional[str] = None
    ) -> IntegrationResult:
        """Create or update a file"""
        return await self.execute(
            "create_or_update_file",
            {
                "owner": owner,
                "repo": repo,
                "path": path,
                "content": content,
                "message": message,
                "branch": branch,
                "sha": sha
            }
        )
    
    async def get_file(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None
    ) -> IntegrationResult:
        """Get file contents"""
        params = {
            "owner": owner,
            "repo": repo,
            "path": path
        }
        if ref:
            params["ref"] = ref
        
        return await self.execute("get_file_contents", params)
    
    async def search_code(
        self,
        query: str,
        owner: Optional[str] = None,
        repo: Optional[str] = None
    ) -> IntegrationResult:
        """Search code"""
        params = {"query": query}
        if owner and repo:
            params["query"] = f"{query} repo:{owner}/{repo}"
        elif owner:
            params["query"] = f"{query} user:{owner}"
        
        return await self.execute("search_code", params)
