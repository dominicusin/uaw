"""
Microsoft Teams Adapter for UAW
Адаптер для Microsoft Teams через Graph API
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import aiohttp
import json

from .base import (
    BaseAdapter, AdapterConfig, AdapterResult,
    AdapterStatus, AdapterCapability, AdapterError, AuthMethod
)


class TeamsConfig(AdapterConfig):
    """Configuration for Microsoft Teams adapter"""
    
    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None
    ):
        super().__init__(
            name="microsoft_teams",
            display_name="Microsoft Teams",
            description="Microsoft Teams adapter using Graph API",
            base_url="https://graph.microsoft.com",
            api_version="v1.0",
            timeout=30,
            max_retries=3,
            rate_limit=10000,  # Microsoft Graph API rate limit
            auth_method=AuthMethod.OAUTH2,
            access_token=access_token,
            client_id=client_id,
            client_secret=client_secret,
            icon_url="https://res.cdn.office.net/assets/Teams/teams_16x16.png",
            documentation_url="https://docs.microsoft.com/en-us/graph/api/overview?view=graph-rest-1.0"
        )
        self.tenant_id = tenant_id
        self._capabilities = [
            AdapterCapability(
                name="list_teams",
                description="List all teams",
                method="GET",
                endpoint="/me/joinedTeams",
                returns="List of teams"
            ),
            AdapterCapability(
                name="get_team",
                description="Get team details",
                method="GET",
                endpoint="/teams/{team_id}",
                parameters=["team_id"],
                returns="Team details"
            ),
            AdapterCapability(
                name="list_team_members",
                description="List members of a team",
                method="GET",
                endpoint="/teams/{team_id}/members",
                parameters=["team_id"],
                returns="List of members"
            ),
            AdapterCapability(
                name="add_team_member",
                description="Add a member to a team",
                method="POST",
                endpoint="/teams/{team_id}/members",
                parameters=["team_id", "user_id"],
                returns="Member added"
            ),
            AdapterCapability(
                name="remove_team_member",
                description="Remove a member from a team",
                method="DELETE",
                endpoint="/teams/{team_id}/members/{member_id}",
                parameters=["team_id", "member_id"],
                returns="Member removed"
            ),
            AdapterCapability(
                name="list_channels",
                description="List all channels in a team",
                method="GET",
                endpoint="/teams/{team_id}/channels",
                parameters=["team_id"],
                returns="List of channels"
            ),
            AdapterCapability(
                name="get_channel",
                description="Get channel details",
                method="GET",
                endpoint="/teams/{team_id}/channels/{channel_id}",
                parameters=["team_id", "channel_id"],
                returns="Channel details"
            ),
            AdapterCapability(
                name="create_channel",
                description="Create a new channel",
                method="POST",
                endpoint="/teams/{team_id}/channels",
                parameters=["team_id", "name", "description", "visibility"],
                returns="Created channel"
            ),
            AdapterCapability(
                name="send_message",
                description="Send a message to a channel",
                method="POST",
                endpoint="/teams/{team_id}/channels/{channel_id}/messages",
                parameters=["team_id", "channel_id", "content", "content_type"],
                returns="Sent message"
            ),
            AdapterCapability(
                name="reply_to_message",
                description="Reply to a message",
                method="POST",
                endpoint="/teams/{team_id}/channels/{channel_id}/messages/{message_id}/replies",
                parameters=["team_id", "channel_id", "message_id", "content", "content_type"],
                returns="Sent reply"
            ),
            AdapterCapability(
                name="update_message",
                description="Update a message",
                method="PATCH",
                endpoint="/teams/{team_id}/channels/{channel_id}/messages/{message_id}",
                parameters=["team_id", "channel_id", "message_id", "content", "content_type"],
                returns="Updated message"
            ),
            AdapterCapability(
                name="delete_message",
                description="Delete a message",
                method="DELETE",
                endpoint="/teams/{team_id}/channels/{channel_id}/messages/{message_id}",
                parameters=["team_id", "channel_id", "message_id"],
                returns="Message deleted"
            ),
            AdapterCapability(
                name="list_messages",
                description="List messages in a channel",
                method="GET",
                endpoint="/teams/{team_id}/channels/{channel_id}/messages",
                parameters=["team_id", "channel_id", "limit"],
                returns="List of messages"
            ),
            AdapterCapability(
                name="create_meeting",
                description="Create a new meeting",
                method="POST",
                endpoint="/me/events",
                parameters=["subject", "body", "start", "end", "attendees", "is_online_meeting", "online_meeting_provider"],
                returns="Created meeting"
            ),
            AdapterCapability(
                name="get_meeting",
                description="Get meeting details",
                method="GET",
                endpoint="/me/events/{event_id}",
                parameters=["event_id"],
                returns="Meeting details"
            ),
            AdapterCapability(
                name="update_meeting",
                description="Update a meeting",
                method="PATCH",
                endpoint="/me/events/{event_id}",
                parameters=["event_id", "subject", "body", "start", "end", "attendees"],
                returns="Updated meeting"
            ),
            AdapterCapability(
                name="cancel_meeting",
                description="Cancel a meeting",
                method="PATCH",
                endpoint="/me/events/{event_id}",
                parameters=["event_id", "subject"],
                returns="Meeting cancelled"
            ),
            AdapterCapability(
                name="list_meetings",
                description="List user's meetings",
                method="GET",
                endpoint="/me/calendar/events",
                parameters=["start_date_time", "end_date_time"],
                returns="List of meetings"
            ),
            AdapterCapability(
                name="get_user",
                description="Get user details",
                method="GET",
                endpoint="/users/{user_id}",
                parameters=["user_id"],
                returns="User details"
            ),
            AdapterCapability(
                name="search_users",
                description="Search for users",
                method="GET",
                endpoint="/users",
                parameters=["query", "limit"],
                returns="List of users"
            ),
        ]
        self.capabilities = self._capabilities


class MicrosoftTeamsAdapter(BaseAdapter):
    """
    Microsoft Teams adapter using Graph API.
    Provides access to Teams data when the MCP connector is not available.
    """
    
    def __init__(self, config: Optional[TeamsConfig] = None):
        if config is None:
            config = TeamsConfig()
        super().__init__(config)
        self.capabilities = config.capabilities if hasattr(config, 'capabilities') else []
    
    async def initialize(self) -> bool:
        """Initialize the adapter"""
        # Check if we have authentication
        if self.config.auth_method == AuthMethod.OAUTH2:
            if self.config.access_token:
                self.status = AdapterStatus.CONFIGURED
                return True
            else:
                self.status = AdapterStatus.UNAVAILABLE
                self.last_error = "No access token provided"
                return False
        
        self.status = AdapterStatus.UNAVAILABLE
        self.last_error = "No authentication method configured"
        return False
    
    async def check_status(self) -> AdapterStatus:
        """Check current status"""
        if self.status == AdapterStatus.CONFIGURED:
            # Try to make a test request
            result = await self.list_teams()
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
            "list_teams": self.list_teams,
            "get_team": self.get_team,
            "list_team_members": self.list_team_members,
            "add_team_member": self.add_team_member,
            "remove_team_member": self.remove_team_member,
            "list_channels": self.list_channels,
            "get_channel": self.get_channel,
            "create_channel": self.create_channel,
            "send_message": self.send_message,
            "reply_to_message": self.reply_to_message,
            "update_message": self.update_message,
            "delete_message": self.delete_message,
            "list_messages": self.list_messages,
            "create_meeting": self.create_meeting,
            "get_meeting": self.get_meeting,
            "update_meeting": self.update_meeting,
            "cancel_meeting": self.cancel_meeting,
            "list_meetings": self.list_meetings,
            "get_user": self.get_user,
            "search_users": self.search_users,
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
    
    # Team operations
    
    async def list_teams(self) -> AdapterResult:
        """List all teams the user is a member of"""
        return await self._make_request(
            method="GET",
            endpoint="/me/joinedTeams"
        )
    
    async def get_team(self, team_id: str) -> AdapterResult:
        """Get team details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/teams/{team_id}"
        )
    
    async def list_team_members(self, team_id: str) -> AdapterResult:
        """List members of a team"""
        return await self._make_request(
            method="GET",
            endpoint=f"/teams/{team_id}/members"
        )
    
    async def add_team_member(self, team_id: str, user_id: str) -> AdapterResult:
        """Add a member to a team"""
        data = {
            "@odata.bind": f"https://graph.microsoft.com/v1.0/users('{user_id}')"
        }
        return await self._make_request(
            method="POST",
            endpoint=f"/teams/{team_id}/members",
            json_data=data
        )
    
    async def remove_team_member(self, team_id: str, member_id: str) -> AdapterResult:
        """Remove a member from a team"""
        return await self._make_request(
            method="DELETE",
            endpoint=f"/teams/{team_id}/members/{member_id}"
        )
    
    # Channel operations
    
    async def list_channels(self, team_id: str) -> AdapterResult:
        """List all channels in a team"""
        return await self._make_request(
            method="GET",
            endpoint=f"/teams/{team_id}/channels"
        )
    
    async def get_channel(self, team_id: str, channel_id: str) -> AdapterResult:
        """Get channel details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/teams/{team_id}/channels/{channel_id}"
        )
    
    async def create_channel(
        self,
        team_id: str,
        name: str,
        description: Optional[str] = None,
        visibility: str = "private"
    ) -> AdapterResult:
        """Create a new channel"""
        data = {
            "displayName": name,
            "description": description or "",
            "membershipType": visibility  # private, standard, private, or shared
        }
        return await self._make_request(
            method="POST",
            endpoint=f"/teams/{team_id}/channels",
            json_data=data
        )
    
    # Message operations
    
    async def send_message(
        self,
        team_id: str,
        channel_id: str,
        content: str,
        content_type: str = "text"
    ) -> AdapterResult:
        """Send a message to a channel"""
        data = {
            "body": {
                "contentType": content_type,
                "content": content
            }
        }
        return await self._make_request(
            method="POST",
            endpoint=f"/teams/{team_id}/channels/{channel_id}/messages",
            json_data=data
        )
    
    async def reply_to_message(
        self,
        team_id: str,
        channel_id: str,
        message_id: str,
        content: str,
        content_type: str = "text"
    ) -> AdapterResult:
        """Reply to a message"""
        data = {
            "body": {
                "contentType": content_type,
                "content": content
            }
        }
        return await self._make_request(
            method="POST",
            endpoint=f"/teams/{team_id}/channels/{channel_id}/messages/{message_id}/replies",
            json_data=data
        )
    
    async def update_message(
        self,
        team_id: str,
        channel_id: str,
        message_id: str,
        content: str,
        content_type: str = "text"
    ) -> AdapterResult:
        """Update a message"""
        data = {
            "body": {
                "contentType": content_type,
                "content": content
            }
        }
        return await self._make_request(
            method="PATCH",
            endpoint=f"/teams/{team_id}/channels/{channel_id}/messages/{message_id}",
            json_data=data
        )
    
    async def delete_message(
        self,
        team_id: str,
        channel_id: str,
        message_id: str
    ) -> AdapterResult:
        """Delete a message"""
        return await self._make_request(
            method="DELETE",
            endpoint=f"/teams/{team_id}/channels/{channel_id}/messages/{message_id}"
        )
    
    async def list_messages(
        self,
        team_id: str,
        channel_id: str,
        limit: int = 50
    ) -> AdapterResult:
        """List messages in a channel"""
        return await self._make_request(
            method="GET",
            endpoint=f"/teams/{team_id}/channels/{channel_id}/messages",
            params={"$top": limit}
        )
    
    # Meeting operations
    
    async def create_meeting(
        self,
        subject: str,
        body: Optional[str] = None,
        start: str = None,
        end: str = None,
        attendees: Optional[List[Dict[str, str]]] = None,
        is_online_meeting: bool = True
    ) -> AdapterResult:
        """Create a new meeting"""
        data = {
            "subject": subject,
            "body": {"contentType": "text", "content": body or ""},
            "start": {"dateTime": start, "timeZone": "UTC"} if start else None,
            "end": {"dateTime": end, "timeZone": "UTC"} if end else None,
            "isOnlineMeeting": is_online_meeting,
            "onlineMeetingProvider": "teamsForBusiness"
        }
        
        if attendees:
            data["attendees"] = attendees
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        return await self._make_request(
            method="POST",
            endpoint="/me/events",
            json_data=data
        )
    
    async def get_meeting(self, event_id: str) -> AdapterResult:
        """Get meeting details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/me/events/{event_id}"
        )
    
    async def update_meeting(
        self,
        event_id: str,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        attendees: Optional[List[Dict[str, str]]] = None
    ) -> AdapterResult:
        """Update a meeting"""
        data = {}
        if subject:
            data["subject"] = subject
        if body:
            data["body"] = {"contentType": "text", "content": body}
        if start:
            data["start"] = {"dateTime": start, "timeZone": "UTC"}
        if end:
            data["end"] = {"dateTime": end, "timeZone": "UTC"}
        if attendees:
            data["attendees"] = attendees
        
        if not data:
            return AdapterResult(
                success=False,
                error="No fields to update"
            )
        
        return await self._make_request(
            method="PATCH",
            endpoint=f"/me/events/{event_id}",
            json_data=data
        )
    
    async def cancel_meeting(self, event_id: str) -> AdapterResult:
        """Cancel a meeting"""
        data = {
            "subject": "CANCELLED"
        }
        return await self._make_request(
            method="PATCH",
            endpoint=f"/me/events/{event_id}",
            json_data=data
        )
    
    async def list_meetings(
        self,
        start_date_time: Optional[str] = None,
        end_date_time: Optional[str] = None
    ) -> AdapterResult:
        """List user's meetings"""
        params = {}
        if start_date_time:
            params["$filter"] = f"start/dateTime ge {start_date_time}"
        if end_date_time:
            if "$filter" in params:
                params["$filter"] += f" and end/dateTime le {end_date_time}"
            else:
                params["$filter"] = f"end/dateTime le {end_date_time}"
        
        return await self._make_request(
            method="GET",
            endpoint="/me/calendar/events",
            params=params
        )
    
    # User operations
    
    async def get_user(self, user_id: str) -> AdapterResult:
        """Get user details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/users/{user_id}"
        )
    
    async def search_users(self, query: str, limit: int = 10) -> AdapterResult:
        """Search for users"""
        return await self._make_request(
            method="GET",
            endpoint="/users",
            params={
                "$count": "true",
                "$search": query,
                "$top": limit
            }
        )
    
    # Utility methods
    
    async def notify_team(
        self,
        team_id: str,
        channel_id: str,
        message: str
    ) -> AdapterResult:
        """Send a notification to a team channel"""
        return await self.send_message(
            team_id=team_id,
            channel_id=channel_id,
            content=message
        )
    
    async def schedule_meeting(
        self,
        title: str,
        attendees: List[str],
        start_time: str,
        end_time: str,
        description: Optional[str] = None
    ) -> AdapterResult:
        """Schedule a meeting with attendees"""
        attendee_objects = [{"emailAddress": {"address": email}} for email in attendees]
        
        return await self.create_meeting(
            subject=title,
            body=description,
            start=start_time,
            end=end_time,
            attendees=attendee_objects
        )
