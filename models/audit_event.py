"""
AuditEvent Model for UAW
Модель журнала операций, изменений и результатов
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

from .base import BaseModel, EntityType, UAWIdentifier


class AuditEventType(Enum):
    """Type of audit event"""
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"
    
    # Integration events
    INTEGRATION_CONNECTED = "integration_connected"
    INTEGRATION_DISCONNECTED = "integration_disconnected"
    INTEGRATION_ERROR = "integration_error"
    INTEGRATION_RATE_LIMIT = "integration_rate_limit"
    
    # Resource events
    RESOURCE_CREATED = "resource_created"
    RESOURCE_UPDATED = "resource_updated"
    RESOURCE_DELETED = "resource_deleted"
    RESOURCE_READ = "resource_read"
    
    # Workflow events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_PAUSED = "workflow_paused"
    WORKFLOW_RESUMED = "workflow_resumed"
    
    # Task events
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # Approval events
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    APPROVAL_EXPIRED = "approval_expired"
    
    # Security events
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILURE = "authentication_failure"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    
    # External service events
    EXTERNAL_API_CALL = "external_api_call"
    EXTERNAL_API_SUCCESS = "external_api_success"
    EXTERNAL_API_FAILURE = "external_api_failure"
    WEBHOOK_RECEIVED = "webhook_received"
    WEBHOOK_PROCESSED = "webhook_processed"


class AuditEventSeverity(Enum):
    """Severity of audit event"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEventStatus(Enum):
    """Status of audit event"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AuditEvent(BaseModel):
    """
    AuditEvent model representing a journal entry for operations, changes, and results.
    
    Attributes:
        uaw_id: Unique UAW identifier
        event_type: Type of audit event
        severity: Event severity
        status: Event status
        timestamp: When event occurred
        title: Event title
        message: Event message
        details: Additional event details
        actor_id: UAW ID of person/system who caused the event
        actor_name: Name of actor
        resource_type: Type of resource affected
        resource_id: UAW ID of resource affected
        old_value: Previous value (for updates)
        new_value: New value (for updates)
        metadata: Additional metadata
        tags: Event tags
        related_events: List of related event IDs
        external_ids: IDs in external systems
        custom_fields: Custom audit event fields
    """
    
    entity_type: ClassVar[EntityType] = EntityType.AUDIT_EVENT
    
    event_type: AuditEventType
    severity: AuditEventSeverity = AuditEventSeverity.INFO
    status: AuditEventStatus = AuditEventStatus.COMPLETED
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    title: Optional[str] = None
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    
    old_value: Any = None
    new_value: Any = None
    
    related_events: List[str] = field(default_factory=list)
    
    # External system IDs
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.related_events, str):
            self.related_events = [self.related_events]
    
    def add_detail(self, key: str, value: Any) -> None:
        """Add a detail"""
        self.details[key] = value
    
    def add_related_event(self, event_id: str) -> None:
        """Add a related event"""
        if event_id not in self.related_events:
            self.related_events.append(event_id)
    
    def add_external_id(self, system: str, external_id: str) -> None:
        """Add an external system ID"""
        self.external_ids[system] = external_id
    
    def get_external_id(self, system: str) -> Optional[str]:
        """Get external ID for a system"""
        return self.external_ids.get(system)
    
    def set_status(self, status: AuditEventStatus) -> None:
        """Set event status"""
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field"""
        self.custom_fields[key] = value
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field"""
        return self.custom_fields.get(key, default)
    
    def is_error(self) -> bool:
        """Check if this is an error event"""
        return self.severity in [AuditEventSeverity.ERROR, AuditEventSeverity.CRITICAL]
    
    def is_completed(self) -> bool:
        """Check if event is completed"""
        return self.status == AuditEventStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if event failed"""
        return self.status == AuditEventStatus.FAILED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        result.update({
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "related_events": self.related_events,
            "external_ids": self.external_ids,
            "custom_fields": self.custom_fields
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """Create from dictionary"""
        uaw_id = data.get("uaw_id")
        if isinstance(uaw_id, str):
            uaw_id = UAWIdentifier.from_string(uaw_id)
        
        return cls(
            uaw_id=uaw_id,
            name=data.get("name", ""),
            description=data.get("description"),
            event_type=AuditEventType(data.get("event_type", "info")),
            severity=AuditEventSeverity(data.get("severity", "info")),
            status=AuditEventStatus(data.get("status", "completed")),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            title=data.get("title"),
            message=data.get("message"),
            details=data.get("details", {}),
            actor_id=data.get("actor_id"),
            actor_name=data.get("actor_name"),
            resource_type=data.get("resource_type"),
            resource_id=data.get("resource_id"),
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            related_events=data.get("related_events", []),
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


@dataclass
class AuditEventBuilder:
    """Builder for creating AuditEvent instances"""
    
    event_type: AuditEventType
    message: str
    
    def with_title(self, title: str) -> "AuditEventBuilder":
        """Set title"""
        self._name = title
        self._title = title
        return self
    
    def with_severity(self, severity: AuditEventSeverity) -> "AuditEventBuilder":
        """Set severity"""
        self._severity = severity
        return self
    
    def with_actor(self, actor_id: str, actor_name: Optional[str] = None) -> "AuditEventBuilder":
        """Set actor"""
        self._actor_id = actor_id
        self._actor_name = actor_name
        return self
    
    def with_resource(self, resource_type: str, resource_id: str) -> "AuditEventBuilder":
        """Set affected resource"""
        self._resource_type = resource_type
        self._resource_id = resource_id
        return self
    
    def with_detail(self, key: str, value: Any) -> "AuditEventBuilder":
        """Add detail"""
        self._details = getattr(self, "_details", {})
        self._details[key] = value
        return self
    
    def with_external_id(self, system: str, external_id: str) -> "AuditEventBuilder":
        """Add external ID"""
        self._external_ids = getattr(self, "_external_ids", {})
        self._external_ids[system] = external_id
        return self
    
    def build(self) -> AuditEvent:
        """Build AuditEvent instance"""
        return AuditEvent(
            uaw_id=AuditEvent.generate_id(),
            name=getattr(self, "_name", self.event_type.value),
            description=getattr(self, "_title", self.message),
            event_type=self.event_type,
            severity=getattr(self, "_severity", AuditEventSeverity.INFO),
            message=self.message,
            title=getattr(self, "_title", None),
            details=getattr(self, "_details", {}),
            actor_id=getattr(self, "_actor_id", None),
            actor_name=getattr(self, "_actor_name", None),
            resource_type=getattr(self, "_resource_type", None),
            resource_id=getattr(self, "_resource_id", None),
            external_ids=getattr(self, "_external_ids", {})
        )


# Convenience functions for creating common audit events
def create_resource_created_event(
    resource_type: str,
    resource_id: str,
    actor_id: Optional[str] = None,
    actor_name: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditEvent:
    """Create a resource created audit event"""
    return AuditEvent(
        uaw_id=AuditEvent.generate_id(),
        name=f"{resource_type}_created",
        description=f"Resource {resource_type} with ID {resource_id} was created",
        event_type=AuditEventType.RESOURCE_CREATED,
        severity=AuditEventSeverity.INFO,
        actor_id=actor_id,
        actor_name=actor_name,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        status=AuditEventStatus.COMPLETED
    )


def create_resource_updated_event(
    resource_type: str,
    resource_id: str,
    actor_id: Optional[str] = None,
    actor_name: Optional[str] = None,
    old_value: Any = None,
    new_value: Any = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditEvent:
    """Create a resource updated audit event"""
    return AuditEvent(
        uaw_id=AuditEvent.generate_id(),
        name=f"{resource_type}_updated",
        description=f"Resource {resource_type} with ID {resource_id} was updated",
        event_type=AuditEventType.RESOURCE_UPDATED,
        severity=AuditEventSeverity.INFO,
        actor_id=actor_id,
        actor_name=actor_name,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
        details=details or {},
        status=AuditEventStatus.COMPLETED
    )


def create_integration_error_event(
    integration_name: str,
    error: str,
    actor_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditEvent:
    """Create an integration error audit event"""
    return AuditEvent(
        uaw_id=AuditEvent.generate_id(),
        name=f"{integration_name}_error",
        description=f"Integration {integration_name} encountered an error",
        event_type=AuditEventType.INTEGRATION_ERROR,
        severity=AuditEventSeverity.ERROR,
        message=error,
        actor_id=actor_id,
        details=details or {"error": error},
        status=AuditEventStatus.COMPLETED
    )


def create_workflow_event(
    workflow_id: str,
    event_type: AuditEventType,
    actor_id: Optional[str] = None,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditEvent:
    """Create a workflow audit event"""
    return AuditEvent(
        uaw_id=AuditEvent.generate_id(),
        name=f"workflow_{event_type.value}",
        description=f"Workflow {workflow_id}: {event_type.value}",
        event_type=event_type,
        severity=AuditEventSeverity.INFO,
        message=message,
        actor_id=actor_id,
        resource_type="workflow",
        resource_id=workflow_id,
        details=details or {},
        status=AuditEventStatus.COMPLETED
    )
