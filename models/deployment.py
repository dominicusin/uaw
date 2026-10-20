"""
Deployment Model for UAW
Модель окружения, версии, статуса сборки и результата проверки
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

from .base import BaseModel, EntityType, UAWIdentifier


class DeploymentEnvironment(Enum):
    """Deployment environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PREVIEW = "preview"
    PRODUCTION = "production"
    TESTING = "testing"


class DeploymentStatus(Enum):
    """Status of a deployment"""
    PENDING = "pending"
    QUEUED = "queued"
    BUILDING = "building"
    DEPLOYING = "deploying"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class DeploymentType(Enum):
    """Type of deployment"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    CI_CD = "ci_cd"
    HOTFIX = "hotfix"
    SCHEDULED = "scheduled"


@dataclass
class BuildInfo:
    """Build information"""
    build_id: str
    build_number: Optional[str] = None
    commit_sha: Optional[str] = None
    branch: Optional[str] = None
    status: str = "queued"  # queued, building, successful, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    artifacts: List[str] = field(default_factory=list)
    logs_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "build_id": self.build_id,
            "build_number": self.build_number,
            "commit_sha": self.commit_sha,
            "branch": self.branch,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "artifacts": self.artifacts,
            "logs_url": self.logs_url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuildInfo":
        return cls(
            build_id=data.get("build_id", ""),
            build_number=data.get("build_number"),
            commit_sha=data.get("commit_sha"),
            branch=data.get("branch"),
            status=data.get("status", "queued"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            duration_seconds=data.get("duration_seconds"),
            artifacts=data.get("artifacts", []),
            logs_url=data.get("logs_url")
        )


@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: str = "unknown"  # healthy, unhealthy, degraded, unknown
    latency_ms: Optional[int] = None
    checked_at: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "checked_at": self.checked_at,
            "details": self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HealthCheck":
        return cls(
            name=data.get("name", ""),
            status=data.get("status", "unknown"),
            latency_ms=data.get("latency_ms"),
            checked_at=data.get("checked_at"),
            details=data.get("details", {})
        )


@dataclass
class TestResult:
    """Test result"""
    test_suite: str
    status: str = "queued"  # queued, running, passed, failed, skipped
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    duration_seconds: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    failures: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_suite": self.test_suite,
            "status": self.status,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "duration_seconds": self.duration_seconds,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "failures": self.failures
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestResult":
        return cls(
            test_suite=data.get("test_suite", ""),
            status=data.get("status", "queued"),
            total_tests=data.get("total_tests", 0),
            passed_tests=data.get("passed_tests", 0),
            failed_tests=data.get("failed_tests", 0),
            skipped_tests=data.get("skipped_tests", 0),
            duration_seconds=data.get("duration_seconds"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            failures=data.get("failures", [])
        )


@dataclass
class Deployment(BaseModel):
    """
    Deployment model representing a deployment of code.
    
    Attributes:
        uaw_id: Unique UAW identifier
        version: Deployment version
        environment: Deployment environment
        status: Current deployment status
        deployment_type: Type of deployment
        repository_id: UAW ID of repository being deployed
        commit_sha: Commit SHA being deployed
        branch: Branch being deployed
        pull_request_id: UAW ID of related pull request
        project_id: UAW ID of related project
        issue_id: UAW ID of related issue
        build_info: Build information
        health_checks: Health check results
        test_results: Test results
        deployed_by: UAW ID of person who deployed
        approved_by: List of UAW IDs of people who approved
        started_at: When deployment started
        completed_at: When deployment completed
        rollback_reason: Reason for rollback if rolled back
        external_ids: IDs in external systems
        custom_fields: Custom deployment fields
    """
    
    entity_type: ClassVar[EntityType] = EntityType.DEPLOYMENT
    
    version: str = "1.0.0"
    environment: DeploymentEnvironment = DeploymentEnvironment.DEVELOPMENT
    status: DeploymentStatus = DeploymentStatus.PENDING
    deployment_type: DeploymentType = DeploymentType.AUTOMATIC
    
    repository_id: Optional[str] = None
    commit_sha: Optional[str] = None
    branch: Optional[str] = None
    pull_request_id: Optional[str] = None
    project_id: Optional[str] = None
    issue_id: Optional[str] = None
    
    # Build and test info
    build_info: Optional[BuildInfo] = None
    health_checks: Dict[str, HealthCheck] = field(default_factory=dict)
    test_results: Dict[str, TestResult] = field(default_factory=dict)
    
    deployed_by: Optional[str] = None
    approved_by: List[str] = field(default_factory=list)
    
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    rollback_reason: Optional[str] = None
    
    # External system IDs
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.approved_by, str):
            self.approved_by = [self.approved_by]
    
    def add_external_id(self, system: str, external_id: str) -> None:
        """Add an external system ID"""
        self.external_ids[system] = external_id
    
    def get_external_id(self, system: str) -> Optional[str]:
        """Get external ID for a system"""
        return self.external_ids.get(system)
    
    def set_build_info(self, build_info: BuildInfo) -> None:
        """Set build information"""
        self.build_info = build_info
    
    def add_health_check(self, health_check: HealthCheck) -> None:
        """Add a health check result"""
        self.health_checks[health_check.name] = health_check
    
    def add_test_result(self, test_result: TestResult) -> None:
        """Add a test result"""
        self.test_results[test_result.test_suite] = test_result
    
    def add_approval(self, person_id: str) -> None:
        """Add an approval"""
        if person_id not in self.approved_by:
            self.approved_by.append(person_id)
    
    def set_status(self, status: DeploymentStatus) -> None:
        """Set deployment status"""
        self.status = status
        if status in [DeploymentStatus.SUCCESSFUL, DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK, DeploymentStatus.CANCELLED]:
            self.completed_at = datetime.now(timezone.utc).isoformat()
        if status == DeploymentStatus.BUILDING or status == DeploymentStatus.DEPLOYING:
            self.started_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field"""
        self.custom_fields[key] = value
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field"""
        return self.custom_fields.get(key, default)
    
    def is_successful(self) -> bool:
        """Check if deployment was successful"""
        return self.status == DeploymentStatus.SUCCESSFUL
    
    def is_failed(self) -> bool:
        """Check if deployment failed"""
        return self.status == DeploymentStatus.FAILED
    
    def is_in_progress(self) -> bool:
        """Check if deployment is in progress"""
        return self.status in [DeploymentStatus.QUEUED, DeploymentStatus.BUILDING, DeploymentStatus.DEPLOYING]
    
    def is_production(self) -> bool:
        """Check if this is a production deployment"""
        return self.environment == DeploymentEnvironment.PRODUCTION
    
    def is_preview(self) -> bool:
        """Check if this is a preview deployment"""
        return self.environment == DeploymentEnvironment.PREVIEW
    
    def requires_approval(self) -> bool:
        """Check if deployment requires approval"""
        return self.is_production() and len(self.approved_by) == 0
    
    def all_health_checks_passed(self) -> bool:
        """Check if all health checks passed"""
        return all(hc.status == "healthy" for hc in self.health_checks.values())
    
    def all_tests_passed(self) -> bool:
        """Check if all tests passed"""
        return all(tr.status == "passed" for tr in self.test_results.values())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        result.update({
            "version": self.version,
            "environment": self.environment.value,
            "status": self.status.value,
            "deployment_type": self.deployment_type.value,
            "repository_id": self.repository_id,
            "commit_sha": self.commit_sha,
            "branch": self.branch,
            "pull_request_id": self.pull_request_id,
            "project_id": self.project_id,
            "issue_id": self.issue_id,
            "build_info": self.build_info.to_dict() if self.build_info else None,
            "health_checks": {k: v.to_dict() for k, v in self.health_checks.items()},
            "test_results": {k: v.to_dict() for k, v in self.test_results.items()},
            "deployed_by": self.deployed_by,
            "approved_by": self.approved_by,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "rollback_reason": self.rollback_reason,
            "external_ids": self.external_ids,
            "custom_fields": self.custom_fields
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Deployment":
        """Create from dictionary"""
        uaw_id = data.get("uaw_id")
        if isinstance(uaw_id, str):
            uaw_id = UAWIdentifier.from_string(uaw_id)
        
        # Parse build info
        build_info = None
        if data.get("build_info"):
            build_info = BuildInfo.from_dict(data["build_info"])
        
        # Parse health checks
        health_checks = {}
        for name, hc_data in data.get("health_checks", {}).items():
            health_checks[name] = HealthCheck.from_dict(hc_data)
        
        # Parse test results
        test_results = {}
        for suite, tr_data in data.get("test_results", {}).items():
            test_results[suite] = TestResult.from_dict(tr_data)
        
        return cls(
            uaw_id=uaw_id,
            name=data.get("name", ""),
            description=data.get("description"),
            version=data.get("version", "1.0.0"),
            environment=DeploymentEnvironment(data.get("environment", "development")),
            status=DeploymentStatus(data.get("status", "pending")),
            deployment_type=DeploymentType(data.get("deployment_type", "automatic")),
            repository_id=data.get("repository_id"),
            commit_sha=data.get("commit_sha"),
            branch=data.get("branch"),
            pull_request_id=data.get("pull_request_id"),
            project_id=data.get("project_id"),
            issue_id=data.get("issue_id"),
            build_info=build_info,
            health_checks=health_checks,
            test_results=test_results,
            deployed_by=data.get("deployed_by"),
            approved_by=data.get("approved_by", []),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            rollback_reason=data.get("rollback_reason"),
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
    
    def get_vercel_deployment_id(self) -> Optional[str]:
        """Get Vercel deployment ID if available"""
        return self.external_ids.get("vercel")
    
    def get_netlify_deployment_id(self) -> Optional[str]:
        """Get Netlify deployment ID if available"""
        return self.external_ids.get("netlify")
    
    def get_github_actions_run_id(self) -> Optional[str]:
        """Get GitHub Actions run ID if available"""
        return self.external_ids.get("github_actions")


@dataclass
class DeploymentBuilder:
    """Builder for creating Deployment instances"""
    
    version: str
    environment: DeploymentEnvironment = DeploymentEnvironment.DEVELOPMENT
    
    def with_name(self, name: str) -> "DeploymentBuilder":
        """Set name"""
        self._name = name
        return self
    
    def with_description(self, description: str) -> "DeploymentBuilder":
        """Set description"""
        self._description = description
        return self
    
    def with_repository(self, repository_id: str) -> "DeploymentBuilder":
        """Set repository"""
        self._repository_id = repository_id
        return self
    
    def with_commit(self, commit_sha: str, branch: str) -> "DeploymentBuilder":
        """Set commit and branch"""
        self._commit_sha = commit_sha
        self._branch = branch
        return self
    
    def with_pr(self, pull_request_id: str) -> "DeploymentBuilder":
        """Set related pull request"""
        self._pull_request_id = pull_request_id
        return self
    
    def with_project(self, project_id: str) -> "DeploymentBuilder":
        """Set related project"""
        self._project_id = project_id
        return self
    
    def with_issue(self, issue_id: str) -> "DeploymentBuilder":
        """Set related issue"""
        self._issue_id = issue_id
        return self
    
    def with_deployer(self, person_id: str) -> "DeploymentBuilder":
        """Set deployer"""
        self._deployed_by = person_id
        return self
    
    def with_external_id(self, system: str, external_id: str) -> "DeploymentBuilder":
        """Add external ID"""
        self._external_ids = getattr(self, "_external_ids", {})
        self._external_ids[system] = external_id
        return self
    
    def build(self) -> Deployment:
        """Build Deployment instance"""
        return Deployment(
            uaw_id=Deployment.generate_id(),
            name=getattr(self, "_name", f"Deployment {self.version}"),
            description=getattr(self, "_description", None),
            version=self.version,
            environment=self.environment,
            repository_id=getattr(self, "_repository_id", None),
            commit_sha=getattr(self, "_commit_sha", None),
            branch=getattr(self, "_branch", None),
            pull_request_id=getattr(self, "_pull_request_id", None),
            project_id=getattr(self, "_project_id", None),
            issue_id=getattr(self, "_issue_id", None),
            deployed_by=getattr(self, "_deployed_by", None),
            external_ids=getattr(self, "_external_ids", {})
        )
