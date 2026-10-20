"""
Approval Model for UAW
Модель запроса на подтверждение действия человеком
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

from .base import BaseModel, EntityType, UAWIdentifier


class ApprovalStatus(Enum):
    """Status of an approval"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalType(Enum):
    """Type of approval"""
    EXPLICIT = "explicit"  # Requires explicit approval
    POLICY_BASED = "policy_based"  # Auto-approved based on policy
    DELEGATED = "delegated"  # Delegated to specific person
    GROUP = "group"  # Requires approval from group


class ApprovalPriority(Enum):
    """Priority of approval"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalVote:
    """Approval vote"""
    voter_id: str
    voter_name: Optional[str] = None
    vote: str = "approved"  # approved, rejected
    comment: Optional[str] = None
    voted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "voter_id": self.voter_id,
            "voter_name": self.voter_name,
            "vote": self.vote,
            "comment": self.comment,
            "voted_at": self.voted_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApprovalVote":
        return cls(
            voter_id=data.get("voter_id", ""),
            voter_name=data.get("voter_name"),
            vote=data.get("vote", "approved"),
            comment=data.get("comment"),
            voted_at=data.get("voted_at", datetime.now(timezone.utc).isoformat())
        )


@dataclass
class Approval(BaseModel):
    """
    Approval model representing a request for human confirmation of an action.
    
    Attributes:
        uaw_id: Unique UAW identifier
        title: Approval title
        description: Approval description
        approval_type: Type of approval
        status: Current approval status
        priority: Approval priority
        action: Action being approved
        resource_type: Type of resource being acted upon
        resource_id: UAW ID of resource being acted upon
        requested_by: UAW ID of person requesting approval
        requested_at: When approval was requested
        approvers: List of UAW IDs of people who can approve
        required_approvers: Number of approvals required
        votes: List of votes
        approved_at: When approval was granted
        approved_by: UAW ID of person who approved
        rejected_at: When approval was rejected
        rejected_by: UAW ID of person who rejected
        rejection_reason: Reason for rejection
        expires_at: When approval request expires
        conditions: Conditions that must be met for approval
        metadata: Additional metadata
        external_ids: IDs in external systems
        custom_fields: Custom approval fields
    """
    
    entity_type: ClassVar[EntityType] = EntityType.APPROVAL
    
    approval_type: ApprovalType = ApprovalType.EXPLICIT
    status: ApprovalStatus = ApprovalStatus.PENDING
    priority: ApprovalPriority = ApprovalPriority.MEDIUM
    
    action: str = ""
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    
    requested_by: Optional[str] = None
    requested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    approvers: List[str] = field(default_factory=list)
    required_approvers: int = 1
    votes: List[ApprovalVote] = field(default_factory=list)
    
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    rejected_at: Optional[str] = None
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    expires_at: Optional[str] = None
    
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # External system IDs
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.approvers, str):
            self.approvers = [self.approvers]
        if isinstance(self.votes, dict):
            self.votes = [ApprovalVote.from_dict(v) for v in self.votes.values()]
    
    def add_approver(self, person_id: str) -> None:
        """Add an approver"""
        if person_id not in self.approvers:
            self.approvers.append(person_id)
    
    def remove_approver(self, person_id: str) -> bool:
        """Remove an approver"""
        if person_id in self.approvers:
            self.approvers.remove(person_id)
            return True
        return False
    
    def add_vote(self, voter_id: str, voter_name: Optional[str] = None, vote: str = "approved", comment: Optional[str] = None) -> None:
        """Add a vote"""
        self.votes.append(ApprovalVote(
            voter_id=voter_id,
            voter_name=voter_name,
            vote=vote,
            comment=comment
        ))
        
        # Update status based on votes
        self._update_status()
    
    def _update_status(self) -> None:
        """Update approval status based on votes"""
        approved_votes = [v for v in self.votes if v.vote == "approved"]
        rejected_votes = [v for v in self.votes if v.vote == "rejected"]
        
        if len(approved_votes) >= self.required_approvers:
            self.status = ApprovalStatus.APPROVED
            self.approved_at = datetime.now(timezone.utc).isoformat()
            # Get the last approver
            if approved_votes:
                self.approved_by = approved_votes[-1].voter_id
        elif rejected_votes:
            self.status = ApprovalStatus.REJECTED
            self.rejected_at = datetime.now(timezone.utc).isoformat()
            self.rejected_by = rejected_votes[-1].voter_id
            self.rejection_reason = rejected_votes[-1].comment
    
    def add_external_id(self, system: str, external_id: str) -> None:
        """Add an external system ID"""
        self.external_ids[system] = external_id
    
    def get_external_id(self, system: str) -> Optional[str]:
        """Get external ID for a system"""
        return self.external_ids.get(system)
    
    def set_condition(self, key: str, value: Any) -> None:
        """Set a condition"""
        self.conditions[key] = value
    
    def get_condition(self, key: str, default: Any = None) -> Any:
        """Get a condition"""
        return self.conditions.get(key, default)
    
    def set_status(self, status: ApprovalStatus) -> None:
        """Set approval status"""
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field"""
        self.custom_fields[key] = value
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field"""
        return self.custom_fields.get(key, default)
    
    def is_pending(self) -> bool:
        """Check if approval is pending"""
        return self.status == ApprovalStatus.PENDING
    
    def is_approved(self) -> bool:
        """Check if approval is approved"""
        return self.status == ApprovalStatus.APPROVED
    
    def is_rejected(self) -> bool:
        """Check if approval is rejected"""
        return self.status == ApprovalStatus.REJECTED
    
    def is_expired(self) -> bool:
        """Check if approval is expired"""
        if self.expires_at:
            from datetime import datetime as dt
            expires = dt.fromisoformat(self.expires_at)
            now = dt.now(timezone.utc)
            if now > expires:
                self.status = ApprovalStatus.EXPIRED
                return True
        return False
    
    def has_required_approvals(self) -> bool:
        """Check if required number of approvals is met"""
        approved_votes = [v for v in self.votes if v.vote == "approved"]
        return len(approved_votes) >= self.required_approvers
    
    def get_approval_count(self) -> int:
        """Get number of approvals"""
        return len([v for v in self.votes if v.vote == "approved"])
    
    def get_rejection_count(self) -> int:
        """Get number of rejections"""
        return len([v for v in self.votes if v.vote == "rejected"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        result.update({
            "approval_type": self.approval_type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at,
            "approvers": self.approvers,
            "required_approvers": self.required_approvers,
            "votes": [v.to_dict() for v in self.votes],
            "approved_at": self.approved_at,
            "approved_by": self.approved_by,
            "rejected_at": self.rejected_at,
            "rejected_by": self.rejected_by,
            "rejection_reason": self.rejection_reason,
            "expires_at": self.expires_at,
            "conditions": self.conditions,
            "external_ids": self.external_ids,
            "custom_fields": self.custom_fields
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Approval":
        """Create from dictionary"""
        uaw_id = data.get("uaw_id")
        if isinstance(uaw_id, str):
            uaw_id = UAWIdentifier.from_string(uaw_id)
        
        # Parse votes
        votes = []
        for v_data in data.get("votes", []):
            votes.append(ApprovalVote.from_dict(v_data))
        
        return cls(
            uaw_id=uaw_id,
            name=data.get("name", ""),
            description=data.get("description"),
            approval_type=ApprovalType(data.get("approval_type", "explicit")),
            status=ApprovalStatus(data.get("status", "pending")),
            priority=ApprovalPriority(data.get("priority", "medium")),
            action=data.get("action", ""),
            resource_type=data.get("resource_type"),
            resource_id=data.get("resource_id"),
            requested_by=data.get("requested_by"),
            requested_at=data.get("requested_at", datetime.now(timezone.utc).isoformat()),
            approvers=data.get("approvers", []),
            required_approvers=data.get("required_approvers", 1),
            votes=votes,
            approved_at=data.get("approved_at"),
            approved_by=data.get("approved_by"),
            rejected_at=data.get("rejected_at"),
            rejected_by=data.get("rejected_by"),
            rejection_reason=data.get("rejection_reason"),
            expires_at=data.get("expires_at"),
            conditions=data.get("conditions", {}),
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
class ApprovalBuilder:
    """Builder for creating Approval instances"""
    
    action: str
    resource_type: str
    resource_id: str
    
    def with_title(self, title: str) -> "ApprovalBuilder":
        """Set title"""
        self._name = title
        return self
    
    def with_description(self, description: str) -> "ApprovalBuilder":
        """Set description"""
        self._description = description
        return self
    
    def with_type(self, approval_type: ApprovalType) -> "ApprovalBuilder":
        """Set approval type"""
        self._approval_type = approval_type
        return self
    
    def with_priority(self, priority: ApprovalPriority) -> "ApprovalBuilder":
        """Set priority"""
        self._priority = priority
        return self
    
    def with_requester(self, person_id: str) -> "ApprovalBuilder":
        """Set requester"""
        self._requested_by = person_id
        return self
    
    def with_approver(self, person_id: str) -> "ApprovalBuilder":
        """Add approver"""
        self._approvers = getattr(self, "_approvers", [])
        if person_id not in self._approvers:
            self._approvers.append(person_id)
        return self
    
    def with_required_count(self, count: int) -> "ApprovalBuilder":
        """Set required approvals count"""
        self._required_approvers = count
        return self
    
    def with_expiration(self, expires_at: str) -> "ApprovalBuilder":
        """Set expiration"""
        self._expires_at = expires_at
        return self
    
    def with_condition(self, key: str, value: Any) -> "ApprovalBuilder":
        """Add condition"""
        self._conditions = getattr(self, "_conditions", {})
        self._conditions[key] = value
        return self
    
    def with_external_id(self, system: str, external_id: str) -> "ApprovalBuilder":
        """Add external ID"""
        self._external_ids = getattr(self, "_external_ids", {})
        self._external_ids[system] = external_id
        return self
    
    def build(self) -> Approval:
        """Build Approval instance"""
        return Approval(
            uaw_id=Approval.generate_id(),
            name=getattr(self, "_name", f"Approval: {self.action}"),
            description=getattr(self, "_description", None),
            action=self.action,
            resource_type=self.resource_type,
            resource_id=self.resource_id,
            approval_type=getattr(self, "_approval_type", ApprovalType.EXPLICIT),
            priority=getattr(self, "_priority", ApprovalPriority.MEDIUM),
            requested_by=getattr(self, "_requested_by", None),
            approvers=getattr(self, "_approvers", []),
            required_approvers=getattr(self, "_required_approvers", 1),
            expires_at=getattr(self, "_expires_at", None),
            conditions=getattr(self, "_conditions", {}),
            external_ids=getattr(self, "_external_ids", {})
        )
