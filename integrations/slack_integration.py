"""
Slack Integration for UAW
Интеграция с Slack через доступные инструменты
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from .base import (
    BaseIntegration, IntegrationConfig, IntegrationResult,
    IntegrationStatus, IntegrationCapability, IntegrationError
)


class SlackConfig(IntegrationConfig):
    """Configuration for Slack integration"""
    
    def __init__(self):
        super().__init__(
            name="slack",
            display_name="Slack",
            description="Slack integration for messages, channels, and canvases",
            integration_type="mcp",
            base_url="https://slack.com/api",
            api_version="v1",
            timeout=30,
            max_retries=3,
            rate_limit=50,  # Slack API rate limit: ~50 requests/minute
            auth_method="oauth2",
            requires_auth=True,
            supports_read=True,
            supports_write=True,
            supports_webhooks=True,
            supports_search=True,
            max_page_size=1000,
            icon_url="https://cdn.slack-edge.com/marketing/img/icons/icon-128x128.png",
            documentation_url="https://api.slack.com/methods"
        )
        self._capabilities = [
            IntegrationCapability(
                name="list_channels",
                description="List all channels",
                operation="read",
                parameters=["cursor", "limit", "types", "exclude_archived"],
                returns="List of channels"
            ),
            IntegrationCapability(
                name="get_channel",
                description="Get channel details",
                operation="read",
                parameters=["channel_id"],
                returns="Channel details"
            ),
            IntegrationCapability(
                name="search_channels",
                description="Search for channels",
                operation="read",
                parameters=["query", "limit", "cursor"],
                returns="List of matching channels"
            ),
            IntegrationCapability(
                name="list_messages",
                description="List messages in a channel",
                operation="read",
                parameters=["channel_id", "limit", "cursor", "oldest", "latest"],
                returns="List of messages"
            ),
            IntegrationCapability(
                name="get_message",
                description="Get message details",
                operation="read",
                parameters=["channel_id", "message_id"],
                returns="Message details"
            ),
            IntegrationCapability(
                name="search_messages",
                description="Search for messages",
                operation="read",
                parameters=["query", "channel_id", "limit", "cursor"],
                returns="List of matching messages"
            ),
            IntegrationCapability(
                name="send_message",
                description="Send a message to a channel",
                operation="write",
                parameters=["channel_id", "text", "blocks", "attachments", "thread_ts", "reply_broadcast"],
                returns="Sent message"
            ),
            IntegrationCapability(
                name="update_message",
                description="Update a message",
                operation="write",
                parameters=["channel_id", "message_id", "text", "blocks", "attachments"],
                returns="Updated message"
            ),
            IntegrationCapability(
                name="delete_message",
                description="Delete a message",
                operation="delete",
                parameters=["channel_id", "message_id"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="add_reaction",
                description="Add a reaction to a message",
                operation="write",
                parameters=["channel_id", "message_id", "name"],
                returns="Reaction result"
            ),
            IntegrationCapability(
                name="remove_reaction",
                description="Remove a reaction from a message",
                operation="write",
                parameters=["channel_id", "message_id", "name"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="list_users",
                description="List all users",
                operation="read",
                parameters=["cursor", "limit"],
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
                name="search_users",
                description="Search for users",
                operation="read",
                parameters=["query", "limit", "cursor"],
                returns="List of matching users"
            ),
            IntegrationCapability(
                name="get_user_profile",
                description="Get authenticated user profile",
                operation="read",
                parameters=[],
                returns="User profile"
            ),
            IntegrationCapability(
                name="list_canvases",
                description="List all canvases",
                operation="read",
                parameters=["limit", "cursor"],
                returns="List of canvases"
            ),
            IntegrationCapability(
                name="get_canvas",
                description="Get canvas details",
                operation="read",
                parameters=["canvas_id"],
                returns="Canvas details"
            ),
            IntegrationCapability(
                name="create_canvas",
                description="Create a new canvas",
                operation="write",
                parameters=["title", "visibility"],
                returns="Created canvas"
            ),
            IntegrationCapability(
                name="update_canvas",
                description="Update a canvas",
                operation="write",
                parameters=["canvas_id", "title", "visibility"],
                returns="Updated canvas"
            ),
            IntegrationCapability(
                name="delete_canvas",
                description="Delete a canvas",
                operation="delete",
                parameters=["canvas_id"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="list_canvas_elements",
                description="List elements in a canvas",
                operation="read",
                parameters=["canvas_id", "limit", "cursor"],
                returns="List of canvas elements"
            ),
            IntegrationCapability(
                name="add_canvas_element",
                description="Add element to a canvas",
                operation="write",
                parameters=["canvas_id", "type", "x", "y", "content"],
                returns="Created element"
            ),
        ]
        self.capabilities = self._capabilities


class SlackIntegration(BaseIntegration):
    """
    Slack integration using available MCP tools.
    Provides full access to Slack API through the slack connector.
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        if config is None:
            config = SlackConfig()
        super().__init__(config)
        self.capabilities = config.capabilities if hasattr(config, 'capabilities') else []
        self._user_id: Optional[str] = None
        self._default_channel: Optional[str] = None
    
    async def initialize(self) -> bool:
        """Initialize Slack integration"""
        try:
            # Check if we can access Slack API
            result = await self._execute_tool("get_user_profile", {})
            if result.success and result.data:
                self._user_id = result.data.get("id") or result.data.get("user_id")
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
                result = await self._execute_tool("get_user_profile", {})
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
        """Execute a Slack action"""
        if parameters is None:
            parameters = {}
        
        # Map action to tool name
        tool_name = self._map_action_to_tool(action)
        
        if not tool_name:
            return IntegrationResult(
                success=False,
                error=f"Unknown Slack action: {action}"
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
            "list_channels": "list_channels",
            "get_channel": "get_channel",
            "search_channels": "search_channels",
            "list_messages": "list_messages",
            "get_message": "get_message",
            "search_messages": "search_messages",
            "send_message": "send_message",
            "update_message": "update_message",
            "delete_message": "delete_message",
            "add_reaction": "add_reaction",
            "remove_reaction": "remove_reaction",
            "list_users": "list_users",
            "get_user": "get_user",
            "search_users": "search_users",
            "get_user_profile": "get_user_profile",
            "list_canvases": "list_canvases",
            "get_canvas": "get_canvas",
            "create_canvas": "create_canvas",
            "update_canvas": "update_canvas",
            "delete_canvas": "delete_canvas",
            "list_canvas_elements": "list_canvas_elements",
            "add_canvas_element": "add_canvas_element",
        }
        
        return action_mappings.get(action, action)
    
    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> IntegrationResult:
        """Execute a Slack MCP tool"""
        # Import the actual tool functions
        try:
            # Dynamic import of slack tools
            import sys
            slack_module = sys.modules.get('slack')
            
            if not slack_module:
                # Try to import
                try:
                    import slack as slack_module
                except ImportError:
                    raise IntegrationError(
                        "Slack integration tools not available",
                        data={"tool": tool_name}
                    )
            
            # Get the tool function
            tool_func = getattr(slack_module, tool_name, None)
            
            if not tool_func:
                raise IntegrationError(
                    f"Slack tool not found: {tool_name}",
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
                f"Slack tool execution failed: {str(e)}",
                data={"tool": tool_name, "parameters": parameters}
            )
    
    # Convenience methods for common operations
    
    async def send_message(
        self,
        channel_id: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None
    ) -> IntegrationResult:
        """Send a message to a channel"""
        params = {
            "channel_id": channel_id,
            "text": text
        }
        if blocks:
            params["blocks"] = blocks
        if thread_ts:
            params["thread_ts"] = thread_ts
        
        return await self.execute("send_message", params)
    
    async def list_channels(
        self,
        limit: int = 100,
        exclude_archived: bool = True
    ) -> IntegrationResult:
        """List all channels"""
        return await self.execute(
            "list_channels",
            {
                "limit": limit,
                "exclude_archived": exclude_archived
            }
        )
    
    async def search_messages(
        self,
        query: str,
        channel_id: Optional[str] = None,
        limit: int = 50
    ) -> IntegrationResult:
        """Search for messages"""
        params = {
            "query": query,
            "limit": limit
        }
        if channel_id:
            params["channel_id"] = channel_id
        
        return await self.execute("search_messages", params)
    
    async def get_user_profile(self) -> IntegrationResult:
        """Get authenticated user profile"""
        return await self.execute("get_user_profile", {})
    
    async def list_users(self, limit: int = 100) -> IntegrationResult:
        """List all users"""
        return await self.execute("list_users", {"limit": limit})
    
    async def notify_team(
        self,
        team_id: str,
        message: str,
        channel_id: Optional[str] = None
    ) -> IntegrationResult:
        """Notify a team with a message"""
        # If channel_id is provided, use it directly
        if channel_id:
            return await self.send_message(channel_id, message)
        
        # Otherwise, find team channel and send message
        # This would need to be implemented based on team-channel mapping
        return await self.send_message(team_id, message)
    
    async def create_thread(
        self,
        channel_id: str,
        initial_message: str
    ) -> IntegrationResult:
        """Create a new thread in a channel"""
        # Send initial message
        result = await self.send_message(channel_id, initial_message)
        
        if result.success and result.data:
            # Get the message timestamp for threading
            message = result.data
            if isinstance(message, dict):
                ts = message.get("ts")
                if ts:
                    # Return the thread timestamp
                    return IntegrationResult(
                        success=True,
                        data={
                            "channel_id": channel_id,
                            "thread_ts": ts,
                            "initial_message": message
                        }
                    )
        
        return result
    
    async def reply_to_thread(
        self,
        channel_id: str,
        thread_ts: str,
        message: str
    ) -> IntegrationResult:
        """Reply to an existing thread"""
        return await self.send_message(
            channel_id,
            message,
            thread_ts=thread_ts
        )
