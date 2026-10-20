"""
Calendly Adapter for UAW
Адаптер для Calendly через REST API
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


class CalendlyConfig(AdapterConfig):
    """Configuration for Calendly adapter"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None
    ):
        super().__init__(
            name="calendly",
            display_name="Calendly",
            description="Calendly adapter for scheduling and availability",
            base_url="https://api.calendly.com",
            api_version="v2",
            timeout=30,
            max_retries=3,
            rate_limit=100,  # Calendly API rate limit
            auth_method=AuthMethod.API_KEY,
            api_key=api_key,
            icon_url="https://calendly.com/assets/calendly-icon-128x128.png",
            documentation_url="https://developer.calendly.com/docs"
        )
        self.webhook_secret = webhook_secret
        self._capabilities = [
            AdapterCapability(
                name="get_user",
                description="Get authenticated user details",
                method="GET",
                endpoint="/users/me",
                returns="User details"
            ),
            AdapterCapability(
                name="list_users",
                description="List all users in organization",
                method="GET",
                endpoint="/users",
                parameters=["email", "organization", "limit", "cursor"],
                returns="List of users"
            ),
            AdapterCapability(
                name="get_user_availability",
                description="Get user availability schedule",
                method="GET",
                endpoint="/users/{user_id}/availability_schedule",
                parameters=["user_id"],
                returns="Availability schedule"
            ),
            AdapterCapability(
                name="list_event_types",
                description="List event types for a user",
                method="GET",
                endpoint="/users/{user_id}/event_types",
                parameters=["user_id", "limit", "cursor"],
                returns="List of event types"
            ),
            AdapterCapability(
                name="get_event_type",
                description="Get event type details",
                method="GET",
                endpoint="/event_types/{event_type_id}",
                parameters=["event_type_id"],
                returns="Event type details"
            ),
            AdapterCapability(
                name="create_event_type",
                description="Create a new event type",
                method="POST",
                endpoint="/event_types",
                parameters=["name", "type", "duration_minutes", "user_id", "color", "description"],
                returns="Created event type"
            ),
            AdapterCapability(
                name="update_event_type",
                description="Update an event type",
                method="PATCH",
                endpoint="/event_types/{event_type_id}",
                parameters=["event_type_id", "name", "type", "duration_minutes", "color", "description", "active"],
                returns="Updated event type"
            ),
            AdapterCapability(
                name="delete_event_type",
                description="Delete an event type",
                method="DELETE",
                endpoint="/event_types/{event_type_id}",
                parameters=["event_type_id"],
                returns="Success status"
            ),
            AdapterCapability(
                name="list_scheduled_events",
                description="List scheduled events",
                method="GET",
                endpoint="/scheduled_events",
                parameters=["organization", "user", "event_type", "status", "from", "to", "limit", "cursor"],
                returns="List of scheduled events"
            ),
            AdapterCapability(
                name="get_scheduled_event",
                description="Get scheduled event details",
                method="GET",
                endpoint="/scheduled_events/{event_id}",
                parameters=["event_id"],
                returns="Event details"
            ),
            AdapterCapability(
                name="cancel_scheduled_event",
                description="Cancel a scheduled event",
                method="POST",
                endpoint="/scheduled_events/{event_id}/cancellation",
                parameters=["event_id", "reason"],
                returns="Cancellation result"
            ),
            AdapterCapability(
                name="create_invitee",
                description="Create an invitee for an event",
                method="POST",
                endpoint="/scheduled_events/{event_id}/invitees",
                parameters=["event_id", "email", "name", "first_name", "last_name"],
                returns="Created invitee"
            ),
            AdapterCapability(
                name="list_invitees",
                description="List invitees for an event",
                method="GET",
                endpoint="/scheduled_events/{event_id}/invitees",
                parameters=["event_id", "limit", "cursor"],
                returns="List of invitees"
            ),
            AdapterCapability(
                name="get_invitee",
                description="Get invitee details",
                method="GET",
                endpoint="/scheduled_events/{event_id}/invitees/{invitee_id}",
                parameters=["event_id", "invitee_id"],
                returns="Invitee details"
            ),
            AdapterCapability(
                name="create_one_off_event",
                description="Create a one-off event",
                method="POST",
                endpoint="/one_off_events",
                parameters=["event_type", "start_time", "invitees", "email_invitees", "custom_questions"],
                returns="Created one-off event"
            ),
            AdapterCapability(
                name="list_event_type_available_times",
                description="List available times for an event type",
                method="GET",
                endpoint="/event_types/{event_type_id}/available_times",
                parameters=["event_type_id", "start_time", "end_time", "timezone", "interval_minutes"],
                returns="List of available times"
            ),
            AdapterCapability(
                name="list_organizations",
                description="List organizations",
                method="GET",
                endpoint="/organizations",
                parameters=["limit", "cursor"],
                returns="List of organizations"
            ),
            AdapterCapability(
                name="get_organization",
                description="Get organization details",
                method="GET",
                endpoint="/organizations/{organization_id}",
                parameters=["organization_id"],
                returns="Organization details"
            ),
            AdapterCapability(
                name="list_webhooks",
                description="List webhooks",
                method="GET",
                endpoint="/webhook_subscriptions",
                parameters=["organization", "user", "limit", "cursor"],
                returns="List of webhooks"
            ),
            AdapterCapability(
                name="create_webhook",
                description="Create a webhook",
                method="POST",
                endpoint="/webhook_subscriptions",
                parameters=["url", "events", "organization", "user", "secret"],
                returns="Created webhook"
            ),
            AdapterCapability(
                name="delete_webhook",
                description="Delete a webhook",
                method="DELETE",
                endpoint="/webhook_subscriptions/{webhook_id}",
                parameters=["webhook_id"],
                returns="Success status"
            ),
        ]
        self.capabilities = self._capabilities


class CalendlyAdapter(BaseAdapter):
    """
    Calendly adapter using REST API.
    Provides access to Calendly scheduling functionality.
    """
    
    def __init__(self, config: Optional[CalendlyConfig] = None):
        if config is None:
            config = CalendlyConfig()
        super().__init__(config)
        self.capabilities = config.capabilities if hasattr(config, 'capabilities') else []
        self._user_id: Optional[str] = None
    
    async def initialize(self) -> bool:
        """Initialize the adapter"""
        # Check if we have API key
        if not self.config.api_key:
            self.status = AdapterStatus.UNAVAILABLE
            self.last_error = "No API key provided"
            return False
        
        # Try to get user info to verify connection
        result = await self.get_user()
        if result.success and result.data:
            user_data = result.data
            if isinstance(user_data, dict):
                self._user_id = user_data.get("uri") or user_data.get("id")
                self.status = AdapterStatus.CONFIGURED
                return True
        
        self.status = AdapterStatus.UNAVAILABLE
        self.last_error = "Failed to verify API key"
        return False
    
    async def check_status(self) -> AdapterStatus:
        """Check current status"""
        if self.status == AdapterStatus.CONFIGURED:
            # Try to make a test request
            result = await self.get_user()
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
            "get_user": self.get_user,
            "list_users": self.list_users,
            "get_user_availability": self.get_user_availability,
            "list_event_types": self.list_event_types,
            "get_event_type": self.get_event_type,
            "create_event_type": self.create_event_type,
            "update_event_type": self.update_event_type,
            "delete_event_type": self.delete_event_type,
            "list_scheduled_events": self.list_scheduled_events,
            "get_scheduled_event": self.get_scheduled_event,
            "cancel_scheduled_event": self.cancel_scheduled_event,
            "create_invitee": self.create_invitee,
            "list_invitees": self.list_invitees,
            "get_invitee": self.get_invitee,
            "create_one_off_event": self.create_one_off_event,
            "list_event_type_available_times": self.list_event_type_available_times,
            "list_organizations": self.list_organizations,
            "get_organization": self.get_organization,
            "list_webhooks": self.list_webhooks,
            "create_webhook": self.create_webhook,
            "delete_webhook": self.delete_webhook,
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
    
    # User operations
    
    async def get_user(self) -> AdapterResult:
        """Get authenticated user details"""
        return await self._make_request(
            method="GET",
            endpoint="/users/me"
        )
    
    async def list_users(
        self,
        email: Optional[str] = None,
        organization: Optional[str] = None,
        limit: int = 100
    ) -> AdapterResult:
        """List all users in organization"""
        params = {"count": limit}
        if email:
            params["email"] = email
        if organization:
            params["organization"] = organization
        
        return await self._make_request(
            method="GET",
            endpoint="/users",
            params=params
        )
    
    async def get_user_availability(self, user_id: Optional[str] = None) -> AdapterResult:
        """Get user availability schedule"""
        uri = user_id or self._user_id or ""
        return await self._make_request(
            method="GET",
            endpoint=f"/users/{uri}/availability_schedule"
        )
    
    # Event type operations
    
    async def list_event_types(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> AdapterResult:
        """List event types for a user"""
        uri = user_id or self._user_id or ""
        return await self._make_request(
            method="GET",
            endpoint=f"/users/{uri}/event_types",
            params={"count": limit}
        )
    
    async def get_event_type(self, event_type_id: str) -> AdapterResult:
        """Get event type details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/event_types/{event_type_id}"
        )
    
    async def create_event_type(
        self,
        name: str,
        type: str = "standard",
        duration_minutes: int = 30,
        user_id: Optional[str] = None,
        color: str = "#4285f4",
        description: Optional[str] = None
    ) -> AdapterResult:
        """Create a new event type"""
        data = {
            "name": name,
            "type": type,
            "duration_minutes": duration_minutes,
            "color": color
        }
        if description:
            data["description"] = description
        if user_id:
            data["user"] = user_id
        elif self._user_id:
            data["user"] = self._user_id
        
        return await self._make_request(
            method="POST",
            endpoint="/event_types",
            json_data=data
        )
    
    async def update_event_type(
        self,
        event_type_id: str,
        name: Optional[str] = None,
        type: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        color: Optional[str] = None,
        description: Optional[str] = None,
        active: Optional[bool] = None
    ) -> AdapterResult:
        """Update an event type"""
        data = {}
        if name:
            data["name"] = name
        if type:
            data["type"] = type
        if duration_minutes:
            data["duration_minutes"] = duration_minutes
        if color:
            data["color"] = color
        if description:
            data["description"] = description
        if active is not None:
            data["active"] = active
        
        if not data:
            return AdapterResult(
                success=False,
                error="No fields to update"
            )
        
        return await self._make_request(
            method="PATCH",
            endpoint=f"/event_types/{event_type_id}",
            json_data=data
        )
    
    async def delete_event_type(self, event_type_id: str) -> AdapterResult:
        """Delete an event type"""
        return await self._make_request(
            method="DELETE",
            endpoint=f"/event_types/{event_type_id}"
        )
    
    # Scheduled event operations
    
    async def list_scheduled_events(
        self,
        organization: Optional[str] = None,
        user: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        from_time: Optional[str] = None,
        to: Optional[str] = None,
        limit: int = 100
    ) -> AdapterResult:
        """List scheduled events"""
        params = {"count": limit}
        if organization:
            params["organization"] = organization
        if user:
            params["user"] = user
        elif self._user_id:
            params["user"] = self._user_id
        if event_type:
            params["event_type"] = event_type
        if status:
            params["status"] = status
        if from_time:
            params["from"] = from_time
        if to:
            params["to"] = to
        
        return await self._make_request(
            method="GET",
            endpoint="/scheduled_events",
            params=params
        )
    
    async def get_scheduled_event(self, event_id: str) -> AdapterResult:
        """Get scheduled event details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/scheduled_events/{event_id}"
        )
    
    async def cancel_scheduled_event(
        self,
        event_id: str,
        reason: Optional[str] = None
    ) -> AdapterResult:
        """Cancel a scheduled event"""
        data = {}
        if reason:
            data["reason"] = reason
        
        return await self._make_request(
            method="POST",
            endpoint=f"/scheduled_events/{event_id}/cancellation",
            json_data=data
        )
    
    # Invitee operations
    
    async def create_invitee(
        self,
        event_id: str,
        email: str,
        name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> AdapterResult:
        """Create an invitee for an event"""
        data = {"email": email}
        if name:
            data["name"] = name
        if first_name:
            data["first_name"] = first_name
        if last_name:
            data["last_name"] = last_name
        
        return await self._make_request(
            method="POST",
            endpoint=f"/scheduled_events/{event_id}/invitees",
            json_data=data
        )
    
    async def list_invitees(
        self,
        event_id: str,
        limit: int = 100
    ) -> AdapterResult:
        """List invitees for an event"""
        return await self._make_request(
            method="GET",
            endpoint=f"/scheduled_events/{event_id}/invitees",
            params={"count": limit}
        )
    
    async def get_invitee(self, event_id: str, invitee_id: str) -> AdapterResult:
        """Get invitee details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/scheduled_events/{event_id}/invitees/{invitee_id}"
        )
    
    # One-off event operations
    
    async def create_one_off_event(
        self,
        event_type: str,
        start_time: str,
        invitees: Optional[List[Dict[str, str]]] = None,
        email_invitees: Optional[List[str]] = None
    ) -> AdapterResult:
        """Create a one-off event"""
        data = {
            "event_type": event_type,
            "start_time": start_time
        }
        
        if invitees:
            data["invitees"] = invitees
        if email_invitees:
            data["email_invitees"] = [{"email": email} for email in email_invitees]
        
        return await self._make_request(
            method="POST",
            endpoint="/one_off_events",
            json_data=data
        )
    
    async def list_event_type_available_times(
        self,
        event_type_id: str,
        start_time: str,
        end_time: str,
        timezone: str = "UTC",
        interval_minutes: int = 30
    ) -> AdapterResult:
        """List available times for an event type"""
        params = {
            "start_time": start_time,
            "end_time": end_time,
            "timezone": timezone,
            "interval_minutes": interval_minutes
        }
        
        return await self._make_request(
            method="GET",
            endpoint=f"/event_types/{event_type_id}/available_times",
            params=params
        )
    
    # Organization operations
    
    async def list_organizations(self, limit: int = 100) -> AdapterResult:
        """List organizations"""
        return await self._make_request(
            method="GET",
            endpoint="/organizations",
            params={"count": limit}
        )
    
    async def get_organization(self, organization_id: str) -> AdapterResult:
        """Get organization details"""
        return await self._make_request(
            method="GET",
            endpoint=f"/organizations/{organization_id}"
        )
    
    # Webhook operations
    
    async def list_webhooks(
        self,
        organization: Optional[str] = None,
        user: Optional[str] = None,
        limit: int = 100
    ) -> AdapterResult:
        """List webhooks"""
        params = {"count": limit}
        if organization:
            params["organization"] = organization
        if user:
            params["user"] = user
        elif self._user_id:
            params["user"] = self._user_id
        
        return await self._make_request(
            method="GET",
            endpoint="/webhook_subscriptions",
            params=params
        )
    
    async def create_webhook(
        self,
        url: str,
        events: List[str],
        organization: Optional[str] = None,
        user: Optional[str] = None,
        secret: Optional[str] = None
    ) -> AdapterResult:
        """Create a webhook"""
        data = {
            "url": url,
            "events": events
        }
        if organization:
            data["organization"] = organization
        if user:
            data["user"] = user
        elif self._user_id:
            data["user"] = self._user_id
        if secret:
            data["secret"] = secret
        
        return await self._make_request(
            method="POST",
            endpoint="/webhook_subscriptions",
            json_data=data
        )
    
    async def delete_webhook(self, webhook_id: str) -> AdapterResult:
        """Delete a webhook"""
        return await self._make_request(
            method="DELETE",
            endpoint=f"/webhook_subscriptions/{webhook_id}"
        )
    
    # Utility methods
    
    async def schedule_meeting(
        self,
        event_type_id: str,
        start_time: str,
        attendees: List[str],
        end_time: Optional[str] = None
    ) -> AdapterResult:
        """Schedule a meeting using Calendly"""
        # Create one-off event
        result = await self.create_one_off_event(
            event_type=event_type_id,
            start_time=start_time,
            email_invitees=attendees
        )
        
        if result.success:
            return result
        
        # Fallback: try to find available time and schedule
        available_times = await self.list_event_type_available_times(
            event_type_id=event_type_id,
            start_time=start_time,
            end_time=end_time or start_time  # Use start_time as fallback
        )
        
        if available_times.success and available_times.data:
            times = available_times.data
            if isinstance(times, dict) and times.get("collection"):
                first_time = times["collection"][0] if times["collection"] else None
                if first_time:
                    return await self.create_one_off_event(
                        event_type=event_type_id,
                        start_time=first_time.get("start_time"),
                        email_invitees=attendees
                    )
        
        return AdapterResult(
            success=False,
            error="Could not find available time for meeting"
        )
