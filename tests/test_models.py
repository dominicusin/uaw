"""
Tests for UAW Data Models
"""

import unittest
from datetime import datetime, timedelta
from uuid import uuid4

from uaw.models.base import UAWIdentifier, BaseModel, EntityType, EntityStatus
from uaw.models.person import Person, PersonBuilder
from uaw.models.team import Team, TeamBuilder
from uaw.models.project import Project, ProjectBuilder
from uaw.models.task import Task, TaskBuilder, TaskStatus, TaskPriority
from uaw.models.issue import Issue, IssueBuilder, IssueType, IssueSeverity, IssueStatus
from uaw.models.repository import (
    Repository, RepositoryBuilder, Branch, BranchBuilder, 
    Commit, CommitBuilder, PullRequest, PullRequestBuilder, PullRequestStatus
)
from uaw.models.deployment import (
    Deployment, DeploymentBuilder, DeploymentStatus, 
    BuildInfo, HealthCheck, TestResult
)
from uaw.models.document import Document, DocumentBuilder, DocumentType, DocumentVersion
from uaw.models.event import Event, EventBuilder, EventStatus, Attendee, RSVPStatus, EventRecurrence
from uaw.models.workflow import (
    Workflow, WorkflowBuilder, WorkflowStep, WorkflowStepType, 
    WorkflowStatus, WorkflowTrigger, WorkflowCondition, WorkflowAction
)
from uaw.models.integration import (
    Integration, IntegrationBuilder, IntegrationStatus, 
    IntegrationCapability, IntegrationRateLimit
)
from uaw.models.approval import Approval, ApprovalBuilder, ApprovalStatus, ApprovalVote
from uaw.models.audit_event import AuditEvent, AuditEventBuilder, AuditEventType


class TestBaseModels(unittest.TestCase):
    """Tests for base model classes"""

    def test_uaw_identifier(self):
        """Test UAWIdentifier"""
        uaw_id = UAWIdentifier(
            entity_type=EntityType.ISSUE,
            entity_id="issue-123",
            service="github",
            external_id="github-issue-456"
        )
        
        self.assertEqual(uaw_id.entity_type, EntityType.ISSUE)
        self.assertEqual(uaw_id.entity_id, "issue-123")
        self.assertEqual(uaw_id.service, "github")
        self.assertEqual(uaw_id.external_id, "github-issue-456")

    def test_uaw_identifier_to_dict(self):
        """Test UAWIdentifier to_dict"""
        uaw_id = UAWIdentifier(
            entity_type=EntityType.PERSON,
            entity_id="person-123",
            service="github",
            external_id="user-456"
        )
        data = uaw_id.to_dict()
        
        self.assertIn("entity_type", data)
        self.assertIn("entity_id", data)
        self.assertIn("service", data)
        self.assertIn("external_id", data)

    def test_base_model(self):
        """Test BaseModel"""
        model = BaseModel(
            uaw_id="test-123",
            entity_type=EntityType.TASK,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            status=EntityStatus.ACTIVE
        )
        
        self.assertEqual(model.uaw_id, "test-123")
        self.assertEqual(model.entity_type, EntityType.TASK)
        self.assertIsNotNone(model.created_at)


class TestPerson(unittest.TestCase):
    """Tests for Person model"""

    def test_person_creation(self):
        """Test Person creation"""
        person = Person(
            uaw_id="person:123",
            name="John Doe",
            email="john@example.com",
            external_ids={"github": "johndoe", "asana": "user-456"},
            teams=["team-1", "team-2"],
            roles=["developer", "admin"],
            timezone="UTC",
        )
        
        self.assertEqual(person.name, "John Doe")
        self.assertEqual(person.email, "john@example.com")
        self.assertEqual(person.external_ids["github"], "johndoe")

    def test_person_to_dict(self):
        """Test Person to_dict"""
        person = Person(
            uaw_id="person:123",
            name="Jane Doe",
            email="jane@example.com"
        )
        data = person.to_dict()
        
        self.assertIn("uaw_id", data)
        self.assertIn("name", data)
        self.assertIn("email", data)

    def test_person_from_dict(self):
        """Test Person from_dict"""
        data = {
            "uaw_id": "person:123",
            "name": "Bob Smith",
            "email": "bob@example.com",
            "external_ids": {"github": "bobsmith"},
            "teams": ["team-1"],
            "roles": ["developer"],
            "timezone": "UTC",
            "avatar_url": None,
            "status": "ACTIVE",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        person = Person.from_dict(data)
        
        self.assertEqual(person.name, "Bob Smith")
        self.assertEqual(person.email, "bob@example.com")

    def test_person_builder(self):
        """Test PersonBuilder"""
        person = (
            PersonBuilder()
            .with_uaw_id("person:123")
            .with_name("Alice")
            .with_email("alice@example.com")
            .with_external_id("github", "alice123")
            .with_team("team-1")
            .with_role("developer")
            .build()
        )
        
        self.assertEqual(person.name, "Alice")
        self.assertEqual(person.email, "alice@example.com")
        self.assertIn("team-1", person.teams)


class TestTeam(unittest.TestCase):
    """Tests for Team model"""

    def test_team_creation(self):
        """Test Team creation"""
        team = Team(
            uaw_id="team:123",
            name="Development Team",
            description="Main development team",
            members=["person:1", "person:2"],
            visibility="private",
        )
        
        self.assertEqual(team.name, "Development Team")
        self.assertEqual(len(team.members), 2)

    def test_team_builder(self):
        """Test TeamBuilder"""
        team = (
            TeamBuilder()
            .with_uaw_id("team:123")
            .with_name("QA Team")
            .with_description("Quality Assurance")
            .with_member("person:1")
            .with_member("person:2")
            .build()
        )
        
        self.assertEqual(team.name, "QA Team")
        self.assertEqual(len(team.members), 2)


class TestProject(unittest.TestCase):
    """Tests for Project model"""

    def test_project_creation(self):
        """Test Project creation"""
        project = Project(
            uaw_id="project:123",
            name="My Project",
            description="A test project",
            status=EntityStatus.ACTIVE,
            visibility="public",
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
        )
        
        self.assertEqual(project.name, "My Project")
        self.assertEqual(project.status, EntityStatus.ACTIVE)

    def test_project_builder(self):
        """Test ProjectBuilder"""
        project = (
            ProjectBuilder()
            .with_uaw_id("project:123")
            .with_name("API Project")
            .with_description("REST API development")
            .with_external_id("github", "repo-123")
            .with_external_id("linear", "proj-456")
            .build()
        )
        
        self.assertEqual(project.name, "API Project")
        self.assertIn("github", project.external_ids)


class TestTask(unittest.TestCase):
    """Tests for Task model"""

    def test_task_creation(self):
        """Test Task creation"""
        task = Task(
            uaw_id="task:123",
            title="Implement login feature",
            description="Add user authentication",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            assignee_id="person:1",
            project_id="project:1",
            due_date=datetime.utcnow() + timedelta(days=7),
        )
        
        self.assertEqual(task.title, "Implement login feature")
        self.assertEqual(task.priority, TaskPriority.HIGH)

    def test_task_status_transitions(self):
        """Test Task status transitions"""
        task = Task(
            uaw_id="task:123",
            title="Test",
            status=TaskStatus.TODO,
        )
        
        # Valid transitions
        task.status = TaskStatus.IN_PROGRESS
        task.status = TaskStatus.DONE
        
        self.assertEqual(task.status, TaskStatus.DONE)

    def test_task_builder(self):
        """Test TaskBuilder"""
        task = (
            TaskBuilder()
            .with_uaw_id("task:123")
            .with_title("Fix bug")
            .with_description("Critical bug in login")
            .with_status(TaskStatus.IN_PROGRESS)
            .with_priority(TaskPriority.URGENT)
            .with_assignee("person:1")
            .with_project("project:1")
            .build()
        )
        
        self.assertEqual(task.title, "Fix bug")
        self.assertEqual(task.priority, TaskPriority.URGENT)


class TestIssue(unittest.TestCase):
    """Tests for Issue model"""

    def test_issue_creation(self):
        """Test Issue creation"""
        issue = Issue(
            uaw_id="issue:123",
            title="Login fails with special characters",
            description="Users cannot login with special chars in password",
            issue_type=IssueType.BUG,
            severity=IssueSeverity.HIGH,
            status=IssueStatus.OPEN,
            repository_id="repo:1",
            assignee_id="person:1",
            labels=["bug", "authentication"],
        )
        
        self.assertEqual(issue.title, "Login fails with special characters")
        self.assertEqual(issue.issue_type, IssueType.BUG)
        self.assertEqual(issue.severity, IssueSeverity.HIGH)

    def test_issue_builder(self):
        """Test IssueBuilder"""
        issue = (
            IssueBuilder()
            .with_uaw_id("issue:123")
            .with_title("Memory leak")
            .with_description("Memory usage grows indefinitely")
            .with_type(IssueType.BUG)
            .with_severity(IssueSeverity.CRITICAL)
            .with_status(IssueStatus.OPEN)
            .with_label("bug")
            .with_label("performance")
            .build()
        )
        
        self.assertEqual(issue.title, "Memory leak")
        self.assertEqual(issue.severity, IssueSeverity.CRITICAL)


class TestRepository(unittest.TestCase):
    """Tests for Repository and related models"""

    def test_repository_creation(self):
        """Test Repository creation"""
        repo = Repository(
            uaw_id="repo:123",
            name="my-repo",
            full_name="org/my-repo",
            description="A test repository",
            is_private=False,
            html_url="https://github.com/org/my-repo",
            default_branch="main",
        )
        
        self.assertEqual(repo.name, "my-repo")
        self.assertEqual(repo.full_name, "org/my-repo")

    def test_branch_creation(self):
        """Test Branch creation"""
        branch = Branch(
            uaw_id="branch:123",
            name="feature/login",
            repository_id="repo:1",
            sha="abc123",
            is_protected=False,
        )
        
        self.assertEqual(branch.name, "feature/login")
        self.assertEqual(branch.repository_id, "repo:1")

    def test_commit_creation(self):
        """Test Commit creation"""
        commit = Commit(
            uaw_id="commit:123",
            sha="abc123def456",
            message="Fix login bug",
            author_id="person:1",
            repository_id="repo:1",
            branch_id="branch:1",
        )
        
        self.assertEqual(commit.sha, "abc123def456")
        self.assertEqual(commit.message, "Fix login bug")

    def test_pull_request_creation(self):
        """Test PullRequest creation"""
        pr = PullRequest(
            uaw_id="pr:123",
            title="Fix login bug",
            body="Closes #123",
            status=PullRequestStatus.OPEN,
            repository_id="repo:1",
            source_branch_id="branch:1",
            target_branch_id="branch:2",
            author_id="person:1",
        )
        
        self.assertEqual(pr.title, "Fix login bug")
        self.assertEqual(pr.status, PullRequestStatus.OPEN)

    def test_pull_request_status_transitions(self):
        """Test PullRequest status transitions"""
        pr = PullRequest(
            uaw_id="pr:123",
            title="Test",
            status=PullRequestStatus.OPEN,
        )
        
        pr.status = PullRequestStatus.IN_REVIEW
        pr.status = PullRequestStatus.APPROVED
        pr.status = PullRequestStatus.MERGED
        
        self.assertEqual(pr.status, PullRequestStatus.MERGED)


class TestDeployment(unittest.TestCase):
    """Tests for Deployment model"""

    def test_deployment_creation(self):
        """Test Deployment creation"""
        deployment = Deployment(
            uaw_id="deployment:123",
            name="v1.0.0",
            environment="production",
            status=DeploymentStatus.QUEUED,
            repository_id="repo:1",
            commit_id="commit:1",
            url="https://app.example.com",
        )
        
        self.assertEqual(deployment.name, "v1.0.0")
        self.assertEqual(deployment.environment, "production")

    def test_build_info_creation(self):
        """Test BuildInfo creation"""
        build = BuildInfo(
            build_id="build:123",
            status="success",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_seconds=120,
            log_url="https://logs.example.com/build-123",
        )
        
        self.assertEqual(build.status, "success")
        self.assertEqual(build.duration_seconds, 120)

    def test_health_check_creation(self):
        """Test HealthCheck creation"""
        health = HealthCheck(
            check_id="health:123",
            name="API Health",
            status=True,
            response_time_ms=150,
            timestamp=datetime.utcnow(),
        )
        
        self.assertTrue(health.status)
        self.assertEqual(health.response_time_ms, 150)

    def test_test_result_creation(self):
        """Test TestResult creation"""
        test = TestResult(
            test_id="test:123",
            name="Unit Tests",
            status="passed",
            passed=10,
            failed=0,
            skipped=0,
            duration_seconds=45,
        )
        
        self.assertEqual(test.status, "passed")
        self.assertEqual(test.passed, 10)


class TestDocument(unittest.TestCase):
    """Tests for Document model"""

    def test_document_creation(self):
        """Test Document creation"""
        doc = Document(
            uaw_id="document:123",
            title="API Documentation",
            document_type=DocumentType.DOCUMENT,
            content="# API Docs",
            repository_id=None,
            project_id="project:1",
            author_id="person:1",
        )
        
        self.assertEqual(doc.title, "API Documentation")
        self.assertEqual(doc.document_type, DocumentType.DOCUMENT)

    def test_document_version_creation(self):
        """Test DocumentVersion creation"""
        version = DocumentVersion(
            version_id="version:123",
            document_id="document:1",
            version_number=1,
            content="# Updated Docs",
            author_id="person:1",
            created_at=datetime.utcnow(),
            change_description="Updated API endpoints",
        )
        
        self.assertEqual(version.version_number, 1)


class TestEvent(unittest.TestCase):
    """Tests for Event model"""

    def test_event_creation(self):
        """Test Event creation"""
        event = Event(
            uaw_id="event:123",
            title="Team Meeting",
            description="Weekly team sync",
            status=EventStatus.SCHEDULED,
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=1, hours=1),
            timezone="UTC",
            location="Zoom",
            is_online=True,
        )
        
        self.assertEqual(event.title, "Team Meeting")
        self.assertEqual(event.status, EventStatus.SCHEDULED)

    def test_attendee_creation(self):
        """Test Attendee creation"""
        attendee = Attendee(
            attendee_id="attendee:123",
            person_id="person:1",
            email="john@example.com",
            rsvp_status=RSVPStatus.ACCEPTED,
            event_id="event:1",
        )
        
        self.assertEqual(attendee.rsvp_status, RSVPStatus.ACCEPTED)

    def test_event_recurrence_creation(self):
        """Test EventRecurrence creation"""
        recurrence = EventRecurrence(
            recurrence_id="recurrence:123",
            event_id="event:1",
            frequency="weekly",
            interval=1,
            end_date=datetime.utcnow() + timedelta(weeks=12),
        )
        
        self.assertEqual(recurrence.frequency, "weekly")


class TestWorkflow(unittest.TestCase):
    """Tests for Workflow model"""

    def test_workflow_creation(self):
        """Test Workflow creation"""
        workflow = Workflow(
            uaw_id="workflow:123",
            name="CI/CD Pipeline",
            description="Automated build and deploy",
            status=WorkflowStatus.PENDING,
            steps=[],
        )
        
        self.assertEqual(workflow.name, "CI/CD Pipeline")
        self.assertEqual(workflow.status, WorkflowStatus.PENDING)

    def test_workflow_step_creation(self):
        """Test WorkflowStep creation"""
        step = WorkflowStep(
            uaw_id="step:123",
            name="Build",
            step_type=WorkflowStepType.ACTION,
            description="Build the project",
            integration="github",
            action="run_workflow",
            parameters={"workflow_id": "build.yml"},
            dependencies=[],
            timeout_seconds=300,
            retry_count=2,
        )
        
        self.assertEqual(step.name, "Build")
        self.assertEqual(step.step_type, WorkflowStepType.ACTION)

    def test_workflow_trigger_creation(self):
        """Test WorkflowTrigger creation"""
        trigger = WorkflowTrigger(
            trigger_id="trigger:123",
            trigger_type="webhook",
            description="GitHub push webhook",
            event_type="push",
            filter_conditions={"branch": "main"},
        )
        
        self.assertEqual(trigger.trigger_type, "webhook")

    def test_workflow_condition_creation(self):
        """Test WorkflowCondition creation"""
        condition = WorkflowCondition(
            condition_id="condition:123",
            type_="status_check",
            field="status",
            expected="success",
            action_on_failure="continue",
        )
        
        self.assertEqual(condition.type_, "status_check")

    def test_workflow_action_creation(self):
        """Test WorkflowAction creation"""
        action = WorkflowAction(
            action_id="action:123",
            name="Deploy",
            action_type="integration",
            integration="vercel",
            method="create_deployment",
            parameters={"environment": "production"},
        )
        
        self.assertEqual(action.name, "Deploy")

    def test_workflow_builder(self):
        """Test WorkflowBuilder"""
        workflow = (
            WorkflowBuilder()
            .with_uaw_id("workflow:123")
            .with_name("Test Workflow")
            .with_description("A test workflow")
            .with_status(WorkflowStatus.PENDING)
            .add_step(
                WorkflowStep(
                    uaw_id="step:1",
                    name="Step 1",
                    step_type=WorkflowStepType.ACTION,
                )
            )
            .build()
        )
        
        self.assertEqual(workflow.name, "Test Workflow")
        self.assertEqual(len(workflow.steps), 1)


class TestIntegration(unittest.TestCase):
    """Tests for Integration model"""

    def test_integration_creation(self):
        """Test Integration creation"""
        integration = Integration(
            uaw_id="integration:123",
            name="GitHub",
            service="github",
            status=IntegrationStatus.CONNECTED,
            base_url="https://api.github.com",
            rate_limits=[
                IntegrationRateLimit(
                    endpoint="/repos",
                    limit=5000,
                    period_seconds=3600,
                    remaining=4999,
                )
            ],
        )
        
        self.assertEqual(integration.name, "GitHub")
        self.assertEqual(integration.status, IntegrationStatus.CONNECTED)

    def test_integration_capability_creation(self):
        """Test IntegrationCapability creation"""
        capability = IntegrationCapability(
            capability_id="capability:123",
            integration_id="integration:1",
            name="list_repositories",
            description="List all repositories",
            method="GET",
            endpoint="/user/repos",
            is_available=True,
        )
        
        self.assertEqual(capability.name, "list_repositories")

    def test_integration_builder(self):
        """Test IntegrationBuilder"""
        integration = (
            IntegrationBuilder()
            .with_uaw_id("integration:123")
            .with_name("GitHub")
            .with_service("github")
            .with_status(IntegrationStatus.CONNECTED)
            .with_base_url("https://api.github.com")
            .build()
        )
        
        self.assertEqual(integration.name, "GitHub")


class TestApproval(unittest.TestCase):
    """Tests for Approval model"""

    def test_approval_creation(self):
        """Test Approval creation"""
        approval = Approval(
            uaw_id="approval:123",
            title="Production Deployment",
            description="Approve deployment to production",
            status=ApprovalStatus.PENDING,
            requester_id="person:1",
            required_approvers=["person:2", "person:3"],
            approved_approvers=[],
        )
        
        self.assertEqual(approval.title, "Production Deployment")
        self.assertEqual(approval.status, ApprovalStatus.PENDING)

    def test_approval_vote_creation(self):
        """Test ApprovalVote creation"""
        vote = ApprovalVote(
            vote_id="vote:123",
            approval_id="approval:1",
            voter_id="person:2",
            vote=True,
            comment="Looks good",
            timestamp=datetime.utcnow(),
        )
        
        self.assertTrue(vote.vote)


class TestAuditEvent(unittest.TestCase):
    """Tests for AuditEvent model"""

    def test_audit_event_creation(self):
        """Test AuditEvent creation"""
        event = AuditEvent(
            event_id="audit:123",
            event_type=AuditEventType.WORKFLOW_STARTED,
            resource_type="workflow",
            resource_id="workflow:1",
            action="start",
            status="success",
            details={"user": "admin"},
            timestamp=datetime.utcnow(),
        )
        
        self.assertEqual(event.event_type, AuditEventType.WORKFLOW_STARTED)

    def test_audit_event_to_dict(self):
        """Test AuditEvent to_dict"""
        event = AuditEvent(
            event_id="audit:123",
            event_type=AuditEventType.WORKFLOW_STARTED,
            resource_type="workflow",
            resource_id="workflow:1",
            action="start",
            status="success",
            details={},
            timestamp=datetime.utcnow(),
        )
        data = event.to_dict()
        
        self.assertIn("event_id", data)
        self.assertIn("event_type", data)
        self.assertIn("resource_type", data)


if __name__ == "__main__":
    unittest.main()
