"""
Security Manager for UAW
Управление безопасностью, разрешениями и уровнями доступа
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Union
import hashlib
import secrets
import hmac


class PermissionLevel(Enum):
    """Permission levels for operations"""
    L0_READ_ONLY = auto()      # Read only operations
    L1_PREPARE = auto()        # Prepare changes, drafts
    L2_SUPERVISED = auto()      # Execute with confirmation
    L3_AUTOMATION = auto()     # Automated execution within limits
    L4_CRITICAL = auto()       # Critical operations requiring explicit approval


class ActionCategory(Enum):
    """Categories of actions for permission management"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    FINANCIAL = "financial"
    DEPLOYMENT = "deployment"


@dataclass
class PermissionRule:
    """Single permission rule"""
    action: str  # Specific action or pattern
    category: ActionCategory
    min_level: PermissionLevel
    max_level: Optional[PermissionLevel] = None
    requires_approval: bool = False
    requires_confirmation: bool = False
    allowed_for: Optional[List[str]] = None  # Specific users/roles
    denied_for: Optional[List[str]] = None  # Specific users/roles
    conditions: Optional[Dict[str, Any]] = None  # Additional conditions
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "category": self.category.value,
            "min_level": self.min_level.name,
            "max_level": self.max_level.name if self.max_level else None,
            "requires_approval": self.requires_approval,
            "requires_confirmation": self.requires_confirmation,
            "allowed_for": self.allowed_for,
            "denied_for": self.denied_for,
            "conditions": self.conditions
        }


@dataclass
class UserPermissions:
    """Permissions for a specific user"""
    user_id: str
    base_level: PermissionLevel
    specific_permissions: Dict[str, PermissionLevel] = field(default_factory=dict)
    roles: List[str] = field(default_factory=list)
    integration_permissions: Dict[str, PermissionLevel] = field(default_factory=dict)
    
    def get_effective_level(
        self,
        action: str,
        integration: Optional[str] = None
    ) -> PermissionLevel:
        """Get effective permission level for an action"""
        # Check specific permissions first
        if action in self.specific_permissions:
            return self.specific_permissions[action]
        
        # Check integration-specific permissions
        if integration and integration in self.integration_permissions:
            return self.integration_permissions[integration]
        
        return self.base_level


@dataclass
class AuditEvent:
    """Single audit event"""
    event_id: str
    timestamp: str
    event_type: str
    action: str
    user_id: Optional[str]
    resource_id: Optional[str]
    resource_type: Optional[str]
    integration: Optional[str]
    status: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SecurityManager:
    """
    Manages security, permissions, and access control for UAW.
    Implements principle of least privilege and separates concerns.
    """
    
    def __init__(self):
        # Default permission rules
        self._rules: Dict[str, PermissionRule] = {}
        
        # User permissions
        self._user_permissions: Dict[str, UserPermissions] = {}
        
        # Initialize default rules
        self._initialize_default_rules()
        
        # Audit log
        self._audit_log: List[AuditEvent] = []
    
    def _initialize_default_rules(self):
        """Initialize default permission rules"""
        # Read operations - L0
        self.add_rule(PermissionRule(
            action="*_read",
            category=ActionCategory.READ,
            min_level=PermissionLevel.L0_READ_ONLY,
            max_level=PermissionLevel.L4_CRITICAL
        ))
        
        self.add_rule(PermissionRule(
            action="*_search",
            category=ActionCategory.READ,
            min_level=PermissionLevel.L0_READ_ONLY
        ))
        
        self.add_rule(PermissionRule(
            action="*_get",
            category=ActionCategory.READ,
            min_level=PermissionLevel.L0_READ_ONLY
        ))
        
        self.add_rule(PermissionRule(
            action="*_list",
            category=ActionCategory.READ,
            min_level=PermissionLevel.L0_READ_ONLY
        ))
        
        # Write operations - L2
        self.add_rule(PermissionRule(
            action="*_create",
            category=ActionCategory.WRITE,
            min_level=PermissionLevel.L1_PREPARE,
            max_level=PermissionLevel.L3_AUTOMATION,
            requires_confirmation=True
        ))
        
        self.add_rule(PermissionRule(
            action="*_update",
            category=ActionCategory.WRITE,
            min_level=PermissionLevel.L1_PREPARE,
            max_level=PermissionLevel.L3_AUTOMATION,
            requires_confirmation=True
        ))
        
        self.add_rule(PermissionRule(
            action="*_write",
            category=ActionCategory.WRITE,
            min_level=PermissionLevel.L2_SUPERVISED,
            max_level=PermissionLevel.L3_AUTOMATION,
            requires_confirmation=True
        ))
        
        # Delete operations - L4
        self.add_rule(PermissionRule(
            action="*_delete",
            category=ActionCategory.DELETE,
            min_level=PermissionLevel.L4_CRITICAL,
            requires_approval=True,
            requires_confirmation=True
        ))
        
        self.add_rule(PermissionRule(
            action="*_remove",
            category=ActionCategory.DELETE,
            min_level=PermissionLevel.L4_CRITICAL,
            requires_approval=True,
            requires_confirmation=True
        ))
        
        # Admin operations - L4
        self.add_rule(PermissionRule(
            action="*_admin",
            category=ActionCategory.ADMIN,
            min_level=PermissionLevel.L4_CRITICAL,
            requires_approval=True
        ))
        
        # Financial operations - L4
        self.add_rule(PermissionRule(
            action="*_payment*",
            category=ActionCategory.FINANCIAL,
            min_level=PermissionLevel.L4_CRITICAL,
            requires_approval=True,
            requires_confirmation=True
        ))
        
        self.add_rule(PermissionRule(
            action="*_charge*",
            category=ActionCategory.FINANCIAL,
            min_level=PermissionLevel.L4_CRITICAL,
            requires_approval=True,
            requires_confirmation=True
        ))
        
        # Production deployment - L4
        self.add_rule(PermissionRule(
            action="deploy_production",
            category=ActionCategory.DEPLOYMENT,
            min_level=PermissionLevel.L4_CRITICAL,
            requires_approval=True,
            requires_confirmation=True
        ))
        
        self.add_rule(PermissionRule(
            action="deploy_staging",
            category=ActionCategory.DEPLOYMENT,
            min_level=PermissionLevel.L2_SUPERVISED,
            max_level=PermissionLevel.L3_AUTOMATION,
            requires_confirmation=True
        ))
        
        self.add_rule(PermissionRule(
            action="deploy_preview",
            category=ActionCategory.DEPLOYMENT,
            min_level=PermissionLevel.L2_SUPERVISED,
            max_level=PermissionLevel.L3_AUTOMATION
        ))
        
        # GitHub specific rules
        self.add_rule(PermissionRule(
            action="github_force_push",
            category=ActionCategory.WRITE,
            min_level=PermissionLevel.L4_CRITICAL,
            requires_approval=True
        ))
        
        self.add_rule(PermissionRule(
            action="github_delete_branch",
            category=ActionCategory.DELETE,
            min_level=PermissionLevel.L3_AUTOMATION,
            requires_confirmation=True
        ))
        
        self.add_rule(PermissionRule(
            action="github_delete_repo",
            category=ActionCategory.DELETE,
            min_level=PermissionLevel.L4_CRITICAL,
            requires_approval=True,
            requires_confirmation=True
        ))
    
    def add_rule(self, rule: PermissionRule) -> None:
        """Add a permission rule"""
        self._rules[rule.action] = rule
    
    def remove_rule(self, action: str) -> bool:
        """Remove a permission rule"""
        if action in self._rules:
            del self._rules[action]
            return True
        return False
    
    def get_rule(self, action: str) -> Optional[PermissionRule]:
        """Get rule for a specific action"""
        # Direct match
        if action in self._rules:
            return self._rules[action]
        
        # Pattern match (e.g., github_* matches github_create_issue)
        for rule_action, rule in self._rules.items():
            if rule_action.endswith("*"):
                prefix = rule_action[:-1]
                if action.startswith(prefix):
                    return rule
            elif "*_" in rule_action:
                # Match patterns like *_read
                parts = rule_action.split("*")
                if len(parts) == 2:
                    prefix = parts[0]
                    suffix = parts[1]
                    if action.startswith(prefix) and action.endswith(suffix):
                        return rule
        
        return None
    
    def get_permission_level(
        self,
        action: str,
        user_id: Optional[str] = None,
        integration: Optional[str] = None
    ) -> PermissionLevel:
        """
        Get required permission level for an action.
        
        Args:
            action: Action to check
            user_id: Optional user ID for user-specific permissions
            integration: Optional integration name
            
        Returns:
            Required permission level
        """
        rule = self.get_rule(action)
        if rule:
            return rule.min_level
        
        # Default to L2 for unknown actions
        return PermissionLevel.L2_SUPERVISED
    
    def check_permission(
        self,
        action: str,
        user_id: str,
        integration: Optional[str] = None
    ) -> Tuple[bool, PermissionLevel, Optional[str]]:
        """
        Check if user has permission for an action.
        
        Args:
            action: Action to check
            user_id: User ID
            integration: Optional integration name
            
        Returns:
            Tuple of (allowed, required_level, reason)
        """
        # Get user permissions
        user_perms = self._user_permissions.get(user_id)
        if not user_perms:
            return False, PermissionLevel.L0_READ_ONLY, "User not found"
        
        # Get required level
        required_level = self.get_permission_level(action, user_id, integration)
        
        # Get user's effective level
        effective_level = user_perms.get_effective_level(action, integration)
        
        # Check if user has required level
        level_order = list(PermissionLevel)
        user_index = level_order.index(effective_level)
        required_index = level_order.index(required_level)
        
        if user_index >= required_index:
            # Check additional conditions
            rule = self.get_rule(action)
            if rule:
                if rule.requires_approval:
                    return False, required_level, "Requires approval"
                if rule.requires_confirmation:
                    return False, required_level, "Requires confirmation"
                if rule.allowed_for and user_id not in rule.allowed_for:
                    return False, required_level, "User not in allowed list"
                if rule.denied_for and user_id in rule.denied_for:
                    return False, required_level, "User is in denied list"
            
            return True, required_level, None
        
        return False, required_level, "Insufficient permission level"
    
    def add_user(
        self,
        user_id: str,
        base_level: PermissionLevel = PermissionLevel.L0_READ_ONLY,
        roles: Optional[List[str]] = None
    ) -> UserPermissions:
        """Add a new user with default permissions"""
        perms = UserPermissions(
            user_id=user_id,
            base_level=base_level,
            roles=roles or []
        )
        self._user_permissions[user_id] = perms
        return perms
    
    def get_user_permissions(self, user_id: str) -> Optional[UserPermissions]:
        """Get permissions for a user"""
        return self._user_permissions.get(user_id)
    
    def set_user_level(
        self,
        user_id: str,
        level: PermissionLevel
    ) -> bool:
        """Set base permission level for a user"""
        if user_id not in self._user_permissions:
            return False
        self._user_permissions[user_id].base_level = level
        return True
    
    def grant_permission(
        self,
        user_id: str,
        action: str,
        level: PermissionLevel
    ) -> bool:
        """Grant specific permission for an action"""
        if user_id not in self._user_permissions:
            return False
        self._user_permissions[user_id].specific_permissions[action] = level
        return True
    
    def revoke_permission(
        self,
        user_id: str,
        action: str
    ) -> bool:
        """Revoke specific permission"""
        if user_id not in self._user_permissions:
            return False
        if action in self._user_permissions[user_id].specific_permissions:
            del self._user_permissions[user_id].specific_permissions[action]
            return True
        return False
    
    def add_role(self, user_id: str, role: str) -> bool:
        """Add a role to a user"""
        if user_id not in self._user_permissions:
            return False
        if role not in self._user_permissions[user_id].roles:
            self._user_permissions[user_id].roles.append(role)
            return True
        return False
    
    def remove_role(self, user_id: str, role: str) -> bool:
        """Remove a role from a user"""
        if user_id not in self._user_permissions:
            return False
        if role in self._user_permissions[user_id].roles:
            self._user_permissions[user_id].roles.remove(role)
            return True
        return False
    
    def generate_session_token(
        self,
        user_id: str,
        expiration_minutes: int = 60
    ) -> str:
        """Generate a session token for a user"""
        timestamp = datetime.now(timezone.utc).isoformat()
        random_bytes = secrets.token_hex(32)
        
        # Create token payload
        payload = f"{user_id}:{timestamp}:{random_bytes}"
        
        # Sign the token
        token = hmac.new(
            self._get_secret_key().encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{payload}:{token}"
    
    def verify_session_token(self, token: str) -> Optional[str]:
        """Verify a session token and return user ID if valid"""
        try:
            parts = token.split(":")
            if len(parts) < 4:
                return None
            
            payload = ":".join(parts[:3])
            signature = parts[3]
            
            # Verify signature
            expected_signature = hmac.new(
                self._get_secret_key().encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            user_id = parts[0]
            timestamp_str = parts[1]
            
            # Check expiration (60 minutes)
            timestamp = datetime.fromisoformat(timestamp_str)
            if (datetime.now(timezone.utc) - timestamp).total_seconds() > 3600:
                return None
            
            return user_id
            
        except Exception:
            return None
    
    def _get_secret_key(self) -> str:
        """Get or generate secret key"""
        if not hasattr(self, "_secret_key"):
            self._secret_key = secrets.token_hex(64)
        return self._secret_key
    
    def log_audit_event(
        self,
        event_type: str,
        action: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        integration: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditEvent:
        """Log an audit event"""
        event_id = f"audit_{len(self._audit_log) + 1}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            action=action,
            user_id=user_id,
            resource_id=resource_id,
            resource_type=resource_type,
            integration=integration,
            status=status,
            details=details or {},
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self._audit_log.append(event)
        
        # Keep only last 1000 events
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]
        
        return event
    
    def get_audit_log(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[AuditEvent]:
        """Get audit log entries with optional filtering"""
        log = self._audit_log
        
        if event_type:
            log = [e for e in log if e.event_type == event_type]
        
        if user_id:
            log = [e for e in log if e.user_id == user_id]
        
        if severity:
            log = [e for e in log if e.severity == severity]
        
        return log[-limit:] if limit else log
    
    def get_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        return {
            "total_rules": len(self._rules),
            "total_users": len(self._user_permissions),
            "audit_events": len(self._audit_log),
            "by_level": {
                level.name: len([
                    p for p in self._user_permissions.values()
                    if p.base_level == level
                ]) for level in PermissionLevel
            }
        }
