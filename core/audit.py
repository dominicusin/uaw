"""
Audit Logger for UAW
Журналирование всех операций и событий для аудита
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class AuditEventType(Enum):
    """Types of audit events"""
    # System events
    SYSTEM_START = "system_start"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"
    
    # Request events
    REQUEST = "request"
    PARSE = "parse"
    PLAN = "plan"
    
    # Workflow events
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_FAIL = "workflow_fail"
    WORKFLOW_CANCEL = "workflow_cancel"
    WORKFLOW_RESUME = "workflow_resume"
    
    # Step events
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    STEP_FAIL = "step_fail"
    STEP_RETRY = "step_retry"
    
    # Integration events
    INTEGRATION_CALL = "integration_call"
    INTEGRATION_SUCCESS = "integration_success"
    INTEGRATION_ERROR = "integration_error"
    
    # Resource events
    RESOURCE_CREATE = "resource_create"
    RESOURCE_UPDATE = "resource_update"
    RESOURCE_DELETE = "resource_delete"
    RESOURCE_LINK = "resource_link"
    
    # Security events
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    
    # Error events
    ERROR = "error"
    WARNING = "warning"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Single audit event record"""
    event_id: str
    timestamp: str
    event_type: AuditEventType
    action: str
    severity: AuditSeverity = AuditSeverity.INFO
    user_id: Optional[str] = None
    workflow_id: Optional[str] = None
    step_id: Optional[str] = None
    integration: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    status: str = "success"
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "action": self.action,
            "severity": self.severity.value,
            "user_id": self.user_id,
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "integration": self.integration,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "status": self.status,
            "details": self.details,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        return cls(
            event_id=data["event_id"],
            timestamp=data["timestamp"],
            event_type=AuditEventType(data["event_type"]),
            action=data["action"],
            severity=AuditSeverity(data.get("severity", "info")),
            user_id=data.get("user_id"),
            workflow_id=data.get("workflow_id"),
            step_id=data.get("step_id"),
            integration=data.get("integration"),
            resource_id=data.get("resource_id"),
            resource_type=data.get("resource_type"),
            status=data.get("status", "success"),
            details=data.get("details", {}),
            metadata=data.get("metadata", {})
        )


class AuditLogger:
    """
    Centralized audit logger for UAW system.
    Logs all operations, errors, and significant events.
    """
    
    def __init__(
        self,
        log_dir: Union[str, Path] = "/workspace/uaw/logs",
        max_log_size: int = 10000,
        max_log_files: int = 5
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_log_size = max_log_size
        self.max_log_files = max_log_files
        
        # In-memory buffer
        self._buffer: List[AuditEvent] = []
        self._buffer_size = 0
        self._max_buffer_size = 100
        
        # Initialize
        self._rotate_logs()
    
    def _rotate_logs(self):
        """Rotate log files to prevent excessive disk usage"""
        log_files = sorted(self.log_dir.glob("audit_*.json"), reverse=True)
        
        # Keep only max_log_files
        for log_file in log_files[self.max_log_files:]:
            try:
                log_file.unlink()
            except Exception:
                pass
    
    def _get_log_path(self) -> Path:
        """Get current log file path"""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        return self.log_dir / f"audit_{date_str}.json"
    
    def _write_to_disk(self):
        """Write buffer to disk"""
        if not self._buffer:
            return
        
        log_path = self._get_log_path()
        
        # Check if file exists and needs rotation
        if log_path.exists():
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                    if len(existing) >= self.max_log_size:
                        # Rotate file
                        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                        rotated_path = self.log_dir / f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{timestamp}.json"
                        log_path.rename(rotated_path)
                        existing = []
            except Exception:
                existing = []
        else:
            existing = []
        
        # Append new events
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                for event in self._buffer:
                    # Check file size
                    f.seek(0, 2)  # End of file
                    if f.tell() > self.max_log_size * 1024:  # ~10MB
                        f.close()
                        self._rotate_logs()
                        log_path = self._get_log_path()
                        f = open(log_path, 'a', encoding='utf-8')
                    
                    json.dump(event.to_dict(), f, ensure_ascii=False)
                    f.write("\n")
        except Exception as e:
            print(f"Warning: Failed to write audit log: {e}")
        
        # Clear buffer
        self._buffer = []
        self._buffer_size = 0
    
    def log(
        self,
        event_type: Union[AuditEventType, str],
        action: str,
        details: Optional[Dict[str, Any]] = None,
        severity: Union[AuditSeverity, str] = AuditSeverity.INFO,
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        step_id: Optional[str] = None,
        integration: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            action: Action being performed
            details: Additional details
            severity: Event severity
            user_id: User ID if applicable
            workflow_id: Workflow ID if applicable
            step_id: Step ID if applicable
            integration: Integration name if applicable
            resource_id: Resource ID if applicable
            resource_type: Resource type if applicable
            status: Status of the operation
            metadata: Additional metadata
            
        Returns:
            Created AuditEvent
        """
        # Convert string types to enums
        if isinstance(event_type, str):
            try:
                event_type = AuditEventType(event_type)
            except ValueError:
                event_type = AuditEventType.SYSTEM_ERROR
        
        if isinstance(severity, str):
            try:
                severity = AuditSeverity(severity)
            except ValueError:
                severity = AuditSeverity.INFO
        
        # Create event
        event = AuditEvent(
            event_id=f"{event_type.value}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            action=action,
            severity=severity,
            user_id=user_id,
            workflow_id=workflow_id,
            step_id=step_id,
            integration=integration,
            resource_id=resource_id,
            resource_type=resource_type,
            status=status,
            details=details or {},
            metadata=metadata or {}
        )
        
        # Add to buffer
        self._buffer.append(event)
        self._buffer_size += 1
        
        # Flush buffer if full
        if self._buffer_size >= self._max_buffer_size:
            self._write_to_disk()
        
        return event
    
    def log_request(
        self,
        action: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Log a user request"""
        return self.log(
            AuditEventType.REQUEST,
            action,
            details=details,
            user_id=user_id
        )
    
    def log_workflow_start(
        self,
        workflow_id: str,
        name: str,
        user_id: Optional[str] = None
    ) -> AuditEvent:
        """Log workflow start"""
        return self.log(
            AuditEventType.WORKFLOW_START,
            "workflow_start",
            details={"name": name},
            workflow_id=workflow_id,
            user_id=user_id
        )
    
    def log_workflow_complete(
        self,
        workflow_id: str,
        duration: Optional[float] = None
    ) -> AuditEvent:
        """Log workflow completion"""
        return self.log(
            AuditEventType.WORKFLOW_COMPLETE,
            "workflow_complete",
            details={"duration": duration},
            workflow_id=workflow_id,
            severity=AuditSeverity.INFO
        )
    
    def log_workflow_error(
        self,
        workflow_id: str,
        error: str,
        step_id: Optional[str] = None
    ) -> AuditEvent:
        """Log workflow error"""
        return self.log(
            AuditEventType.WORKFLOW_FAIL,
            "workflow_error",
            details={"error": error},
            workflow_id=workflow_id,
            step_id=step_id,
            severity=AuditSeverity.ERROR
        )
    
    def log_step(
        self,
        workflow_id: str,
        step_id: str,
        step_name: str,
        status: str,
        duration: Optional[float] = None
    ) -> AuditEvent:
        """Log a workflow step"""
        event_type = (
            AuditEventType.STEP_COMPLETE if status == "success" 
            else AuditEventType.STEP_FAIL
        )
        return self.log(
            event_type,
            f"step_{status}",
            details={"step_name": step_name, "duration": duration},
            workflow_id=workflow_id,
            step_id=step_id,
            severity=AuditSeverity.DEBUG
        )
    
    def log_integration(
        self,
        integration: str,
        operation: str,
        status: str,
        duration: Optional[float] = None,
        error: Optional[str] = None
    ) -> AuditEvent:
        """Log integration call"""
        event_type = (
            AuditEventType.INTEGRATION_SUCCESS if status == "success"
            else AuditEventType.INTEGRATION_ERROR
        )
        return self.log(
            event_type,
            operation,
            details={"status": status, "duration": duration, "error": error},
            integration=integration,
            severity=AuditSeverity.INFO if status == "success" else AuditSeverity.WARNING
        )
    
    def log_error(
        self,
        error: str,
        context: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.ERROR
    ) -> AuditEvent:
        """Log an error"""
        return self.log(
            AuditEventType.ERROR,
            "error",
            details={"error": error, "context": context},
            severity=severity
        )
    
    def log_security(
        self,
        event_type: str,
        action: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str = "success"
    ) -> AuditEvent:
        """Log a security event"""
        return self.log(
            AuditEventType(event_type),
            action,
            details={"status": status},
            user_id=user_id,
            resource_id=resource_id,
            severity=AuditSeverity.INFO if status == "success" else AuditSeverity.WARNING
        )
    
    def flush(self):
        """Flush buffer to disk"""
        self._write_to_disk()
    
    def get_events(
        self,
        limit: int = 100,
        event_type: Optional[Union[AuditEventType, str]] = None,
        severity: Optional[Union[AuditSeverity, str]] = None,
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> List[AuditEvent]:
        """
        Get audit events with optional filtering.
        
        Note: This reads from disk and may be slow for large logs.
        """
        events = []
        
        # Read all log files
        log_files = sorted(self.log_dir.glob("audit_*.json"), reverse=True)
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            data = json.loads(line)
                            event = AuditEvent.from_dict(data)
                            
                            # Apply filters
                            if event_type:
                                if isinstance(event_type, str):
                                    if event.event_type.value != event_type:
                                        continue
                                else:
                                    if event.event_type != event_type:
                                        continue
                            
                            if severity:
                                if isinstance(severity, str):
                                    if event.severity.value != severity:
                                        continue
                                else:
                                    if event.severity != severity:
                                        continue
                            
                            if user_id and event.user_id != user_id:
                                continue
                            
                            if workflow_id and event.workflow_id != workflow_id:
                                continue
                            
                            if since:
                                if event.timestamp < since:
                                    continue
                            
                            if until:
                                if event.timestamp > until:
                                    continue
                            
                            events.append(event)
                            
                            if len(events) >= limit:
                                return events
                            
                        except json.JSONDecodeError:
                            continue
            except Exception:
                continue
        
        return events
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit log statistics"""
        events = self.get_events(limit=1000)
        
        return {
            "total_events": len(events),
            "by_type": {
                event_type.value: len([
                    e for e in events if e.event_type == event_type
                ]) for event_type in AuditEventType
            },
            "by_severity": {
                severity.value: len([
                    e for e in events if e.severity == severity
                ]) for severity in AuditSeverity
            },
            "by_integration": {
                integration: len([
                    e for e in events if e.integration == integration
                ]) for integration in set(
                    e.integration for e in events if e.integration
                )
            }
        }
    
    def clear(self, days: Optional[int] = None) -> int:
        """
        Clear audit logs.
        
        Args:
            days: If specified, only clear logs older than this many days
            
        Returns:
            Number of log files deleted
        """
        deleted = 0
        
        if days is None:
            # Clear all
            for log_file in self.log_dir.glob("audit_*.json"):
                try:
                    log_file.unlink()
                    deleted += 1
                except Exception:
                    pass
        else:
            # Clear old logs
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            for log_file in self.log_dir.glob("audit_*.json"):
                try:
                    # Extract date from filename
                    date_str = log_file.stem.split("_")[1]
                    file_date = datetime.strptime(date_str, "%Y%m%d").date()
                    
                    if file_date < cutoff.date():
                        log_file.unlink()
                        deleted += 1
                except Exception:
                    pass
        
        return deleted
