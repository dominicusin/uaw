"""
Vercel Adapter for UAW
Адаптер для Vercel через REST API
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import aiohttp
import json
import base64

from .base import (
    BaseAdapter, AdapterConfig, AdapterResult,
    AdapterStatus, AdapterCapability, AdapterError, AuthMethod
)


class VercelConfig(AdapterConfig):
    """Configuration for Vercel adapter"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        team_id: Optional[str] = None
    ):
        super().__init__(
            name="vercel",
            display_name="Vercel",
            description="Vercel adapter for deployments, projects, and management",
            base_url="https://api.vercel.com",
            api_version="v1",
            timeout=60,  # Deployments can take time
            max_retries=3,
            rate_limit=120,  # Vercel API rate limit: 120 requests/minute
            auth_method=AuthMethod.BEARER_TOKEN,
            access_token=api_key,
            icon_url="https://assets.vercel.com/image/upload/v1588805858/vercel/favicon.ico",
            documentation_url="https://vercel.com/docs/api"
        )
        self.team_id = team_id
        self._capabilities = [
            AdapterCapability(
                name="list_projects",
                description="List all projects",
                method="GET",
                endpoint="/v1/projects",
                parameters=["teamId", "limit", "since"],
                returns="List of projects"
            ),
            AdapterCapability(
                name="get_project",
                description="Get project details",
                method="GET",
                endpoint="/v1/projects/{project_id}",
                parameters=["project_id"],
                returns="Project details"
            ),
            AdapterCapability(
                name="create_project",
                description="Create a new project",
                method="POST",
                endpoint="/v1/projects",
                parameters=["name", "teamId", "repository", "gitRepository", "rootDirectory"],
                returns="Created project"
            ),
            AdapterCapability(
                name="update_project",
                description="Update project properties",
                method="PATCH",
                endpoint="/v1/projects/{project_id}",
                parameters=["project_id", "name", "teamId", "repository", "gitRepository", "rootDirectory", "serverlessFunctionRegion"],
                returns="Updated project"
            ),
            AdapterCapability(
                name="delete_project",
                description="Delete a project",
                method="DELETE",
                endpoint="/v1/projects/{project_id}",
                parameters=["project_id"],
                returns="Success status"
            ),
            AdapterCapability(
                name="list_deployments",
                description="List all deployments for a project",
                method="GET",
                endpoint="/v1/projects/{project_id}/deployments",
                parameters=["project_id", "limit", "since", "state"],
                returns="List of deployments"
            ),
            AdapterCapability(
                name="get_deployment",
                description="Get deployment details",
                method="GET",
                endpoint="/v1/deployments/{deployment_id}",
                parameters=["deployment_id"],
                returns="Deployment details"
            ),
            AdapterCapability(
                name="create_deployment",
                description="Create a new deployment",
                method="POST",
                endpoint="/v1/deployments",
                parameters=["projectId", "ref", "target", "regions", "withCache"],
                returns="Created deployment"
            ),
            AdapterCapability(
                name="cancel_deployment",
                description="Cancel a deployment",
                method="POST",
                endpoint="/v1/deployments/{deployment_id}/cancel",
                parameters=["deployment_id"],
                returns="Cancellation result"
            ),
            AdapterCapability(
                name="retry_deployment",
                description="Retry a failed deployment",
                method="POST",
                endpoint="/v1/deployments/{deployment_id}/retry",
                parameters=["deployment_id"],
                returns="Retry result"
            ),
            AdapterCapability(
                name="list_builds",
                description="List all builds for a project",
                method="GET",
                endpoint="/v1/projects/{project_id}/builds",
                parameters=["project_id", "limit", "since", "state"],
                returns="List of builds"
            ),
            AdapterCapability(
                name="get_build",
                description="Get build details",
                method="GET",
                endpoint="/v1/builds/{build_id}",
                parameters=["build_id"],
                returns="Build details"
            ),
            AdapterCapability(
                name="cancel_build",
                description="Cancel a build",
                method="POST",
                endpoint="/v1/builds/{build_id}/cancel",
                parameters=["build_id"],
                returns="Cancellation result"
            ),
            AdapterCapability(
                name="list_environments",
                description="List environments for a project",
                method="GET",
                endpoint="/v1/projects/{project_id}/envs",
                parameters=["project_id", "teamId"],
                returns="List of environments"
            ),
            AdapterCapability(
                name="get_environment",
                description="Get environment details",
                method="GET",
                endpoint="/v1/projects/{project_id}/envs/{env_id}",
                parameters=["project_id", "env_id"],
                returns="Environment details"
            ),
            AdapterCapability(
                name="create_environment",
                description="Create a new environment variable",
                method="POST",
                endpoint="/v1/projects/{project_id}/envs",
                parameters=["project_id", "key", "value", "target", "type"],
                returns="Created environment variable"
            ),
            AdapterCapability(
                name="update_environment",
                description="Update an environment variable",
                method="PATCH",
                endpoint="/v1/projects/{project_id}/envs/{env_id}",
                parameters=["project_id", "env_id", "key", "value", "target", "type"],
                returns="Updated environment variable"
            ),
            AdapterCapability(
                name="delete_environment",
                description="Delete an environment variable",
                method="DELETE",
                endpoint="/v1/projects/{project_id}/envs/{env_id}",
                parameters=["project_id", "env_id"],
                returns="Success status"
            ),
            AdapterCapability(
                name="list_domains",
                description="List domains for a project",
                method="GET",
                endpoint="/v1/projects/{project_id}/domains",
                parameters=["project_id", "teamId"],
                returns="List of domains"
            ),
            AdapterCapability(
                name="get_domain",
                description="Get domain details",
                method="GET",
                endpoint="/v1/domains/{domain_id}",
                parameters=["domain_id"],
                returns="Domain details"
            ),
            AdapterCapability(
                name="create_domain",
                description="Create a new domain",
                method="POST",
                endpoint="/v1/domains",
                parameters=["name", "teamId", "projectId"],
                returns="Created domain"
            ),
            AdapterCapability(
                name="delete_domain",
                description="Delete a domain",
                method="DELETE",
                endpoint="/v1/domains/{domain_id}",
                parameters=["domain_id"],
                returns="Success status"
            ),
            AdapterCapability(
                name="list_teams",
                description="List all teams",
                method="GET",
                endpoint="/v1/teams",
                parameters=["limit"],
                returns="List of teams"
            ),
            AdapterCapability(
                name="get_team",
                description="Get team details",
                method="GET",
                endpoint="/v1/teams/{team_id}",
                parameters=["team_id"],
                returns="Team details"
            ),
            AdapterCapability(
                name="list_team_members",
                description="List members of a team",
                method="GET",
                endpoint="/v1/teams/{team_id}/members",
                parameters=["team_id"],
                returns="List of members"
            ),
            AdapterCapability(
                name="list_logs",
                description="List logs for a project",
                method="GET",
                endpoint="/v1/projects/{project_id}/logs",
                parameters=["project_id", "limit", "since", "outputFormat"],
                returns="List of logs"
            ),
            AdapterCapability(
                name="get_log",
                description="Get log details",
                method="GET",
                endpoint="/v1/logs/{log_id}",
                parameters=["log_id"],
                returns="Log details"
            ),
        ]
        self.capabilities = self._capabilities


class VercelAdapter(BaseAdapter):
    """
    Vercel adapter using REST API.
    Provides access to Vercel deployments and projects.
    """
    
    def __init__(self, config: Optional[VercelConfig] = None):
        if config is None:
            config = VercelConfig()
        super().__init__(config)
        self.capabilities = config.capabilities if hasattr(config, 'capabilities') else []
        self._default_project_id: Optional[str] = None
        self.team_id = config.team_id
    
    async def initialize(self) -> bool:
        """Initialize the adapter"""
        # Check if we have API key
        if not self.config.access_token:
            self.status = AdapterStatus.UNAVAILABLE
            self.last_error = "No API key provided"
            return False
        
        # Try to list projects to verify connection
        result = await self.list_projects()
        if result.success and result.data:
            projects = result.data
            if isinstance(projects, dict) and projects.get("projects"):
                self._default_project_id = projects["projects"][0].get("id")
                self.status = AdapterStatus.CONFIGURED
                return True
        
        self.status = AdapterStatus.UNAVAILABLE
        self.last_error = "Failed to verify API key"
        return False
    
    async def check_status(self) -> AdapterStatus:
        """Check current status"""
        if self.status == AdapterStatus.CONFIGURED:
            # Try to make a test request
            result = await self.list_projects()
            if result.success:
                return AdapterStatus.AVAILABLE
        
        return self.status
    
    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """Execute an action"""
        if parameters is None:
            parameters = {}
        
        # Map action to method
        action_mappings = {
            "list_projects": self.list_projects,
            "get_project": self.get_project,
            "create_project": self.create_project,
            "update_project": self.update_project,
            "delete_project": self.delete_project,
            "list_deployments": self.list_deployments,
            "get_deployment": self.get_deployment,
            "create_deployment": self.create_deployment,
            "cancel_deployment": self.cancel_deployment,
            "retry_deployment": self.retry_deployment,
            "list_builds": self.list_builds,
            "get_build": self.get_build,
            "cancel_build": self.cancel_build,
            "list_environments": self.list_environments,
            "get_environment": self.get_environment,
            "create_environment": self.create_environment,
            "update_environment": self.update_environment,
            "delete_environment": self.delete_environment,
            "list_domains": self.list_domains,
            "get_domain": self.get_domain,
            "create_domain": self.create_domain,
            "delete_domain": self.delete_domain,
            "list_teams": self.list_teams,
            "get_team": self.get_team,
            "list_team_members": self.list_team_members,
            "list_logs": self.list_logs,
            "get_log": self.get_log,
        }
        
        method = action_mappings.get(action)
        if not method:
            return AdapterResult(
                success=False,
                error=f"Unknown action: {action}"
            )
        
        try:
            return await method(**parameters)
        except Exception as e:
            return AdapterResult(
                success=False,
                error=str(e)
            )
    
    # Project operations
    
    async def list_projects(
        self,
        team_id: Optional[str] = None,
        limit: int = 100
    ) -> AdapterResult:
        """List all projects"""
        params = {"limit": limit}
        if team_id:
            params["teamId"] = team_id
        elif self.team_id:
            params["teamId"] = self.team_id
        
        return await self._make_request(
            method="GET",
            endpoint="/v1/projects",
            params=params
        )
    
    async def get_project(self, project_id: str) -> AdapterResult:
        """Get project details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/v1/projects/{project_id}"
        )
    
    async def create_project(
        self,
        name: str,
        team_id: Optional[str] = None,
        repository: Optional[str] = None,
        git_repository: Optional[Dict[str, str]] = None,
        root_directory: Optional[str] = None
    ) -> AdapterResult:
        """Create a new project"""
        data = {"name": name}
        if team_id:
            data["teamId"] = team_id
        elif self.team_id:
            data["teamId"] = self.team_id
        if repository:
            data["repository"] = repository
        if git_repository:
            data["gitRepository"] = git_repository
        if root_directory:
            data["rootDirectory"] = root_directory
        
        return await self._make_request(
            method="POST",
            endpoint="/v1/projects",
            json_data=data
        )
    
    async def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        team_id: Optional[str] = None,
        repository: Optional[str] = None,
        git_repository: Optional[Dict[str, str]] = None,
        root_directory: Optional[str] = None,
        serverless_function_region: Optional[str] = None
    ) -> AdapterResult:
        """Update project properties"""
        data = {}
        if name:
            data["name"] = name
        if team_id:
            data["teamId"] = team_id
        if repository:
            data["repository"] = repository
        if git_repository:
            data["gitRepository"] = git_repository
        if root_directory:
            data["rootDirectory"] = root_directory
        if serverless_function_region:
            data["serverlessFunctionRegion"] = serverless_function_region
        
        if not data:
            return AdapterResult(
                success=False,
                error="No fields to update"
            )
        
        return await self._make_request(
            method="PATCH",
            endpoint=f"/v1/projects/{project_id}",
            json_data=data
        )
    
    async def delete_project(self, project_id: str) -> AdapterResult:
        """Delete a project"""
        return await self._make_request(
            method="DELETE",
            endpoint=f"/v1/projects/{project_id}"
        )
    
    # Deployment operations
    
    async def list_deployments(
        self,
        project_id: Optional[str] = None,
        limit: int = 100,
        state: Optional[str] = None
    ) -> AdapterResult:
        """List all deployments for a project"""
        params = {"limit": limit}
        if project_id:
            params["projectId"] = project_id
        elif self._default_project_id:
            params["projectId"] = self._default_project_id
        if state:
            params["state"] = state
        
        return await self._make_request(
            method="GET",
            endpoint="/v1/deployments",
            params=params
        )
    
    async def get_deployment(self, deployment_id: str) -> AdapterResult:
        """Get deployment details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/v1/deployments/{deployment_id}"
        )
    
    async def create_deployment(
        self,
        project_id: Optional[str] = None,
        ref: str = "main",
        target: str = "production",
        regions: Optional[List[str]] = None
    ) -> AdapterResult:
        """Create a new deployment"""
        data = {
            "ref": ref,
            "target": target
        }
        if project_id:
            data["projectId"] = project_id
        elif self._default_project_id:
            data["projectId"] = self._default_project_id
        if regions:
            data["regions"] = regions
        
        return await self._make_request(
            method="POST",
            endpoint="/v1/deployments",
            json_data=data
        )
    
    async def cancel_deployment(self, deployment_id: str) -> AdapterResult:
        """Cancel a deployment"""
        return await self._make_request(
            method="POST",
            endpoint=f"/v1/deployments/{deployment_id}/cancel"
        )
    
    async def retry_deployment(self, deployment_id: str) -> AdapterResult:
        """Retry a failed deployment"""
        return await self._make_request(
            method="POST",
            endpoint=f"/v1/deployments/{deployment_id}/retry"
        )
    
    # Build operations
    
    async def list_builds(
        self,
        project_id: Optional[str] = None,
        limit: int = 100,
        state: Optional[str] = None
    ) -> AdapterResult:
        """List all builds for a project"""
        params = {"limit": limit}
        if project_id:
            params["projectId"] = project_id
        elif self._default_project_id:
            params["projectId"] = self._default_project_id
        if state:
            params["state"] = state
        
        return await self._make_request(
            method="GET",
            endpoint="/v1/builds",
            params=params
        )
    
    async def get_build(self, build_id: str) -> AdapterResult:
        """Get build details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/v1/builds/{build_id}"
        )
    
    async def cancel_build(self, build_id: str) -> AdapterResult:
        """Cancel a build"""
        return await self._make_request(
            method="POST",
            endpoint=f"/v1/builds/{build_id}/cancel"
        )
    
    # Environment operations
    
    async def list_environments(
        self,
        project_id: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> AdapterResult:
        """List environments for a project"""
        params = {}
        if project_id:
            params["projectId"] = project_id
        elif self._default_project_id:
            params["projectId"] = self._default_project_id
        if team_id:
            params["teamId"] = team_id
        elif self.team_id:
            params["teamId"] = self.team_id
        
        return await self._make_request(
            method="GET",
            endpoint="/v1/envs",
            params=params
        )
    
    async def get_environment(self, project_id: str, env_id: str) -> AdapterResult:
        """Get environment details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/v1/projects/{project_id}/envs/{env_id}"
        )
    
    async def create_environment(
        self,
        project_id: Optional[str] = None,
        key: str = None,
        value: str = None,
        target: List[str] = None,
        env_type: str = "encrypted"
    ) -> AdapterResult:
        """Create a new environment variable"""
        data = {
            "key": key,
            "value": value,
            "target": target or ["production", "preview", "development"],
            "type": env_type
        }
        if project_id:
            data["projectId"] = project_id
        elif self._default_project_id:
            data["projectId"] = self._default_project_id
        
        return await self._make_request(
            method="POST",
            endpoint="/v1/envs",
            json_data=data
        )
    
    async def update_environment(
        self,
        project_id: str,
        env_id: str,
        key: Optional[str] = None,
        value: Optional[str] = None,
        target: Optional[List[str]] = None,
        env_type: Optional[str] = None
    ) -> AdapterResult:
        """Update an environment variable"""
        data = {}
        if key:
            data["key"] = key
        if value:
            data["value"] = value
        if target:
            data["target"] = target
        if env_type:
            data["type"] = env_type
        
        if not data:
            return AdapterResult(
                success=False,
                error="No fields to update"
            )
        
        return await self._make_request(
            method="PATCH",
            endpoint=f"/v1/projects/{project_id}/envs/{env_id}",
            json_data=data
        )
    
    async def delete_environment(self, project_id: str, env_id: str) -> AdapterResult:
        """Delete an environment variable"""
        return await self._make_request(
            method="DELETE",
            endpoint=f"/v1/projects/{project_id}/envs/{env_id}"
        )
    
    # Domain operations
    
    async def list_domains(
        self,
        project_id: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> AdapterResult:
        """List domains for a project"""
        params = {}
        if project_id:
            params["projectId"] = project_id
        elif self._default_project_id:
            params["projectId"] = self._default_project_id
        if team_id:
            params["teamId"] = team_id
        elif self.team_id:
            params["teamId"] = self.team_id
        
        return await self._make_request(
            method="GET",
            endpoint="/v1/domains",
            params=params
        )
    
    async def get_domain(self, domain_id: str) -> AdapterResult:
        """Get domain details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/v1/domains/{domain_id}"
        )
    
    async def create_domain(
        self,
        name: str,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> AdapterResult:
        """Create a new domain"""
        data = {"name": name}
        if team_id:
            data["teamId"] = team_id
        elif self.team_id:
            data["teamId"] = self.team_id
        if project_id:
            data["projectId"] = project_id
        elif self._default_project_id:
            data["projectId"] = self._default_project_id
        
        return await self._make_request(
            method="POST",
            endpoint="/v1/domains",
            json_data=data
        )
    
    async def delete_domain(self, domain_id: str) -> AdapterResult:
        """Delete a domain"""
        return await self._make_request(
            method="DELETE",
            endpoint=f"/v1/domains/{domain_id}"
        )
    
    # Team operations
    
    async def list_teams(self, limit: int = 100) -> AdapterResult:
        """List all teams"""
        return await self._make_request(
            method="GET",
            endpoint="/v1/teams",
            params={"limit": limit}
        )
    
    async def get_team(self, team_id: str) -> AdapterResult:
        """Get team details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/v1/teams/{team_id}"
        )
    
    async def list_team_members(self, team_id: str) -> AdapterResult:
        """List members of a team"""
        return await self._make_request(
            method="GET",
            endpoint=f"/v1/teams/{team_id}/members"
        )
    
    # Log operations
    
    async def list_logs(
        self,
        project_id: Optional[str] = None,
        limit: int = 100,
        since: Optional[str] = None,
        output_format: str = "json"
    ) -> AdapterResult:
        """List logs for a project"""
        params = {
            "limit": limit,
            "outputFormat": output_format
        }
        if project_id:
            params["projectId"] = project_id
        elif self._default_project_id:
            params["projectId"] = self._default_project_id
        if since:
            params["since"] = since
        
        return await self._make_request(
            method="GET",
            endpoint="/v1/logs",
            params=params
        )
    
    async def get_log(self, log_id: str) -> AdapterResult:
        """Get log details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/v1/logs/{log_id}"
        )
    
    # Utility methods
    
    async def deploy_project(
        self,
        project_id: Optional[str] = None,
        branch: str = "main",
        wait_for_completion: bool = False,
        timeout: int = 300  # 5 minutes
    ) -> AdapterResult:
        """
        Deploy a project and optionally wait for completion.
        
        Args:
            project_id: Project ID to deploy
            branch: Branch to deploy
            wait_for_completion: Whether to wait for deployment to complete
            timeout: Timeout in seconds
            
        Returns:
            Deployment result
        """
        # Create deployment
        result = await self.create_deployment(
            project_id=project_id,
            ref=branch
        )
        
        if not result.success:
            return result
        
        if not wait_for_completion:
            return result
        
        # Wait for completion
        deploy = result.data
        if isinstance(deploy, dict):
            deploy_id = deploy.get("id")
            if deploy_id:
                import asyncio
                
                start_time = asyncio.get_event_loop().time()
                while True:
                    # Check status
                    status_result = await self.get_deployment(deploy_id)
                    
                    if status_result.success and status_result.data:
                        deploy_data = status_result.data
                        if isinstance(deploy_data, dict):
                            state = deploy_data.get("state")
                            if state in ["READY", "COMPLETED"]:
                                return IntegrationResult(
                                    success=True,
                                    data={
                                        "deploy": deploy,
                                        "status": deploy_data
                                    }
                                )
                            elif state in ["ERROR", "CANCELED"]:
                                return IntegrationResult(
                                    success=False,
                                    error=f"Deployment failed with state: {state}",
                                    data={"deploy_id": deploy_id, "state": state}
                                )
                    
                    # Check timeout
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        return AdapterResult(
                            success=False,
                            error="Deployment timeout",
                            data={"deploy_id": deploy_id, "elapsed": elapsed}
                        )
                    
                    # Wait before checking again
                    await asyncio.sleep(5)
        
        return result
    
    async def check_deployment_health(self, deployment_id: str) -> AdapterResult:
        """Check the health/status of a deployment"""
        result = await self.get_deployment(deployment_id)
        
        if result.success and result.data:
            deploy = result.data
            if isinstance(deploy, dict):
                state = deploy.get("state")
                ready = deploy.get("ready", False)
                
                return AdapterResult(
                    success=True,
                    data={
                        "status": state,
                        "ready": ready,
                        "healthy": state == "READY" and ready,
                        "deploy": deploy
                    }
                )
        
        return result
