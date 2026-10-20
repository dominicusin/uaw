"""
Event Model for UAW
Модель встречи, события календаря или напоминания
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

from .base import BaseModel, EntityType, UAWIdentifier


class EventType(Enum):
    """Type of event"""
    MEETING = "meeting"
    APPOINTMENT = "appointment"
    REMINDER = "reminder"
    DEADLINE = "deadline"
    WORKSHOP = "workshop"
    PRESENTATION = "presentation"
    SOCIAL = "social"
    OTHER = "other"


class EventStatus(Enum):
    """Status of an event"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class EventVisibility(Enum):
    """Visibility of an event"""
    PUBLIC = "public"
    PRIVATE = "private"
    ORGANIZATION = "organization"
    INVITE_ONLY = "invite_only"


class RSVPStatus(Enum):
    """RSVP status for attendees"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"


@dataclass
class Attendee:
    """Event attendee"""
    person_id: str
    person_name: Optional[str] = None
    person_email: Optional[str] = None
    rsvp_status: RSVPStatus = RSVPStatus.PENDING
    rsvp_updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "person_id": self.person_id,
            "person_name": self.person_name,
            "person_email": self.person_email,
            "rsvp_status": self.rsvp_status.value,
            "rsvp_updated_at": self.rsvp_updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Attendee":
        return cls(
            person_id=data.get("person_id", ""),
            person_name=data.get("person_name"),
            person_email=data.get("person_email"),
            rsvp_status=RSVPStatus(data.get("rsvp_status", "pending")),
            rsvp_updated_at=data.get("rsvp_updated_at")
        )


@dataclass
class EventRecurrence:
    """Event recurrence pattern"""
    type: str = "none"  # none, daily, weekly, monthly, yearly, custom
    interval: int = 1
    days_of_week: List[str] = field(default_factory=list)  # e.g., ["MO", "WE", "FR"]
    day_of_month: Optional[int] = None
    month_of_year: Optional[int] = None
    end_date: Optional[str] = None
    max_occurrences: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "interval": self.interval,
            "days_of_week": self.days_of_week,
            "day_of_month": self.day_of_month,
            "month_of_year": self.month_of_year,
            "end_date": self.end_date,
            "max_occurrences": self.max_occurrences
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventRecurrence":
        return cls(
            type=data.get("type", "none"),
            interval=data.get("interval", 1),
            days_of_week=data.get("days_of_week", []),
            day_of_month=data.get("day_of_month"),
            month_of_year=data.get("month_of_year"),
            end_date=data.get("end_date"),
            max_occurrences=data.get("max_occurrences")
        )


@dataclass
class Event(BaseModel):
    """
    Event model representing a meeting, calendar event, or reminder.
    
    Attributes:
        uaw_id: Unique UAW identifier
        title: Event title
        event_type: Type of event
        status: Current event status
        visibility: Event visibility
        start_time: Event start time
        end_time: Event end time
        time_zone: Event timezone
        location: Event location (physical or virtual)
        description: Event description
        agenda: Event agenda
        organizer_id: UAW ID of event organizer
        attendees: List of attendees
        required_attendees: List of required attendee IDs
        optional_attendees: List of optional attendee IDs
        recurrence: Event recurrence pattern
        parent_event_id: UAW ID of parent event (for recurring events)
        related_projects: List of related project IDs
        related_tasks: List of related task IDs
        related_issues: List of related issue IDs
        related_documents: List of related document IDs
        calendar_id: UAW ID of calendar this event belongs to
        meeting_link: Virtual meeting link
        reminders: List of reminder times (in minutes before start)
        external_ids: IDs in external systems
        custom_fields: Custom event fields
    """
    
    entity_type: ClassVar[EntityType] = EntityType.EVENT
    
    event_type: EventType = EventType.MEETING
    status: EventStatus = EventStatus.SCHEDULED
    visibility: EventVisibility = EventVisibility.PRIVATE
    
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    time_zone: str = "UTC"
    location: Optional[str] = None
    agenda: Optional[str] = None
    
    organizer_id: Optional[str] = None
    attendees: List[Attendee] = field(default_factory=list)
    required_attendees: List[str] = field(default_factory=list)
    optional_attendees: List[str] = field(default_factory=list)
    
    recurrence: Optional[EventRecurrence] = None
    parent_event_id: Optional[str] = None
    
    # Related entities
    related_projects: List[str] = field(default_factory=list)
    related_tasks: List[str] = field(default_factory=list)
    related_issues: List[str] = field(default_factory=list)
    related_documents: List[str] = field(default_factory=list)
    
    calendar_id: Optional[str] = None
    meeting_link: Optional[str] = None
    reminders: List[int] = field(default_factory=list)  # Minutes before start
    
    # External system IDs
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.attendees, dict):
            self.attendees = [Attendee.from_dict(a) for a in self.attendees.values()]
        if isinstance(self.reminders, str):
            self.reminders = [int(self.reminders)]
        if isinstance(self.recurrence, dict):
            self.recurrence = EventRecurrence.from_dict(self.recurrence)
    
    def add_attendee(self, attendee: Attendee) -> None:
        """Add an attendee"""
        # Check if attendee already exists
        for existing in self.attendees:
            if existing.person_id == attendee.person_id:
                return
        self.attendees.append(attendee)
    
    def remove_attendee(self, person_id: str) -> bool:
        """Remove an attendee"""
        for i, attendee in enumerate(self.attendees):
            if attendee.person_id == person_id:
                self.attendees.pop(i)
                return True
        return False
    
    def get_attendee(self, person_id: str) -> Optional[Attendee]:
        """Get an attendee by person ID"""
        for attendee in self.attendees:
            if attendee.person_id == person_id:
                return attendee
        return None
    
    def set_attendee_rsvp(self, person_id: str, status: RSVPStatus) -> bool:
        """Set RSVP status for an attendee"""
        attendee = self.get_attendee(person_id)
        if attendee:
            attendee.rsvp_status = status
            attendee.rsvp_updated_at = datetime.now(timezone.utc).isoformat()
            return True
        return False
    
    def add_external_id(self, system: str, external_id: str) -> None:
        """Add an external system ID"""
        self.external_ids[system] = external_id
    
    def get_external_id(self, system: str) -> Optional[str]:
        """Get external ID for a system"""
        return self.external_ids.get(system)
    
    def add_required_attendee(self, person_id: str) -> None:
        """Add a required attendee"""
        if person_id not in self.required_attendees:
            self.required_attendees.append(person_id)
    
    def add_optional_attendee(self, person_id: str) -> None:
        """Add an optional attendee"""
        if person_id not in self.optional_attendees:
            self.optional_attendees.append(person_id)
    
    def link_project(self, project_id: str) -> None:
        """Link a project"""
        if project_id not in self.related_projects:
            self.related_projects.append(project_id)
    
    def link_task(self, task_id: str) -> None:
        """Link a task"""
        if task_id not in self.related_tasks:
            self.related_tasks.append(task_id)
    
    def link_issue(self, issue_id: str) -> None:
        """Link an issue"""
        if issue_id not in self.related_issues:
            self.related_issues.append(issue_id)
    
    def link_document(self, document_id: str) -> None:
        """Link a document"""
        if document_id not in self.related_documents:
            self.related_documents.append(document_id)
    
    def add_reminder(self, minutes_before: int) -> None:
        """Add a reminder"""
        if minutes_before not in self.reminders:
            self.reminders.append(minutes_before)
    
    def set_status(self, status: EventStatus) -> None:
        """Set event status"""
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_recurrence(self, recurrence: EventRecurrence) -> None:
        """Set event recurrence"""
        self.recurrence = recurrence
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field"""
        self.custom_fields[key] = value
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field"""
        return self.custom_fields.get(key, default)
    
    def is_scheduled(self) -> bool:
        """Check if event is scheduled"""
        return self.status == EventStatus.SCHEDULED
    
    def is_cancelled(self) -> bool:
        """Check if event is cancelled"""
        return self.status == EventStatus.CANCELLED
    
    def is_recurring(self) -> bool:
        """Check if event is recurring"""
        return self.recurrence is not None and self.recurrence.type != "none"
    
    def get_duration_minutes(self) -> Optional[int]:
        """Get event duration in minutes"""
        if self.start_time and self.end_time:
            from datetime import datetime as dt
            start = dt.fromisoformat(self.start_time)
            end = dt.fromisoformat(self.end_time)
            duration = (end - start).total_seconds() / 60
            return int(duration)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        result.update({
            "event_type": self.event_type.value,
            "status": self.status.value,
            "visibility": self.visibility.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "time_zone": self.time_zone,
            "location": self.location,
            "agenda": self.agenda,
            "organizer_id": self.organizer_id,
            "attendees": [a.to_dict() for a in self.attendees],
            "required_attendees": self.required_attendees,
            "optional_attendees": self.optional_attendees,
            "recurrence": self.recurrence.to_dict() if self.recurrence else None,
            "parent_event_id": self.parent_event_id,
            "related_projects": self.related_projects,
            "related_tasks": self.related_tasks,
            "related_issues": self.related_issues,
            "related_documents": self.related_documents,
            "calendar_id": self.calendar_id,
            "meeting_link": self.meeting_link,
            "reminders": self.reminders,
            "external_ids": self.external_ids,
            "custom_fields": self.custom_fields
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create from dictionary"""
        uaw_id = data.get("uaw_id")
        if isinstance(uaw_id, str):
            uaw_id = UAWIdentifier.from_string(uaw_id)
        
        # Parse attendees
        attendees = []
        for a_data in data.get("attendees", []):
            attendees.append(Attendee.from_dict(a_data))
        
        # Parse recurrence
        recurrence = None
        if data.get("recurrence"):
            recurrence = EventRecurrence.from_dict(data["recurrence"])
        
        return cls(
            uaw_id=uaw_id,
            name=data.get("name", ""),
            description=data.get("description"),
            event_type=EventType(data.get("event_type", "meeting")),
            status=EventStatus(data.get("status", "scheduled")),
            visibility=EventVisibility(data.get("visibility", "private")),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            time_zone=data.get("time_zone", "UTC"),
            location=data.get("location"),
            agenda=data.get("agenda"),
            organizer_id=data.get("organizer_id"),
            attendees=attendees,
            required_attendees=data.get("required_attendees", []),
            optional_attendees=data.get("optional_attendees", []),
            recurrence=recurrence,
            parent_event_id=data.get("parent_event_id"),
            related_projects=data.get("related_projects", []),
            related_tasks=data.get("related_tasks", []),
            related_issues=data.get("related_issues", []),
            related_documents=data.get("related_documents", []),
            calendar_id=data.get("calendar_id"),
            meeting_link=data.get("meeting_link"),
            reminders=data.get("reminders", []),
            external_ids=data.get("external_ids", {}),
            custom_fields=data.get("custom_fields", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            is_active=data.get("is_active", True)
        )
    
    def get_google_calendar_event_id(self) -> Optional[str]:
        """Get Google Calendar event ID if available"""
        return self.external_ids.get("google_calendar")
    
    def get_outlook_event_id(self) -> Optional[str]:
        """Get Outlook event ID if available"""
        return self.external_ids.get("outlook")
    
    def get_calendly_event_id(self) -> Optional[str]:
        """Get Calendly event ID if available"""
        return self.external_ids.get("calendly")
    
    def get_teams_meeting_id(self) -> Optional[str]:
        """Get Microsoft Teams meeting ID if available"""
        return self.external_ids.get("teams")


@dataclass
class EventBuilder:
    """Builder for creating Event instances"""
    
    name: str
    start_time: str
    end_time: str
    event_type: EventType = EventType.MEETING
    
    def with_description(self, description: str) -> "EventBuilder":
        """Set description"""
        self._description = description
        return self
    
    def with_location(self, location: str) -> "EventBuilder":
        """Set location"""
        self._location = location
        return self
    
    def with_timezone(self, time_zone: str) -> "EventBuilder":
        """Set timezone"""
        self._time_zone = time_zone
        return self
    
    def with_organizer(self, organizer_id: str) -> "EventBuilder":
        """Set organizer"""
        self._organizer_id = organizer_id
        return self
    
    def with_attendee(
        self,
        person_id: str,
        person_name: Optional[str] = None,
        person_email: Optional[str] = None
    ) -> "EventBuilder":
        """Add attendee"""
        self._attendees = getattr(self, "_attendees", [])
        self._attendees.append(Attendee(
            person_id=person_id,
            person_name=person_name,
            person_email=person_email
        ))
        return self
    
    def with_meeting_link(self, meeting_link: str) -> "EventBuilder":
        """Set meeting link"""
        self._meeting_link = meeting_link
        return self
    
    def with_external_id(self, system: str, external_id: str) -> "EventBuilder":
        """Add external ID"""
        self._external_ids = getattr(self, "_external_ids", {})
        self._external_ids[system] = external_id
        return self
    
    def build(self) -> Event:
        """Build Event instance"""
        return Event(
            uaw_id=Event.generate_id(),
            name=self.name,
            description=getattr(self, "_description", None),
            event_type=self.event_type,
            start_time=self.start_time,
            end_time=self.end_time,
            time_zone=getattr(self, "_time_zone", "UTC"),
            location=getattr(self, "_location", None),
            organizer_id=getattr(self, "_organizer_id", None),
            attendees=getattr(self, "_attendees", []),
            meeting_link=getattr(self, "_meeting_link", None),
            external_ids=getattr(self, "_external_ids", {})
        )
