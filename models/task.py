"""
Task Model for UAW
Модель задачи/подзадачи
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

from .base import BaseModel, EntityType, UAWIdentifier


class TaskStatus(Enum):
    """Status of a task"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    IN_REVIEW = "in_review"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Priority of a task"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Task(BaseModel):
    """
    Task model representing a task, subtask, or work item.
    
    Attributes:
        uaw_id: Unique UAW identifier
        name: Task name/title
        description: Task description
        status: Current task status
        priority: Task priority
        project_id: UAW ID of parent project
        assignee_id: UAW ID of assigned person
        team_id: UAW ID of team
        parent_task_id: UAW ID of parent task (for subtasks)
        subtasks: List of subtask UAW IDs
        due_date: Task due date
        start_date: Task start date
        completed_at: When task was completed
        estimated_hours: Estimated hours to complete
        actual_hours: Actual hours spent
        dependencies: List of task IDs this task depends on
        external_ids: IDs in external systems
        checklist: List of checklist items
        attachments: List of attachment references
        custom_fields: Custom task fields
    """
    
    entity_type: ClassVar[EntityType] = EntityType.TASK
    
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    
    project_id: Optional[str] = None
    assignee_id: Optional[str] = None
    team_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    subtasks: List[str] = field(default_factory=list)
    
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    completed_at: Optional[str] = None
    
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    
    # External system IDs
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    # Checklist
    checklist: List[Dict[str, Any]] = field(default_factory=list)
    
    # Attachments
    attachments: List[str] = field(default_factory=list)
    
    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.subtasks, str):
            self.subtasks = [self.subtasks]
        if isinstance(self.dependencies, str):
            self.dependencies = [self.dependencies]
        if isinstance(self.attachments, str):
            self.attachments = [self.attachments]
    
    def add_subtask(self, task_id: str) -> None:
        """Add a subtask"""
        if task_id not in self.subtasks:
            self.subtasks.append(task_id)
    
    def remove_subtask(self, task_id: str) -> bool:
        """Remove a subtask"""
        if task_id in self.subtasks:
            self.subtasks.remove(task_id)
            return True
        return False
    
    def add_dependency(self, task_id: str) -> None:
        """Add a task dependency"""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)
    
    def remove_dependency(self, task_id: str) -> bool:
        """Remove a task dependency"""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)
            return True
        return False
    
    def add_external_id(self, system: str, external_id: str) -> None:
        """Add an external system ID"""
        self.external_ids[system] = external_id
    
    def get_external_id(self, system: str) -> Optional[str]:
        """Get external ID for a system"""
        return self.external_ids.get(system)
    
    def add_checklist_item(self, title: str, completed: bool = False) -> None:
        """Add a checklist item"""
        self.checklist.append({
            "title": title,
            "completed": completed,
            "completed_at": None
        })
    
    def complete_checklist_item(self, index: int) -> bool:
        """Mark a checklist item as completed"""
        if 0 <= index < len(self.checklist):
            self.checklist[index]["completed"] = True
            self.checklist[index]["completed_at"] = datetime.now(timezone.utc).isoformat()
            return True
        return False
    
    def add_attachment(self, attachment_id: str) -> None:
        """Add an attachment"""
        if attachment_id not in self.attachments:
            self.attachments.append(attachment_id)
    
    def set_status(self, status: TaskStatus) -> None:
        """Set task status"""
        self.status = status
        if status == TaskStatus.DONE:
            self.completed_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_priority(self, priority: TaskPriority) -> None:
        """Set task priority"""
        self.priority = priority
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_assignee(self, person_id: str) -> None:
        """Assign task to a person"""
        self.assignee_id = person_id
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field"""
        self.custom_fields[key] = value
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field"""
        return self.custom_fields.get(key, default)
    
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.status == TaskStatus.DONE
    
    def is_in_progress(self) -> bool:
        """Check if task is in progress"""
        return self.status == TaskStatus.IN_PROGRESS
    
    def is_blocked(self) -> bool:
        """Check if task is blocked"""
        return self.status == TaskStatus.BLOCKED
    
    def has_dependencies(self) -> bool:
        """Check if task has dependencies"""
        return len(self.dependencies) > 0
    
    def dependencies_completed(self, completed_task_ids: List[str]) -> bool:
        """Check if all dependencies are completed"""
        return all(dep in completed_task_ids for dep in self.dependencies)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        result.update({
            "status": self.status.value,
            "priority": self.priority.value,
            "project_id": self.project_id,
            "assignee_id": self.assignee_id,
            "team_id": self.team_id,
            "parent_task_id": self.parent_task_id,
            "subtasks": self.subtasks,
            "due_date": self.due_date,
            "start_date": self.start_date,
            "completed_at": self.completed_at,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "dependencies": self.dependencies,
            "external_ids": self.external_ids,
            "checklist": self.checklist,
            "attachments": self.attachments,
            "custom_fields": self.custom_fields
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create from dictionary"""
        uaw_id = data.get("uaw_id")
        if isinstance(uaw_id, str):
            uaw_id = UAWIdentifier.from_string(uaw_id)
        
        return cls(
            uaw_id=uaw_id,
            name=data.get("name", ""),
            description=data.get("description"),
            status=TaskStatus(data.get("status", "todo")),
            priority=TaskPriority(data.get("priority", "medium")),
            project_id=data.get("project_id"),
            assignee_id=data.get("assignee_id"),
            team_id=data.get("team_id"),
            parent_task_id=data.get("parent_task_id"),
            subtasks=data.get("subtasks", []),
            due_date=data.get("due_date"),
            start_date=data.get("start_date"),
            completed_at=data.get("completed_at"),
            estimated_hours=data.get("estimated_hours"),
            actual_hours=data.get("actual_hours"),
            dependencies=data.get("dependencies", []),
            external_ids=data.get("external_ids", {}),
            checklist=data.get("checklist", []),
            attachments=data.get("attachments", []),
            custom_fields=data.get("custom_fields", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            is_active=data.get("is_active", True)
        )
    
    def get_asana_task_id(self) -> Optional[str]:
        """Get Asana task GID if available"""
        return self.external_ids.get("asana")
    
    def get_linear_issue_id(self) -> Optional[str]:
        """Get Linear issue ID if available"""
        return self.external_ids.get("linear")
    
    def get_github_issue_number(self) -> Optional[str]:
        """Get GitHub issue number if available"""
        return self.external_ids.get("github")


@dataclass
class TaskBuilder:
    """Builder for creating Task instances"""
    
    name: str
    
    def with_description(self, description: str) -> "TaskBuilder":
        """Set description"""
        self._description = description
        return self
    
    def with_status(self, status: TaskStatus) -> "TaskBuilder":
        """Set status"""
        self._status = status
        return self
    
    def with_priority(self, priority: TaskPriority) -> "TaskBuilder":
        """Set priority"""
        self._priority = priority
        return self
    
    def with_project(self, project_id: str) -> "TaskBuilder":
        """Set parent project"""
        self._project_id = project_id
        return self
    
    def with_assignee(self, person_id: str) -> "TaskBuilder":
        """Set assignee"""
        self._assignee_id = person_id
        return self
    
    def with_team(self, team_id: str) -> "TaskBuilder":
        """Set team"""
        self._team_id = team_id
        return self
    
    def with_parent(self, parent_task_id: str) -> "TaskBuilder":
        """Set parent task"""
        self._parent_task_id = parent_task_id
        return self
    
    def with_dates(
        self,
        due_date: Optional[str] = None,
        start_date: Optional[str] = None
    ) -> "TaskBuilder":
        """Set dates"""
        self._due_date = due_date
        self._start_date = start_date
        return self
    
    def with_dependency(self, task_id: str) -> "TaskBuilder":
        """Add dependency"""
        self._dependencies = getattr(self, "_dependencies", [])
        if task_id not in self._dependencies:
            self._dependencies.append(task_id)
        return self
    
    def with_external_id(self, system: str, external_id: str) -> "TaskBuilder":
        """Add external ID"""
        self._external_ids = getattr(self, "_external_ids", {})
        self._external_ids[system] = external_id
        return self
    
    def build(self) -> Task:
        """Build Task instance"""
        return Task(
            uaw_id=Task.generate_id(),
            name=self.name,
            description=getattr(self, "_description", None),
            status=getattr(self, "_status", TaskStatus.TODO),
            priority=getattr(self, "_priority", TaskPriority.MEDIUM),
            project_id=getattr(self, "_project_id", None),
            assignee_id=getattr(self, "_assignee_id", None),
            team_id=getattr(self, "_team_id", None),
            parent_task_id=getattr(self, "_parent_task_id", None),
            due_date=getattr(self, "_due_date", None),
            start_date=getattr(self, "_start_date", None),
            dependencies=getattr(self, "_dependencies", []),
            external_ids=getattr(self, "_external_ids", {})
        )
