"""
Netlify Integration for UAW
Интеграция с Netlify через доступные инструменты
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from .base import (
    BaseIntegration, IntegrationConfig, IntegrationResult,
    IntegrationStatus, IntegrationCapability, IntegrationError
)


class NetlifyConfig(IntegrationConfig):
    """Configuration for Netlify integration"""
    
    def __init__(self):
        super().__init__(
            name="netlify",
            display_name="Netlify",
            description="Netlify integration for deployments, sites, and management",
            integration_type="mcp",
            base_url="https://api.netlify.com/api/v1",
            api_version="v1",
            timeout=60,  # Deployments can take time
            max_retries=3,
            rate_limit=60,  # Netlify API rate limit: 60 requests/minute
            auth_method="oauth2",
            requires_auth=True,
            supports_read=True,
            supports_write=True,
            supports_webhooks=True,
            supports_search=True,
            max_page_size=100,
            icon_url="https://www.netlify.com/v3/img/components/logomark-dark.svg",
            documentation_url="https://open-api.netlify.com/"
        )
        self._capabilities = [
            IntegrationCapability(
                name="list_sites",
                description="List all sites",
                operation="read",
                parameters=["filter", "limit", "offset"],
                returns="List of sites"
            ),
            IntegrationCapability(
                name="get_site",
                description="Get site details",
                operation="read",
                parameters=["site_id"],
                returns="Site details"
            ),
            IntegrationCapability(
                name="create_site",
                description="Create a new site",
                operation="write",
                parameters=["name", "config", "force_ssl", "custom_domain", "password"],
                returns="Created site"
            ),
            IntegrationCapability(
                name="update_site",
                description="Update site properties",
                operation="write",
                parameters=["site_id", "name", "config", "force_ssl", "custom_domain", "password"],
                returns="Updated site"
            ),
            IntegrationCapability(
                name="delete_site",
                description="Delete a site",
                operation="delete",
                parameters=["site_id"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="list_deploys",
                description="List all deployments for a site",
                operation="read",
                parameters=["site_id", "limit", "offset"],
                returns="List of deployments"
            ),
            IntegrationCapability(
                name="get_deploy",
                description="Get deployment details",
                operation="read",
                parameters=["deploy_id"],
                returns="Deployment details"
            ),
            IntegrationCapability(
                name="create_deploy",
                description="Create a new deployment",
                operation="write",
                parameters=["site_id", "branch", "title", "draft", "production"],
                returns="Created deployment"
            ),
            IntegrationCapability(
                name="restore_deploy",
                description="Restore a deployment",
                operation="write",
                parameters=["site_id", "deploy_id"],
                returns="Restore result"
            ),
            IntegrationCapability(
                name="list_builds",
                description="List all builds for a site",
                operation="read",
                parameters=["site_id", "limit", "offset"],
                returns="List of builds"
            ),
            IntegrationCapability(
                name="get_build",
                description="Get build details",
                operation="read",
                parameters=["build_id"],
                returns="Build details"
            ),
            IntegrationCapability(
                name="cancel_build",
                description="Cancel a build",
                operation="write",
                parameters=["build_id"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="list_forms",
                description="List all forms for a site",
                operation="read",
                parameters=["site_id"],
                returns="List of forms"
            ),
            IntegrationCapability(
                name="get_form",
                description="Get form details",
                operation="read",
                parameters=["form_id"],
                returns="Form details"
            ),
            IntegrationCapability(
                name="list_submissions",
                description="List form submissions",
                operation="read",
                parameters=["form_id", "site_id", "limit", "offset"],
                returns="List of submissions"
            ),
            IntegrationCapability(
                name="get_submission",
                description="Get submission details",
                operation="read",
                parameters=["submission_id"],
                returns="Submission details"
            ),
            IntegrationCapability(
                name="list_functions",
                description="List serverless functions",
                operation="read",
                parameters=["site_id"],
                returns="List of functions"
            ),
            IntegrationCapability(
                name="get_function",
                description="Get function details",
                operation="read",
                parameters=["function_id"],
                returns="Function details"
            ),
            IntegrationCapability(
                name="list_hooks",
                description="List webhooks",
                operation="read",
                parameters=["site_id"],
                returns="List of webhooks"
            ),
            IntegrationCapability(
                name="create_hook",
                description="Create a webhook",
                operation="write",
                parameters=["site_id", "event", "url", "secret"],
                returns="Created webhook"
            ),
            IntegrationCapability(
                name="delete_hook",
                description="Delete a webhook",
                operation="delete",
                parameters=["hook_id"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="list_dns_zones",
                description="List DNS zones",
                operation="read",
                parameters=[],
                returns="List of DNS zones"
            ),
            IntegrationCapability(
                name="get_dns_zone",
                description="Get DNS zone details",
                operation="read",
                parameters=["zone_id"],
                returns="DNS zone details"
            ),
            IntegrationCapability(
                name="create_dns_record",
                description="Create a DNS record",
                operation="write",
                parameters=["zone_id", "type", "name", "value", "ttl", "priority"],
                returns="Created DNS record"
            ),
            IntegrationCapability(
                name="delete_dns_record",
                description="Delete a DNS record",
                operation="delete",
                parameters=["zone_id", "record_id"],
                returns="Success status"
            ),
        ]
        self.capabilities = self._capabilities


class NetlifyIntegration(BaseIntegration):
    """
    Netlify integration using available MCP tools.
    Provides full access to Netlify API through the netlify connector.
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        if config is None:
            config = NetlifyConfig()
        super().__init__(config)
        self.capabilities = config.capabilities if hasattr(config, 'capabilities') else []
        self._default_site_id: Optional[str] = None
    
    async def initialize(self) -> bool:
        """Initialize Netlify integration"""
        try:
            # Check if we can access Netlify API
            result = await self._execute_tool("list_sites", {})
            if result.success and result.data:
                sites = result.data if isinstance(result.data, list) else []
                if sites:
                    self._default_site_id = sites[0].get("id")
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
            try:
                result = await self._execute_tool("list_sites", {})
                if result.success:
                    return IntegrationStatus.CONNECTED
            except Exception:
                pass
        
        return self.status
    
    async def execute(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> IntegrationResult:
        """Execute a Netlify action"""
        if parameters is None:
            parameters = {}
        
        # Add site_id if needed
        if "site_id" not in parameters and self._default_site_id:
            site_actions = [
                "get_site", "update_site", "delete_site",
                "list_deploys", "create_deploy", "list_builds",
                "list_forms", "list_functions", "list_hooks"
            ]
            if any(action.startswith(a) for a in site_actions):
                parameters["site_id"] = self._default_site_id
        
        # Map action to tool name
        tool_name = self._map_action_to_tool(action)
        
        if not tool_name:
            return IntegrationResult(
                success=False,
                error=f"Unknown Netlify action: {action}"
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
            "list_sites": "list_sites",
            "get_site": "get_site",
            "create_site": "create_site",
            "update_site": "update_site",
            "delete_site": "delete_site",
            "list_deploys": "list_deploys",
            "get_deploy": "get_deploy",
            "create_deploy": "create_deploy",
            "restore_deploy": "restore_deploy",
            "list_builds": "list_builds",
            "get_build": "get_build",
            "cancel_build": "cancel_build",
            "list_forms": "list_forms",
            "get_form": "get_form",
            "list_submissions": "list_submissions",
            "get_submission": "get_submission",
            "list_functions": "list_functions",
            "get_function": "get_function",
            "list_hooks": "list_hooks",
            "create_hook": "create_hook",
            "delete_hook": "delete_hook",
            "list_dns_zones": "list_dns_zones",
            "get_dns_zone": "get_dns_zone",
            "create_dns_record": "create_dns_record",
            "delete_dns_record": "delete_dns_record",
        }
        
        return action_mappings.get(action, action)
    
    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> IntegrationResult:
        """Execute a Netlify MCP tool"""
        # Import the actual tool functions
        try:
            # Dynamic import of netlify tools
            import sys
            netlify_module = sys.modules.get('netlify')
            
            if not netlify_module:
                # Try to import
                try:
                    import netlify as netlify_module
                except ImportError:
                    raise IntegrationError(
                        "Netlify integration tools not available",
                        data={"tool": tool_name}
                    )
            
            # Get the tool function
            tool_func = getattr(netlify_module, tool_name, None)
            
            if not tool_func:
                raise IntegrationError(
                    f"Netlify tool not found: {tool_name}",
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
                f"Netlify tool execution failed: {str(e)}",
                data={"tool": tool_name, "parameters": parameters}
            )
    
    # Convenience methods for common operations
    
    async def list_sites(self) -> IntegrationResult:
        """List all sites"""
        return await self.execute("list_sites", {})
    
    async def get_site(self, site_id: Optional[str] = None) -> IntegrationResult:
        """Get site details"""
        params = {}
        if site_id:
            params["site_id"] = site_id
        elif self._default_site_id:
            params["site_id"] = self._default_site_id
        else:
            return IntegrationResult(
                success=False,
                error="No site_id specified and no default site available"
            )
        
        return await self.execute("get_site", params)
    
    async def create_deploy(
        self,
        site_id: Optional[str] = None,
        branch: str = "main",
        title: Optional[str] = None,
        draft: bool = False
    ) -> IntegrationResult:
        """Create a new deployment"""
        params = {
            "branch": branch,
            "draft": draft
        }
        if site_id:
            params["site_id"] = site_id
        elif self._default_site_id:
            params["site_id"] = self._default_site_id
        else:
            return IntegrationResult(
                success=False,
                error="No site_id specified and no default site available"
            )
        
        if title:
            params["title"] = title
        
        return await self.execute("create_deploy", params)
    
    async def get_deploy(self, deploy_id: str) -> IntegrationResult:
        """Get deployment details"""
        return await self.execute("get_deploy", {"deploy_id": deploy_id})
    
    async def list_deploys(self, site_id: Optional[str] = None) -> IntegrationResult:
        """List deployments for a site"""
        params = {}
        if site_id:
            params["site_id"] = site_id
        elif self._default_site_id:
            params["site_id"] = self._default_site_id
        
        return await self.execute("list_deploys", params)
    
    async def check_deployment_health(self, deploy_id: str) -> IntegrationResult:
        """Check the health/status of a deployment"""
        result = await self.get_deploy(deploy_id)
        
        if result.success and result.data:
            deploy = result.data
            if isinstance(deploy, dict):
                status = deploy.get("state", "unknown")
                ready = deploy.get("ready", False)
                
                return IntegrationResult(
                    success=True,
                    data={
                        "status": status,
                        "ready": ready,
                        "healthy": status == "ready" and ready,
                        "deploy": deploy
                    }
                )
        
        return result
    
    async def deploy_site(
        self,
        site_id: Optional[str] = None,
        branch: str = "main",
        wait_for_completion: bool = False,
        timeout: int = 300  # 5 minutes
    ) -> IntegrationResult:
        """
        Deploy a site and optionally wait for completion.
        
        Args:
            site_id: Site ID to deploy
            branch: Branch to deploy
            wait_for_completion: Whether to wait for deployment to complete
            timeout: Timeout in seconds
            
        Returns:
            Deployment result
        """
        # Create deployment
        result = await self.create_deploy(site_id=site_id, branch=branch)
        
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
                    status_result = await self.check_deployment_health(deploy_id)
                    
                    if status_result.success and status_result.data:
                        status_data = status_result.data
                        if status_data.get("healthy") or status_data.get("ready"):
                            return IntegrationResult(
                                success=True,
                                data={
                                    "deploy": deploy,
                                    "status": status_data
                                }
                            )
                    
                    # Check timeout
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > timeout:
                        return IntegrationResult(
                            success=False,
                            error="Deployment timeout",
                            data={"deploy_id": deploy_id, "elapsed": elapsed}
                        )
                    
                    # Wait before checking again
                    await asyncio.sleep(5)
        
        return result
