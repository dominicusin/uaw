"""
UAW Models Package
Модуль моделей данных для Unified Agentic Workspace

Содержит все модели сущностей системы:
- BaseModel, UAWIdentifier: Базовые модели
- Person: Пользователь/сотрудник
- Team: Команда
- Project: Проект
- Task: Задача/подзадача
- Issue: Дефект/запрос на изменение
- Repository: Репозиторий
- Deployment: Развёртывание
- Document: Документ/файл
- Event: Событие/встреча
- Workflow: Рабочий процесс
- Integration: Интеграция
- Approval: Подтверждение
- AuditEvent: Журнал операций
"""

from .base import BaseModel, EntityType, UAWIdentifier
from .person import Person, PersonBuilder
from .team import Team, TeamBuilder
from .project import Project, ProjectBuilder, ProjectStatus, ProjectVisibility
from .task import Task, TaskBuilder, TaskStatus, TaskPriority
from .issue import Issue, IssueBuilder, IssueStatus, IssueType, IssueSeverity
from .repository import (
    Repository, RepositoryBuilder, RepositoryStatus, RepositoryVisibility,
    Branch, BranchProtection, Commit, PullRequest
)
from .deployment import (
    Deployment, DeploymentBuilder, DeploymentEnvironment, DeploymentStatus, DeploymentType,
    BuildInfo, HealthCheck, TestResult
)
from .document import (
    Document, DocumentBuilder, DocumentType, DocumentStatus, DocumentVisibility,
    DocumentVersion, DocumentComment
)
from .event import (
    Event, EventBuilder, EventType, EventStatus, EventVisibility,
    Attendee, RSVPStatus, EventRecurrence
)
from .workflow import (
    Workflow, WorkflowBuilder, WorkflowStatus, WorkflowTriggerType,
    StepStatus, WorkflowCondition, WorkflowAction, WorkflowStep, WorkflowTrigger
)
from .integration import (
    Integration, IntegrationBuilder, IntegrationStatus, IntegrationType,
    AuthenticationMethod, IntegrationCapability, IntegrationRateLimit
)
from .approval import (
    Approval, ApprovalBuilder, ApprovalStatus, ApprovalType, ApprovalPriority,
    ApprovalVote
)
from .audit_event import (
    AuditEvent, AuditEventBuilder, AuditEventType, AuditEventSeverity, AuditEventStatus,
    create_resource_created_event, create_resource_updated_event,
    create_integration_error_event, create_workflow_event
)

# All model classes
MODEL_CLASSES = {
    EntityType.PERSON: Person,
    EntityType.TEAM: Team,
    EntityType.PROJECT: Project,
    EntityType.TASK: Task,
    EntityType.ISSUE: Issue,
    EntityType.REPOSITORY: Repository,
    EntityType.DEPLOYMENT: Deployment,
    EntityType.DOCUMENT: Document,
    EntityType.EVENT: Event,
    EntityType.WORKFLOW: Workflow,
    EntityType.INTEGRATION: Integration,
    EntityType.APPROVAL: Approval,
    EntityType.AUDIT_EVENT: AuditEvent,
}

# Builder classes
BUILDER_CLASSES = {
    EntityType.PERSON: PersonBuilder,
    EntityType.TEAM: TeamBuilder,
    EntityType.PROJECT: ProjectBuilder,
    EntityType.TASK: TaskBuilder,
    EntityType.ISSUE: IssueBuilder,
    EntityType.REPOSITORY: RepositoryBuilder,
    EntityType.DEPLOYMENT: DeploymentBuilder,
    EntityType.DOCUMENT: DocumentBuilder,
    EntityType.EVENT: EventBuilder,
    EntityType.WORKFLOW: WorkflowBuilder,
    EntityType.INTEGRATION: IntegrationBuilder,
    EntityType.APPROVAL: ApprovalBuilder,
    EntityType.AUDIT_EVENT: AuditEventBuilder,
}

# Enum types
STATUS_ENUMS = {
    "task": TaskStatus,
    "issue": IssueStatus,
    "project": ProjectStatus,
    "repository": RepositoryStatus,
    "deployment": DeploymentStatus,
    "document": DocumentStatus,
    "event": EventStatus,
    "workflow": WorkflowStatus,
    "step": StepStatus,
    "approval": ApprovalStatus,
    "audit_event": AuditEventStatus,
}

TYPE_ENUMS = {
    "issue": IssueType,
    "deployment": DeploymentType,
    "document": DocumentType,
    "event": EventType,
    "approval": ApprovalType,
    "workflow_trigger": WorkflowTriggerType,
    "repository_visibility": RepositoryVisibility,
    "project_visibility": ProjectVisibility,
    "document_visibility": DocumentVisibility,
    "event_visibility": EventVisibility,
    "integration_type": IntegrationType,
    "authentication_method": AuthenticationMethod,
    "integration_status": IntegrationStatus,
}

__all__ = [
    # Base
    "BaseModel", "EntityType", "UAWIdentifier",
    
    # Person
    "Person", "PersonBuilder",
    
    # Team
    "Team", "TeamBuilder",
    
    # Project
    "Project", "ProjectBuilder", "ProjectStatus", "ProjectVisibility",
    
    # Task
    "Task", "TaskBuilder", "TaskStatus", "TaskPriority",
    
    # Issue
    "Issue", "IssueBuilder", "IssueStatus", "IssueType", "IssueSeverity",
    
    # Repository
    "Repository", "RepositoryBuilder", "RepositoryStatus", "RepositoryVisibility",
    "Branch", "BranchProtection", "Commit", "PullRequest",
    
    # Deployment
    "Deployment", "DeploymentBuilder", "DeploymentEnvironment", "DeploymentStatus", "DeploymentType",
    "BuildInfo", "HealthCheck", "TestResult",
    
    # Document
    "Document", "DocumentBuilder", "DocumentType", "DocumentStatus", "DocumentVisibility",
    "DocumentVersion", "DocumentComment",
    
    # Event
    "Event", "EventBuilder", "EventType", "EventStatus", "EventVisibility",
    "Attendee", "RSVPStatus", "EventRecurrence",
    
    # Workflow
    "Workflow", "WorkflowBuilder", "WorkflowStatus", "WorkflowTriggerType",
    "StepStatus", "WorkflowCondition", "WorkflowAction", "WorkflowStep", "WorkflowTrigger",
    
    # Integration
    "Integration", "IntegrationBuilder", "IntegrationStatus", "IntegrationType",
    "AuthenticationMethod", "IntegrationCapability", "IntegrationRateLimit",
    
    # Approval
    "Approval", "ApprovalBuilder", "ApprovalStatus", "ApprovalType", "ApprovalPriority",
    "ApprovalVote",
    
    # AuditEvent
    "AuditEvent", "AuditEventBuilder", "AuditEventType", "AuditEventSeverity", "AuditEventStatus",
    "create_resource_created_event", "create_resource_updated_event",
    "create_integration_error_event", "create_workflow_event",
    
    # Collections
    "MODEL_CLASSES", "BUILDER_CLASSES", "STATUS_ENUMS", "TYPE_ENUMS",
]
