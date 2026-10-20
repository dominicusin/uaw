"""
Calendar Integration for UAW
Интеграция с календарными сервисами (Google Calendar, Outlook)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime, timezone

from .base import (
    BaseIntegration, IntegrationConfig, IntegrationResult,
    IntegrationStatus, IntegrationCapability, IntegrationError
)


class CalendarType(Enum):
    """Calendar service types"""
    GOOGLE = "google_calendar"
    OUTLOOK = "outlook_calendar"


class CalendarConfig(IntegrationConfig):
    """Configuration for Calendar integration"""
    
    def __init__(self, calendar_type: CalendarType = CalendarType.GOOGLE):
        self.calendar_type = calendar_type
        
        if calendar_type == CalendarType.GOOGLE:
            super().__init__(
                name="google_calendar",
                display_name="Google Calendar",
                description="Google Calendar integration for events and scheduling",
                integration_type="mcp",
                base_url="https://www.googleapis.com/calendar/v3",
                api_version="v3",
                timeout=30,
                max_retries=3,
                rate_limit=1000,  # Google API rate limit
                auth_method="oauth2",
                requires_auth=True,
                supports_read=True,
                supports_write=True,
                supports_webhooks=True,
                supports_search=True,
                max_page_size=2500,
                icon_url="https://www.google.com/favicon.ico",
                documentation_url="https://developers.google.com/calendar/api"
            )
        else:  # Outlook
            super().__init__(
                name="outlook_calendar",
                display_name="Outlook Calendar",
                description="Outlook Calendar integration for events and scheduling",
                integration_type="mcp",
                base_url="https://graph.microsoft.com/v1.0",
                api_version="v1.0",
                timeout=30,
                max_retries=3,
                rate_limit=10000,  # Microsoft Graph API rate limit
                auth_method="oauth2",
                requires_auth=True,
                supports_read=True,
                supports_write=True,
                supports_webhooks=True,
                supports_search=True,
                max_page_size=1000,
                icon_url="https://res.cdn.office.net/mail/16.0.14326.20288/images/favicon.ico",
                documentation_url="https://docs.microsoft.com/en-us/graph/api/overview?view=graph-rest-1.0"
            )
        
        self._capabilities = [
            IntegrationCapability(
                name="list_calendars",
                description="List all calendars",
                operation="read",
                parameters=["min_access_role"],
                returns="List of calendars"
            ),
            IntegrationCapability(
                name="get_calendar",
                description="Get calendar details",
                operation="read",
                parameters=["calendar_id"],
                returns="Calendar details"
            ),
            IntegrationCapability(
                name="list_events",
                description="List events in a calendar",
                operation="read",
                parameters=["calendar_id", "time_min", "time_max", "max_results", "order_by", "q", "single_events", "show_deleted"],
                returns="List of events"
            ),
            IntegrationCapability(
                name="get_event",
                description="Get event details",
                operation="read",
                parameters=["calendar_id", "event_id"],
                returns="Event details"
            ),
            IntegrationCapability(
                name="create_event",
                description="Create a new event",
                operation="write",
                parameters=["calendar_id", "summary", "description", "start", "end", "attendees", "location", "recurrence", "reminders", "conference_data"],
                returns="Created event"
            ),
            IntegrationCapability(
                name="update_event",
                description="Update an event",
                operation="write",
                parameters=["calendar_id", "event_id", "summary", "description", "start", "end", "attendees", "location", "status"],
                returns="Updated event"
            ),
            IntegrationCapability(
                name="delete_event",
                description="Delete an event",
                operation="delete",
                parameters=["calendar_id", "event_id"],
                returns="Success status"
            ),
            IntegrationCapability(
                name="search_events",
                description="Search for events",
                operation="read",
                parameters=["calendar_id", "query", "time_min", "time_max"],
                returns="List of matching events"
            ),
            IntegrationCapability(
                name="find_free_time",
                description="Find free time slots",
                operation="read",
                parameters=["calendar_ids", "time_min", "time_max", "duration", "attendees"],
                returns="List of free time slots"
            ),
            IntegrationCapability(
                name="list_attendees",
                description="List attendees of an event",
                operation="read",
                parameters=["calendar_id", "event_id"],
                returns="List of attendees"
            ),
            IntegrationCapability(
                name="add_attendee",
                description="Add attendee to an event",
                operation="write",
                parameters=["calendar_id", "event_id", "attendee"],
                returns="Updated attendees"
            ),
            IntegrationCapability(
                name="remove_attendee",
                description="Remove attendee from an event",
                operation="write",
                parameters=["calendar_id", "event_id", "attendee_id"],
                returns="Updated attendees"
            ),
            IntegrationCapability(
                name="accept_event",
                description="Accept an event invitation",
                operation="write",
                parameters=["calendar_id", "event_id"],
                returns="Acceptance status"
            ),
            IntegrationCapability(
                name="decline_event",
                description="Decline an event invitation",
                operation="write",
                parameters=["calendar_id", "event_id", "reason"],
                returns="Decline status"
            ),
            IntegrationCapability(
                name="tentatively_accept_event",
                description="Tentatively accept an event",
                operation="write",
                parameters=["calendar_id", "event_id"],
                returns="Tentative acceptance status"
            ),
        ]
        self.capabilities = self._capabilities


class CalendarIntegration(BaseIntegration):
    """
    Calendar integration supporting Google Calendar and Outlook.
    Uses the appropriate MCP connector based on configuration.
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        if config is None:
            config = CalendarConfig()
        super().__init__(config)
        self.capabilities = config.capabilities if hasattr(config, 'capabilities') else []
        self.calendar_type = getattr(config, 'calendar_type', CalendarType.GOOGLE)
        self._primary_calendar_id: Optional[str] = None
    
    async def initialize(self) -> bool:
        """Initialize Calendar integration"""
        try:
            # Check which calendar service is available
            if self.calendar_type == CalendarType.GOOGLE:
                result = await self._execute_tool("list_calendars", {}, service="google_calendar")
            else:
                result = await self._execute_tool("list_calendars", {}, service="outlook_calendar")
            
            if result.success and result.data:
                calendars = result.data if isinstance(result.data, list) else []
                if calendars:
                    # Find primary calendar
                    for cal in calendars:
                        if cal.get("primary", False):
                            self._primary_calendar_id = cal.get("id")
                            break
                    if not self._primary_calendar_id and calendars:
                        self._primary_calendar_id = calendars[0].get("id")
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
                if self.calendar_type == CalendarType.GOOGLE:
                    result = await self._execute_tool("list_calendars", {}, service="google_calendar")
                else:
                    result = await self._execute_tool("list_calendars", {}, service="outlook_calendar")
                
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
        """Execute a Calendar action"""
        if parameters is None:
            parameters = {}
        
        # Add calendar_id if needed
        if "calendar_id" not in parameters and self._primary_calendar_id:
            calendar_actions = [
                "list_events", "get_event", "create_event", "update_event",
                "delete_event", "search_events", "list_attendees",
                "add_attendee", "remove_attendee", "accept_event",
                "decline_event", "tentatively_accept_event"
            ]
            if any(action.startswith(a) for a in calendar_actions):
                parameters["calendar_id"] = self._primary_calendar_id
        
        # Map action to tool name
        tool_name = self._map_action_to_tool(action)
        
        if not tool_name:
            return IntegrationResult(
                success=False,
                error=f"Unknown Calendar action: {action}"
            )
        
        # Execute the tool
        try:
            service = self.config.name
            result = await self._execute_tool(tool_name, parameters, service=service)
            return result
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=str(e)
            )
    
    def _map_action_to_tool(self, action: str) -> str:
        """Map action name to tool name"""
        # Direct mappings for Google Calendar
        google_mappings = {
            "list_calendars": "list_calendars",
            "get_calendar": "get_calendar",
            "list_events": "list_events",
            "get_event": "get_event",
            "create_event": "create_event",
            "update_event": "update_event",
            "delete_event": "delete_event",
            "search_events": "search_events",
            "find_free_time": "find_free_time",
            "list_attendees": "list_attendees",
            "add_attendee": "add_attendee",
            "remove_attendee": "remove_attendee",
            "accept_event": "accept_event",
            "decline_event": "decline_event",
            "tentatively_accept_event": "tentatively_accept_event",
        }
        
        # Direct mappings for Outlook Calendar
        outlook_mappings = {
            "list_calendars": "list_calendars",
            "get_calendar": "get_calendar",
            "list_events": "list_events",
            "get_event": "get_event",
            "create_event": "create_event",
            "update_event": "update_event",
            "delete_event": "delete_event",
            "search_events": "search_events",
            "find_free_time": "find_free_time",
            "list_attendees": "list_attendees",
            "add_attendee": "add_attendee",
            "remove_attendee": "remove_attendee",
            "accept_event": "accept_event",
            "decline_event": "decline_event",
            "tentatively_accept_event": "tentatively_accept_event",
        }
        
        if self.calendar_type == CalendarType.GOOGLE:
            return google_mappings.get(action, action)
        else:
            return outlook_mappings.get(action, action)
    
    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        service: str = "google_calendar"
    ) -> IntegrationResult:
        """Execute a Calendar MCP tool"""
        # Import the actual tool functions
        try:
            # Dynamic import based on service
            if service == "google_calendar":
                import sys
                google_module = sys.modules.get('google_calendar')
                
                if not google_module:
                    try:
                        import google_calendar as google_module
                    except ImportError:
                        raise IntegrationError(
                            "Google Calendar integration tools not available",
                            data={"tool": tool_name}
                        )
                
                tool_func = getattr(google_module, tool_name, None)
            else:  # outlook_calendar
                import sys
                outlook_module = sys.modules.get('outlook_calendar')
                
                if not outlook_module:
                    try:
                        import outlook_calendar as outlook_module
                    except ImportError:
                        raise IntegrationError(
                            "Outlook Calendar integration tools not available",
                            data={"tool": tool_name}
                        )
                
                tool_func = getattr(outlook_module, tool_name, None)
            
            if not tool_func:
                raise IntegrationError(
                    f"Calendar tool not found: {tool_name}",
                    data={"tool": tool_name, "service": service}
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
                f"Calendar tool execution failed: {str(e)}",
                data={"tool": tool_name, "parameters": parameters, "service": service}
            )
    
    # Convenience methods for common operations
    
    async def list_calendars(self) -> IntegrationResult:
        """List all calendars"""
        return await self.execute("list_calendars", {})
    
    async def list_events(
        self,
        calendar_id: Optional[str] = None,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 100
    ) -> IntegrationResult:
        """List events in a calendar"""
        params = {"max_results": max_results}
        if calendar_id:
            params["calendar_id"] = calendar_id
        if time_min:
            params["time_min"] = time_min
        if time_max:
            params["time_max"] = time_max
        
        return await self.execute("list_events", params)
    
    async def create_event(
        self,
        summary: str,
        start: Dict[str, Any],
        end: Dict[str, Any],
        description: Optional[str] = None,
        attendees: Optional[List[Dict[str, Any]]] = None,
        location: Optional[str] = None,
        calendar_id: Optional[str] = None
    ) -> IntegrationResult:
        """Create a new event"""
        params = {
            "summary": summary,
            "start": start,
            "end": end
        }
        if description:
            params["description"] = description
        if attendees:
            params["attendees"] = attendees
        if location:
            params["location"] = location
        if calendar_id:
            params["calendar_id"] = calendar_id
        
        return await self.execute("create_event", params)
    
    async def find_free_time(
        self,
        attendees: List[Dict[str, Any]],
        duration: Dict[str, Any],
        time_min: str,
        time_max: str
    ) -> IntegrationResult:
        """Find free time slots for attendees"""
        return await self.execute(
            "find_free_time",
            {
                "attendees": attendees,
                "duration": duration,
                "time_min": time_min,
                "time_max": time_max
            }
        )
    
    async def schedule_meeting(
        self,
        title: str,
        attendees: List[str],
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> IntegrationResult:
        """
        Schedule a meeting with multiple attendees.
        Automatically finds a suitable time if needed.
        """
        # Convert attendee emails to attendee objects
        attendee_objects = [{"email": email} for email in attendees]
        
        # Try to create event directly first
        start = {"dateTime": start_time, "timeZone": "UTC"}
        end = {"dateTime": end_time, "timeZone": "UTC"}
        
        result = await self.create_event(
            summary=title,
            start=start,
            end=end,
            description=description,
            attendees=attendee_objects,
            location=location
        )
        
        if result.success:
            return result
        
        # If direct scheduling failed, try to find free time
        duration = {"minutes": int((datetime.fromisoformat(end_time) - 
                                    datetime.fromisoformat(start_time)).total_seconds() / 60)}
        
        free_time_result = await self.find_free_time(
            attendees=attendee_objects,
            duration=duration,
            time_min=start_time,
            time_max=end_time
        )
        
        if free_time_result.success and free_time_result.data:
            # Use first available slot
            slots = free_time_result.data if isinstance(free_time_result.data, list) else []
            if slots:
                slot = slots[0]
                start = slot.get("start", start_time)
                end = slot.get("end", end_time)
                
                return await self.create_event(
                    summary=title,
                    start={"dateTime": start, "timeZone": "UTC"},
                    end={"dateTime": end, "timeZone": "UTC"},
                    description=description,
                    attendees=attendee_objects,
                    location=location
                )
        
        return IntegrationResult(
            success=False,
            error="Could not find suitable time for meeting"
        )
