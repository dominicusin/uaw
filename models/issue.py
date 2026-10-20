"""
Issue Model for UAW
Модель дефекта, запроса на изменение или технической проблемы
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

from .base import BaseModel, EntityType, UAWIdentifier


class IssueStatus(Enum):
    """Status of an issue"""
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    TESTING = "testing"
    DONE = "done"
    CANCELLED = "cancelled"


class IssueType(Enum):
    """Type of issue"""
    BUG = "bug"
    FEATURE = "feature"
    TASK = "task"
    ENHANCEMENT = "enhancement"
    DOCUMENTATION = "documentation"
    QUESTION = "question"
    SECURITY = "security"


class IssueSeverity(Enum):
    """Severity of an issue"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Issue(BaseModel):
    """
    Issue model representing a defect, feature request, or technical problem.
    
    Attributes:
        uaw_id: Unique UAW identifier
        title: Issue title
        description: Issue description
        issue_type: Type of issue (bug, feature, etc.)
        status: Current issue status
        severity: Issue severity
        repository_id: UAW ID of related repository
        project_id: UAW ID of related project
        assignee_id: UAW ID of assigned person
        reporter_id: UAW ID of person who reported the issue
        labels: List of labels/tags
        milestone_id: UAW ID of milestone
        related_issues: List of related issue IDs
        linked_tasks: List of linked task IDs
        linked_prs: List of linked pull request IDs
        linked_deployments: List of linked deployment IDs
        due_date: Issue due date
        closed_at: When issue was closed
        resolved_at: When issue was resolved
        external_ids: IDs in external systems
        comments: List of comment references
        custom_fields: Custom issue fields
    """
    
    entity_type: ClassVar[EntityType] = EntityType.ISSUE
    
    issue_type: IssueType = IssueType.TASK
    status: IssueStatus = IssueStatus.BACKLOG
    severity: IssueSeverity = IssueSeverity.MEDIUM
    
    repository_id: Optional[str] = None
    project_id: Optional[str] = None
    assignee_id: Optional[str] = None
    reporter_id: Optional[str] = None
    
    labels: List[str] = field(default_factory=list)
    milestone_id: Optional[str] = None
    
    # Related entities
    related_issues: List[str] = field(default_factory=list)
    linked_tasks: List[str] = field(default_factory=list)
    linked_prs: List[str] = field(default_factory=list)
    linked_deployments: List[str] = field(default_factory=list)
    
    due_date: Optional[str] = None
    closed_at: Optional[str] = None
    resolved_at: Optional[str] = None
    
    # External system IDs
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    # Comments
    comments: List[str] = field(default_factory=list)
    
    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.labels, str):
            self.labels = [self.labels]
        if isinstance(self.related_issues, str):
            self.related_issues = [self.related_issues]
        if isinstance(self.linked_tasks, str):
            self.linked_tasks = [self.linked_tasks]
        if isinstance(self.linked_prs, str):
            self.linked_prs = [self.linked_prs]
        if isinstance(self.linked_deployments, str):
            self.linked_deployments = [self.linked_deployments]
        if isinstance(self.comments, str):
            self.comments = [self.comments]
    
    def add_label(self, label: str) -> None:
        """Add a label"""
        if label not in self.labels:
            self.labels.append(label)
    
    def remove_label(self, label: str) -> bool:
        """Remove a label"""
        if label in self.labels:
            self.labels.remove(label)
            return True
        return False
    
    def has_label(self, label: str) -> bool:
        """Check if issue has a specific label"""
        return label in self.labels
    
    def add_external_id(self, system: str, external_id: str) -> None:
        """Add an external system ID"""
        self.external_ids[system] = external_id
    
    def get_external_id(self, system: str) -> Optional[str]:
        """Get external ID for a system"""
        return self.external_ids.get(system)
    
    def link_task(self, task_id: str) -> None:
        """Link a task to this issue"""
        if task_id not in self.linked_tasks:
            self.linked_tasks.append(task_id)
    
    def unlink_task(self, task_id: str) -> bool:
        """Unlink a task from this issue"""
        if task_id in self.linked_tasks:
            self.linked_tasks.remove(task_id)
            return True
        return False
    
    def link_pr(self, pr_id: str) -> None:
        """Link a pull request to this issue"""
        if pr_id not in self.linked_prs:
            self.linked_prs.append(pr_id)
    
    def link_deployment(self, deployment_id: str) -> None:
        """Link a deployment to this issue"""
        if deployment_id not in self.linked_deployments:
            self.linked_deployments.append(deployment_id)
    
    def relate_issue(self, issue_id: str) -> None:
        """Relate another issue"""
        if issue_id not in self.related_issues:
            self.related_issues.append(issue_id)
    
    def add_comment(self, comment_id: str) -> None:
        """Add a comment reference"""
        if comment_id not in self.comments:
            self.comments.append(comment_id)
    
    def set_status(self, status: IssueStatus) -> None:
        """Set issue status"""
        self.status = status
        if status in [IssueStatus.DONE, IssueStatus.CANCELLED]:
            self.closed_at = datetime.now(timezone.utc).isoformat()
        if status == IssueStatus.DONE:
            self.resolved_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_type(self, issue_type: IssueType) -> None:
        """Set issue type"""
        self.issue_type = issue_type
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_severity(self, severity: IssueSeverity) -> None:
        """Set issue severity"""
        self.severity = severity
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_assignee(self, person_id: str) -> None:
        """Assign issue to a person"""
        self.assignee_id = person_id
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field"""
        self.custom_fields[key] = value
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field"""
        return self.custom_fields.get(key, default)
    
    def is_open(self) -> bool:
        """Check if issue is open"""
        return self.status not in [IssueStatus.DONE, IssueStatus.CANCELLED]
    
    def is_closed(self) -> bool:
        """Check if issue is closed"""
        return self.status in [IssueStatus.DONE, IssueStatus.CANCELLED]
    
    def is_resolved(self) -> bool:
        """Check if issue is resolved"""
        return self.status == IssueStatus.DONE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        result.update({
            "issue_type": self.issue_type.value,
            "status": self.status.value,
            "severity": self.severity.value,
            "repository_id": self.repository_id,
            "project_id": self.project_id,
            "assignee_id": self.assignee_id,
            "reporter_id": self.reporter_id,
            "labels": self.labels,
            "milestone_id": self.milestone_id,
            "related_issues": self.related_issues,
            "linked_tasks": self.linked_tasks,
            "linked_prs": self.linked_prs,
            "linked_deployments": self.linked_deployments,
            "due_date": self.due_date,
            "closed_at": self.closed_at,
            "resolved_at": self.resolved_at,
            "external_ids": self.external_ids,
            "comments": self.comments,
            "custom_fields": self.custom_fields
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Issue":
        """Create from dictionary"""
        uaw_id = data.get("uaw_id")
        if isinstance(uaw_id, str):
            uaw_id = UAWIdentifier.from_string(uaw_id)
        
        return cls(
            uaw_id=uaw_id,
            name=data.get("name", ""),
            description=data.get("description"),
            issue_type=IssueType(data.get("issue_type", "task")),
            status=IssueStatus(data.get("status", "backlog")),
            severity=IssueSeverity(data.get("severity", "medium")),
            repository_id=data.get("repository_id"),
            project_id=data.get("project_id"),
            assignee_id=data.get("assignee_id"),
            reporter_id=data.get("reporter_id"),
            labels=data.get("labels", []),
            milestone_id=data.get("milestone_id"),
            related_issues=data.get("related_issues", []),
            linked_tasks=data.get("linked_tasks", []),
            linked_prs=data.get("linked_prs", []),
            linked_deployments=data.get("linked_deployments", []),
            due_date=data.get("due_date"),
            closed_at=data.get("closed_at"),
            resolved_at=data.get("resolved_at"),
            external_ids=data.get("external_ids", {}),
            comments=data.get("comments", []),
            custom_fields=data.get("custom_fields", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            is_active=data.get("is_active", True)
        )
    
    def get_github_issue_number(self) -> Optional[str]:
        """Get GitHub issue number if available"""
        return self.external_ids.get("github")
    
    def get_linear_issue_id(self) -> Optional[str]:
        """Get Linear issue ID if available"""
        return self.external_ids.get("linear")
    
    def get_asana_task_id(self) -> Optional[str]:
        """Get Asana task GID if available"""
        return self.external_ids.get("asana")


@dataclass
class IssueBuilder:
    """Builder for creating Issue instances"""
    
    name: str
    issue_type: IssueType = IssueType.TASK
    
    def with_description(self, description: str) -> "IssueBuilder":
        """Set description"""
        self._description = description
        return self
    
    def with_status(self, status: IssueStatus) -> "IssueBuilder":
        """Set status"""
        self._status = status
        return self
    
    def with_severity(self, severity: IssueSeverity) -> "IssueBuilder":
        """Set severity"""
        self._severity = severity
        return self
    
    def with_repository(self, repository_id: str) -> "IssueBuilder":
        """Set related repository"""
        self._repository_id = repository_id
        return self
    
    def with_project(self, project_id: str) -> "IssueBuilder":
        """Set related project"""
        self._project_id = project_id
        return self
    
    def with_assignee(self, person_id: str) -> "IssueBuilder":
        """Set assignee"""
        self._assignee_id = person_id
        return self
    
    def with_reporter(self, person_id: str) -> "IssueBuilder":
        """Set reporter"""
        self._reporter_id = person_id
        return self
    
    def with_label(self, label: str) -> "IssueBuilder":
        """Add label"""
        self._labels = getattr(self, "_labels", [])
        if label not in self._labels:
            self._labels.append(label)
        return self
    
    def with_due_date(self, due_date: str) -> "IssueBuilder":
        """Set due date"""
        self._due_date = due_date
        return self
    
    def with_external_id(self, system: str, external_id: str) -> "IssueBuilder":
        """Add external ID"""
        self._external_ids = getattr(self, "_external_ids", {})
        self._external_ids[system] = external_id
        return self
    
    def build(self) -> Issue:
        """Build Issue instance"""
        return Issue(
            uaw_id=Issue.generate_id(),
            name=self.name,
            description=getattr(self, "_description", None),
            issue_type=self.issue_type,
            status=getattr(self, "_status", IssueStatus.BACKLOG),
            severity=getattr(self, "_severity", IssueSeverity.MEDIUM),
            repository_id=getattr(self, "_repository_id", None),
            project_id=getattr(self, "_project_id", None),
            assignee_id=getattr(self, "_assignee_id", None),
            reporter_id=getattr(self, "_reporter_id", None),
            labels=getattr(self, "_labels", []),
            due_date=getattr(self, "_due_date", None),
            external_ids=getattr(self, "_external_ids", {})
        )
