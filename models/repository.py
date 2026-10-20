"""
Repository Model for UAW
Модель репозитория, ветки, коммита и pull request
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

from .base import BaseModel, EntityType, UAWIdentifier


class RepositoryVisibility(Enum):
    """Visibility of a repository"""
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"


class RepositoryStatus(Enum):
    """Status of a repository"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class BranchProtection(Enum):
    """Branch protection level"""
    NONE = "none"
    READ_ONLY = "read_only"
    REQUIRES_REVIEW = "requires_review"
    REQUIRES_STATUS_CHECKS = "requires_status_checks"
    FULL_PROTECTION = "full_protection"


@dataclass
class Branch:
    """Branch model"""
    name: str
    sha: str
    is_default: bool = False
    is_protected: bool = False
    protection_level: BranchProtection = BranchProtection.NONE
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "sha": self.sha,
            "is_default": self.is_default,
            "is_protected": self.is_protected,
            "protection_level": self.protection_level.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Branch":
        return cls(
            name=data.get("name", ""),
            sha=data.get("sha", ""),
            is_default=data.get("is_default", False),
            is_protected=data.get("is_protected", False),
            protection_level=BranchProtection(data.get("protection_level", "none")),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class Commit:
    """Commit model"""
    sha: str
    message: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    author_date: Optional[str] = None
    committer_name: Optional[str] = None
    committer_email: Optional[str] = None
    committer_date: Optional[str] = None
    parents: List[str] = field(default_factory=list)
    files_changed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sha": self.sha,
            "message": self.message,
            "author_name": self.author_name,
            "author_email": self.author_email,
            "author_date": self.author_date,
            "committer_name": self.committer_name,
            "committer_email": self.committer_email,
            "committer_date": self.committer_date,
            "parents": self.parents,
            "files_changed": self.files_changed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Commit":
        return cls(
            sha=data.get("sha", ""),
            message=data.get("message", ""),
            author_name=data.get("author_name"),
            author_email=data.get("author_email"),
            author_date=data.get("author_date"),
            committer_name=data.get("committer_name"),
            committer_email=data.get("committer_email"),
            committer_date=data.get("committer_date"),
            parents=data.get("parents", []),
            files_changed=data.get("files_changed", [])
        )


@dataclass
class PullRequest:
    """Pull Request model"""
    number: int
    title: str
    body: Optional[str] = None
    state: str = "open"  # open, closed, merged
    is_merged: bool = False
    is_draft: bool = False
    base_branch: str = "main"
    head_branch: str = ""
    author_id: Optional[str] = None
    assignee_ids: List[str] = field(default_factory=list)
    reviewer_ids: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    linked_issues: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    merged_at: Optional[str] = None
    closed_at: Optional[str] = None
    commits: List[str] = field(default_factory=list)  # List of commit SHAs
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "state": self.state,
            "is_merged": self.is_merged,
            "is_draft": self.is_draft,
            "base_branch": self.base_branch,
            "head_branch": self.head_branch,
            "author_id": self.author_id,
            "assignee_ids": self.assignee_ids,
            "reviewer_ids": self.reviewer_ids,
            "labels": self.labels,
            "linked_issues": self.linked_issues,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "merged_at": self.merged_at,
            "closed_at": self.closed_at,
            "commits": self.commits
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PullRequest":
        return cls(
            number=data.get("number", 0),
            title=data.get("title", ""),
            body=data.get("body"),
            state=data.get("state", "open"),
            is_merged=data.get("is_merged", False),
            is_draft=data.get("is_draft", False),
            base_branch=data.get("base_branch", "main"),
            head_branch=data.get("head_branch", ""),
            author_id=data.get("author_id"),
            assignee_ids=data.get("assignee_ids", []),
            reviewer_ids=data.get("reviewer_ids", []),
            labels=data.get("labels", []),
            linked_issues=data.get("linked_issues", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            merged_at=data.get("merged_at"),
            closed_at=data.get("closed_at"),
            commits=data.get("commits", [])
        )


@dataclass
class Repository(BaseModel):
    """
    Repository model representing a code repository.
    
    Attributes:
        uaw_id: Unique UAW identifier
        name: Repository name
        full_name: Full repository name (org/repo)
        description: Repository description
        visibility: Repository visibility
        status: Repository status
        organization_id: UAW ID of organization
        team_id: UAW ID of primary team
        default_branch: Default branch name
        branches: List of branches
        open_prs: List of open pull requests
        closed_prs: List of closed pull requests
        issues_enabled: Whether issues are enabled
        wiki_enabled: Whether wiki is enabled
        stars: Number of stars
        forks: Number of forks
        size: Repository size in bytes
        language: Primary language
        topics: List of topics/tags
        homepage: Homepage URL
        external_ids: IDs in external systems
        custom_fields: Custom repository fields
    """
    
    entity_type: ClassVar[EntityType] = EntityType.REPOSITORY
    
    full_name: Optional[str] = None
    visibility: RepositoryVisibility = RepositoryVisibility.PRIVATE
    status: RepositoryStatus = RepositoryStatus.ACTIVE
    
    organization_id: Optional[str] = None
    team_id: Optional[str] = None
    default_branch: str = "main"
    
    # Branches
    branches: Dict[str, Branch] = field(default_factory=dict)
    
    # Pull requests
    open_prs: Dict[int, PullRequest] = field(default_factory=dict)
    closed_prs: Dict[int, PullRequest] = field(default_factory=dict)
    
    # Features
    issues_enabled: bool = True
    wiki_enabled: bool = False
    
    # Statistics
    stars: int = 0
    forks: int = 0
    size: int = 0
    language: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    homepage: Optional[str] = None
    
    # External system IDs
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.topics, str):
            self.topics = [self.topics]
    
    def add_branch(self, branch: Branch) -> None:
        """Add a branch"""
        self.branches[branch.name] = branch
    
    def remove_branch(self, branch_name: str) -> bool:
        """Remove a branch"""
        if branch_name in self.branches:
            del self.branches[branch_name]
            return True
        return False
    
    def get_branch(self, branch_name: str) -> Optional[Branch]:
        """Get a branch by name"""
        return self.branches.get(branch_name)
    
    def add_pr(self, pr: PullRequest) -> None:
        """Add a pull request"""
        if pr.state == "open":
            self.open_prs[pr.number] = pr
        else:
            self.closed_prs[pr.number] = pr
    
    def get_pr(self, pr_number: int) -> Optional[PullRequest]:
        """Get a pull request by number"""
        return self.open_prs.get(pr_number) or self.closed_prs.get(pr_number)
    
    def close_pr(self, pr_number: int) -> bool:
        """Close a pull request"""
        if pr_number in self.open_prs:
            pr = self.open_prs[pr_number]
            pr.state = "closed"
            pr.closed_at = datetime.now(timezone.utc).isoformat()
            self.closed_prs[pr_number] = pr
            del self.open_prs[pr_number]
            return True
        return False
    
    def merge_pr(self, pr_number: int) -> bool:
        """Merge a pull request"""
        if pr_number in self.open_prs:
            pr = self.open_prs[pr_number]
            pr.state = "closed"
            pr.is_merged = True
            pr.merged_at = datetime.now(timezone.utc).isoformat()
            pr.closed_at = datetime.now(timezone.utc).isoformat()
            self.closed_prs[pr_number] = pr
            del self.open_prs[pr_number]
            return True
        return False
    
    def add_external_id(self, system: str, external_id: str) -> None:
        """Add an external system ID"""
        self.external_ids[system] = external_id
    
    def get_external_id(self, system: str) -> Optional[str]:
        """Get external ID for a system"""
        return self.external_ids.get(system)
    
    def add_topic(self, topic: str) -> None:
        """Add a topic"""
        if topic not in self.topics:
            self.topics.append(topic)
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field"""
        self.custom_fields[key] = value
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field"""
        return self.custom_fields.get(key, default)
    
    def is_public(self) -> bool:
        """Check if repository is public"""
        return self.visibility == RepositoryVisibility.PUBLIC
    
    def is_archived(self) -> bool:
        """Check if repository is archived"""
        return self.status == RepositoryStatus.ARCHIVED
    
    def has_open_prs(self) -> bool:
        """Check if repository has open pull requests"""
        return len(self.open_prs) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        result.update({
            "full_name": self.full_name,
            "visibility": self.visibility.value,
            "status": self.status.value,
            "organization_id": self.organization_id,
            "team_id": self.team_id,
            "default_branch": self.default_branch,
            "branches": {k: v.to_dict() for k, v in self.branches.items()},
            "open_prs": {k: v.to_dict() for k, v in self.open_prs.items()},
            "closed_prs": {k: v.to_dict() for k, v in self.closed_prs.items()},
            "issues_enabled": self.issues_enabled,
            "wiki_enabled": self.wiki_enabled,
            "stars": self.stars,
            "forks": self.forks,
            "size": self.size,
            "language": self.language,
            "topics": self.topics,
            "homepage": self.homepage,
            "external_ids": self.external_ids,
            "custom_fields": self.custom_fields
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Repository":
        """Create from dictionary"""
        uaw_id = data.get("uaw_id")
        if isinstance(uaw_id, str):
            uaw_id = UAWIdentifier.from_string(uaw_id)
        
        # Parse branches
        branches = {}
        for name, branch_data in data.get("branches", {}).items():
            branches[name] = Branch.from_dict(branch_data)
        
        # Parse pull requests
        open_prs = {}
        closed_prs = {}
        for num, pr_data in data.get("open_prs", {}).items():
            open_prs[int(num)] = PullRequest.from_dict(pr_data)
        for num, pr_data in data.get("closed_prs", {}).items():
            closed_prs[int(num)] = PullRequest.from_dict(pr_data)
        
        return cls(
            uaw_id=uaw_id,
            name=data.get("name", ""),
            description=data.get("description"),
            full_name=data.get("full_name"),
            visibility=RepositoryVisibility(data.get("visibility", "private")),
            status=RepositoryStatus(data.get("status", "active")),
            organization_id=data.get("organization_id"),
            team_id=data.get("team_id"),
            default_branch=data.get("default_branch", "main"),
            branches=branches,
            open_prs=open_prs,
            closed_prs=closed_prs,
            issues_enabled=data.get("issues_enabled", True),
            wiki_enabled=data.get("wiki_enabled", False),
            stars=data.get("stars", 0),
            forks=data.get("forks", 0),
            size=data.get("size", 0),
            language=data.get("language"),
            topics=data.get("topics", []),
            homepage=data.get("homepage"),
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
    
    def get_github_repository(self) -> Optional[str]:
        """Get GitHub repository full name if available"""
        return self.external_ids.get("github") or self.full_name
    
    def get_gitlab_project_id(self) -> Optional[str]:
        """Get GitLab project ID if available"""
        return self.external_ids.get("gitlab")


@dataclass
class RepositoryBuilder:
    """Builder for creating Repository instances"""
    
    name: str
    full_name: Optional[str] = None
    
    def with_description(self, description: str) -> "RepositoryBuilder":
        """Set description"""
        self._description = description
        return self
    
    def with_visibility(self, visibility: RepositoryVisibility) -> "RepositoryBuilder":
        """Set visibility"""
        self._visibility = visibility
        return self
    
    def with_team(self, team_id: str) -> "RepositoryBuilder":
        """Set primary team"""
        self._team_id = team_id
        return self
    
    def with_default_branch(self, branch_name: str) -> "RepositoryBuilder":
        """Set default branch"""
        self._default_branch = branch_name
        return self
    
    def with_external_id(self, system: str, external_id: str) -> "RepositoryBuilder":
        """Add external ID"""
        self._external_ids = getattr(self, "_external_ids", {})
        self._external_ids[system] = external_id
        return self
    
    def build(self) -> Repository:
        """Build Repository instance"""
        return Repository(
            uaw_id=Repository.generate_id(),
            name=self.name,
            full_name=self.full_name,
            description=getattr(self, "_description", None),
            visibility=getattr(self, "_visibility", RepositoryVisibility.PRIVATE),
            team_id=getattr(self, "_team_id", None),
            default_branch=getattr(self, "_default_branch", "main"),
            external_ids=getattr(self, "_external_ids", {})
        )
