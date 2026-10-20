"""
Resource Mapping for UAW
Сопоставление ресурсов между различными сервисами
"""

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum


class ResourceType(Enum):
    """Types of resources that can be mapped"""
    PERSON = "person"
    TEAM = "team"
    PROJECT = "project"
    TASK = "task"
    ISSUE = "issue"
    REPOSITORY = "repository"
    DEPLOYMENT = "deployment"
    DOCUMENT = "document"
    EVENT = "event"
    WORKFLOW = "workflow"


class SourceSystem(Enum):
    """Source systems for resources"""
    UAW = "uaw"
    GITHUB = "github"
    ASANA = "asana"
    LINEAR = "linear"
    SLACK = "slack"
    GOOGLE_CALENDAR = "google_calendar"
    OUTLOOK_CALENDAR = "outlook_calendar"
    NETLIFY = "netlify"
    VERCEL = "vercel"
    NOTION = "notion"
    BOX = "box"
    GOOGLE_DRIVE = "google_drive"
    SHAREPOINT = "sharepoint"
    MICROSOFT_TEAMS = "microsoft_teams"
    CALENDLY = "calendly"
    GAMMA = "gamma"
    CANVA = "canva"
    EXCALIDRAW = "excalidraw"
    FIGMA = "figma"
    WIX = "wix"


@dataclass
class ResourceReference:
    """Reference to a resource in a specific system"""
    system: SourceSystem
    resource_id: str
    resource_type: ResourceType
    url: Optional[str] = None
    name: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "system": self.system.value,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type.value,
            "url": self.url,
            "name": self.name,
            "additional_data": self.additional_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceReference":
        return cls(
            system=SourceSystem(data["system"]),
            resource_id=data["resource_id"],
            resource_type=ResourceType(data["resource_type"]),
            url=data.get("url"),
            name=data.get("name"),
            additional_data=data.get("additional_data", {})
        )


@dataclass
class ResourceMapping:
    """
    Mapping between resources across different systems.
    Allows tracking relationships between objects in different services.
    """
    uaw_id: str
    resource_type: ResourceType
    primary_system: SourceSystem
    primary_id: str
    references: Dict[SourceSystem, ResourceReference] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sync_status: str = "synced"
    last_sync: Optional[str] = None
    
    def add_reference(self, reference: ResourceReference) -> None:
        """Add a reference to another system"""
        self.references[reference.system] = reference
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def get_reference(self, system: SourceSystem) -> Optional[ResourceReference]:
        """Get reference for a specific system"""
        return self.references.get(system)
    
    def remove_reference(self, system: SourceSystem) -> bool:
        """Remove reference for a specific system"""
        if system in self.references:
            del self.references[system]
            self.updated_at = datetime.now(timezone.utc).isoformat()
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uaw_id": self.uaw_id,
            "resource_type": self.resource_type.value,
            "primary_system": self.primary_system.value,
            "primary_id": self.primary_id,
            "references": {
                system.value: ref.to_dict()
                for system, ref in self.references.items()
            },
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "sync_status": self.sync_status,
            "last_sync": self.last_sync
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceMapping":
        mapping = cls(
            uaw_id=data["uaw_id"],
            resource_type=ResourceType(data["resource_type"]),
            primary_system=SourceSystem(data["primary_system"]),
            primary_id=data["primary_id"],
            metadata=data.get("metadata", {}),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            sync_status=data.get("sync_status", "synced"),
            last_sync=data.get("last_sync")
        )
        
        for system_str, ref_data in data.get("references", {}).items():
            system = SourceSystem(system_str)
            ref = ResourceReference.from_dict(ref_data)
            mapping.references[system] = ref
        
        return mapping


class ResourceMapper:
    """
    Manages resource mappings across different systems.
    Provides methods to create, retrieve, and manage mappings.
    """
    
    def __init__(self, state_manager: Optional[Any] = None):
        self.state_manager = state_manager
        self._mappings: Dict[str, ResourceMapping] = {}
        
        # Load existing mappings if state manager is available
        if self.state_manager:
            self._load_mappings()
    
    def _load_mappings(self):
        """Load mappings from state manager"""
        if not self.state_manager:
            return
        
        entries = self.state_manager.list_entries()
        for entry in entries:
            if entry.state_type.value == "resource_mapping":
                mapping = ResourceMapping.from_dict(entry.value)
                self._mappings[mapping.uaw_id] = mapping
    
    def _save_mapping(self, mapping: ResourceMapping):
        """Save mapping to state manager"""
        if self.state_manager:
            self.state_manager.save_resource_mapping(
                mapping.uaw_id,
                mapping.to_dict()
            )
    
    def create_mapping(
        self,
        resource_type: ResourceType,
        primary_system: SourceSystem,
        primary_id: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ResourceMapping:
        """
        Create a new resource mapping.
        
        Args:
            resource_type: Type of resource
            primary_system: Primary system for this resource
            primary_id: ID in primary system
            name: Optional name
            metadata: Optional metadata
            
        Returns:
            Created ResourceMapping
        """
        uaw_id = f"{resource_type.value}_{uuid.uuid4().hex[:12]}"
        
        mapping = ResourceMapping(
            uaw_id=uaw_id,
            resource_type=resource_type,
            primary_system=primary_system,
            primary_id=primary_id,
            metadata=metadata or {},
            sync_status="created"
        )
        
        # Add primary reference
        primary_ref = ResourceReference(
            system=primary_system,
            resource_id=primary_id,
            resource_type=resource_type,
            name=name
        )
        mapping.add_reference(primary_ref)
        
        self._mappings[uaw_id] = mapping
        self._save_mapping(mapping)
        
        return mapping
    
    def add_reference(
        self,
        mapping_id: str,
        system: SourceSystem,
        resource_id: str,
        resource_type: Optional[ResourceType] = None,
        url: Optional[str] = None,
        name: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a reference to an existing mapping.
        
        Args:
            mapping_id: UAW mapping ID
            system: Source system
            resource_id: Resource ID in that system
            resource_type: Resource type (defaults to mapping's type)
            url: Optional URL
            name: Optional name
            additional_data: Optional additional data
            
        Returns:
            True if successful
        """
        if mapping_id not in self._mappings:
            return False
        
        mapping = self._mappings[mapping_id]
        
        if resource_type is None:
            resource_type = mapping.resource_type
        
        ref = ResourceReference(
            system=system,
            resource_id=resource_id,
            resource_type=resource_type,
            url=url,
            name=name,
            additional_data=additional_data or {}
        )
        
        mapping.add_reference(ref)
        self._save_mapping(mapping)
        
        return True
    
    def get_mapping(self, mapping_id: str) -> Optional[ResourceMapping]:
        """Get a mapping by UAW ID"""
        return self._mappings.get(mapping_id)
    
    def get_by_system_id(
        self,
        system: SourceSystem,
        resource_id: str
    ) -> Optional[ResourceMapping]:
        """Find mapping by system and resource ID"""
        for mapping in self._mappings.values():
            if resource_id in [
                ref.resource_id for ref in mapping.references.values()
                if ref.system == system
            ]:
                return mapping
        return None
    
    def get_by_type(self, resource_type: ResourceType) -> List[ResourceMapping]:
        """Get all mappings of a specific type"""
        return [
            mapping for mapping in self._mappings.values()
            if mapping.resource_type == resource_type
        ]
    
    def get_all_mappings(self) -> List[ResourceMapping]:
        """Get all mappings"""
        return list(self._mappings.values())
    
    def update_mapping(
        self,
        mapping_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        sync_status: Optional[str] = None
    ) -> bool:
        """Update mapping metadata or status"""
        if mapping_id not in self._mappings:
            return False
        
        mapping = self._mappings[mapping_id]
        
        if metadata:
            mapping.metadata.update(metadata)
        if sync_status:
            mapping.sync_status = sync_status
            mapping.last_sync = datetime.now(timezone.utc).isoformat()
        
        mapping.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_mapping(mapping)
        
        return True
    
    def delete_mapping(self, mapping_id: str) -> bool:
        """Delete a mapping"""
        if mapping_id not in self._mappings:
            return False
        
        del self._mappings[mapping_id]
        
        if self.state_manager:
            self.state_manager.delete(f"mapping_{mapping_id}")
        
        return True
    
    def sync_mapping(self, mapping_id: str) -> bool:
        """
        Mark a mapping as synced.
        This would typically trigger actual sync operations.
        """
        if mapping_id not in self._mappings:
            return False
        
        mapping = self._mappings[mapping_id]
        mapping.sync_status = "synced"
        mapping.last_sync = datetime.now(timezone.utc).isoformat()
        mapping.updated_at = datetime.now(timezone.utc).isoformat()
        
        self._save_mapping(mapping)
        return True
    
    def create_person_mapping(
        self,
        primary_system: SourceSystem,
        primary_id: str,
        name: str,
        email: Optional[str] = None
    ) -> ResourceMapping:
        """Create mapping for a person"""
        mapping = self.create_mapping(
            ResourceType.PERSON,
            primary_system,
            primary_id,
            name=name,
            metadata={"email": email} if email else {}
        )
        return mapping
    
    def create_project_mapping(
        self,
        primary_system: SourceSystem,
        primary_id: str,
        name: str,
        description: Optional[str] = None
    ) -> ResourceMapping:
        """Create mapping for a project"""
        mapping = self.create_mapping(
            ResourceType.PROJECT,
            primary_system,
            primary_id,
            name=name,
            metadata={"description": description} if description else {}
        )
        return mapping
    
    def create_task_mapping(
        self,
        primary_system: SourceSystem,
        primary_id: str,
        title: str,
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None
    ) -> ResourceMapping:
        """Create mapping for a task"""
        mapping = self.create_mapping(
            ResourceType.TASK,
            primary_system,
            primary_id,
            name=title,
            metadata={
                "project_id": project_id,
                "assignee_id": assignee_id
            }
        )
        return mapping
    
    def link_github_asana(
        self,
        github_owner: str,
        github_repo: str,
        github_issue_number: int,
        asana_task_id: str,
        title: str
    ) -> ResourceMapping:
        """
        Create mapping between GitHub issue and Asana task.
        
        Args:
            github_owner: GitHub repository owner
            github_repo: GitHub repository name
            github_issue_number: GitHub issue number
            asana_task_id: Asana task GID
            title: Issue/task title
            
        Returns:
            ResourceMapping linking both resources
        """
        # Create mapping with GitHub as primary
        mapping = self.create_mapping(
            ResourceType.ISSUE,
            SourceSystem.GITHUB,
            f"{github_owner}/{github_repo}#{github_issue_number}",
            name=title
        )
        
        # Add GitHub reference
        github_ref = ResourceReference(
            system=SourceSystem.GITHUB,
            resource_id=f"{github_owner}/{github_repo}#{github_issue_number}",
            resource_type=ResourceType.ISSUE,
            url=f"https://github.com/{github_owner}/{github_repo}/issues/{github_issue_number}",
            name=title,
            additional_data={
                "owner": github_owner,
                "repo": github_repo,
                "issue_number": github_issue_number
            }
        )
        mapping.add_reference(github_ref)
        
        # Add Asana reference
        asana_ref = ResourceReference(
            system=SourceSystem.ASANA,
            resource_id=asana_task_id,
            resource_type=ResourceType.TASK,
            url=f"https://app.asana.com/0/0/{asana_task_id}/f",
            name=title
        )
        mapping.add_reference(asana_ref)
        
        self._save_mapping(mapping)
        return mapping
    
    def find_related_resources(
        self,
        mapping_id: str
    ) -> Dict[SourceSystem, ResourceReference]:
        """Find all resources related to a mapping"""
        mapping = self.get_mapping(mapping_id)
        if not mapping:
            return {}
        return mapping.references
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mapping statistics"""
        return {
            "total_mappings": len(self._mappings),
            "by_type": {
                resource_type.value: len([
                    m for m in self._mappings.values()
                    if m.resource_type == resource_type
                ]) for resource_type in ResourceType
            },
            "by_system": {
                system.value: len([
                    m for m in self._mappings.values()
                    if m.primary_system == system
                ]) for system in SourceSystem
            }
        }
