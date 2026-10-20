"""
Document Model for UAW
Модель документа, файла, презентации или диаграммы
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

from .base import BaseModel, EntityType, UAWIdentifier


class DocumentType(Enum):
    """Type of document"""
    TEXT = "text"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    PDF = "pdf"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CODE = "code"
    DIAGRAM = "diagram"
    DESIGN = "design"


class DocumentStatus(Enum):
    """Status of a document"""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DocumentVisibility(Enum):
    """Visibility of a document"""
    PUBLIC = "public"
    PRIVATE = "private"
    SHARED = "shared"
    INTERNAL = "internal"


@dataclass
class DocumentVersion:
    """Document version"""
    version_number: str
    created_at: str
    created_by: Optional[str] = None
    description: Optional[str] = None
    is_current: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_number": self.version_number,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "description": self.description,
            "is_current": self.is_current
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentVersion":
        return cls(
            version_number=data.get("version_number", ""),
            created_at=data.get("created_at", ""),
            created_by=data.get("created_by"),
            description=data.get("description"),
            is_current=data.get("is_current", False)
        )


@dataclass
class DocumentComment:
    """Document comment"""
    comment_id: str
    content: str
    created_at: str
    created_by: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "content": self.content,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentComment":
        return cls(
            comment_id=data.get("comment_id", ""),
            content=data.get("content", ""),
            created_at=data.get("created_at", ""),
            created_by=data.get("created_by"),
            resolved=data.get("resolved", False),
            resolved_at=data.get("resolved_at")
        )


@dataclass
class Document(BaseModel):
    """
    Document model representing a document, file, or content.
    
    Attributes:
        uaw_id: Unique UAW identifier
        title: Document title
        document_type: Type of document
        status: Current document status
        visibility: Document visibility
        content: Document content (or reference to content)
        content_url: URL to access content
        file_path: Path to file if applicable
        file_size: Size of file in bytes
        mime_type: MIME type of document
        author_id: UAW ID of document author
        owner_id: UAW ID of document owner
        project_id: UAW ID of related project
        issue_id: UAW ID of related issue
        task_id: UAW ID of related task
        repository_id: UAW ID of related repository
        parent_document_id: UAW ID of parent document
        children: List of child document IDs
        versions: List of document versions
        comments: List of document comments
        tags: List of tags
        metadata: Document metadata
        external_ids: IDs in external systems
        custom_fields: Custom document fields
    """
    
    entity_type: ClassVar[EntityType] = EntityType.DOCUMENT
    
    document_type: DocumentType = DocumentType.TEXT
    status: DocumentStatus = DocumentStatus.DRAFT
    visibility: DocumentVisibility = DocumentVisibility.PRIVATE
    
    content: Optional[str] = None
    content_url: Optional[str] = None
    file_path: Optional[str] = None
    file_size: int = 0
    mime_type: Optional[str] = None
    
    author_id: Optional[str] = None
    owner_id: Optional[str] = None
    project_id: Optional[str] = None
    issue_id: Optional[str] = None
    task_id: Optional[str] = None
    repository_id: Optional[str] = None
    parent_document_id: Optional[str] = None
    
    children: List[str] = field(default_factory=list)
    versions: List[DocumentVersion] = field(default_factory=list)
    comments: List[DocumentComment] = field(default_factory=list)
    
    # External system IDs
    external_ids: Dict[str, str] = field(default_factory=dict)
    
    # Custom fields
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.children, str):
            self.children = [self.children]
        if isinstance(self.versions, dict):
            self.versions = [DocumentVersion.from_dict(v) for v in self.versions.values()]
        if isinstance(self.comments, dict):
            self.comments = [DocumentComment.from_dict(c) for c in self.comments.values()]
    
    def add_child(self, document_id: str) -> None:
        """Add a child document"""
        if document_id not in self.children:
            self.children.append(document_id)
    
    def remove_child(self, document_id: str) -> bool:
        """Remove a child document"""
        if document_id in self.children:
            self.children.remove(document_id)
            return True
        return False
    
    def add_version(self, version: DocumentVersion) -> None:
        """Add a version"""
        # Mark old versions as not current
        for v in self.versions:
            v.is_current = False
        version.is_current = True
        self.versions.append(version)
    
    def get_current_version(self) -> Optional[DocumentVersion]:
        """Get current version"""
        for v in self.versions:
            if v.is_current:
                return v
        return None
    
    def add_comment(self, comment: DocumentComment) -> None:
        """Add a comment"""
        self.comments.append(comment)
    
    def add_external_id(self, system: str, external_id: str) -> None:
        """Add an external system ID"""
        self.external_ids[system] = external_id
    
    def get_external_id(self, system: str) -> Optional[str]:
        """Get external ID for a system"""
        return self.external_ids.get(system)
    
    def set_status(self, status: DocumentStatus) -> None:
        """Set document status"""
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_visibility(self, visibility: DocumentVisibility) -> None:
        """Set document visibility"""
        self.visibility = visibility
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_content(self, content: str, content_url: Optional[str] = None) -> None:
        """Set document content"""
        self.content = content
        self.content_url = content_url
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def set_custom_field(self, key: str, value: Any) -> None:
        """Set a custom field"""
        self.custom_fields[key] = value
    
    def get_custom_field(self, key: str, default: Any = None) -> Any:
        """Get a custom field"""
        return self.custom_fields.get(key, default)
    
    def is_published(self) -> bool:
        """Check if document is published"""
        return self.status == DocumentStatus.PUBLISHED
    
    def is_draft(self) -> bool:
        """Check if document is a draft"""
        return self.status == DocumentStatus.DRAFT
    
    def has_children(self) -> bool:
        """Check if document has children"""
        return len(self.children) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        result.update({
            "document_type": self.document_type.value,
            "status": self.status.value,
            "visibility": self.visibility.value,
            "content": self.content,
            "content_url": self.content_url,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "author_id": self.author_id,
            "owner_id": self.owner_id,
            "project_id": self.project_id,
            "issue_id": self.issue_id,
            "task_id": self.task_id,
            "repository_id": self.repository_id,
            "parent_document_id": self.parent_document_id,
            "children": self.children,
            "versions": [v.to_dict() for v in self.versions],
            "comments": [c.to_dict() for c in self.comments],
            "external_ids": self.external_ids,
            "custom_fields": self.custom_fields
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create from dictionary"""
        uaw_id = data.get("uaw_id")
        if isinstance(uaw_id, str):
            uaw_id = UAWIdentifier.from_string(uaw_id)
        
        # Parse versions
        versions = []
        for v_data in data.get("versions", []):
            versions.append(DocumentVersion.from_dict(v_data))
        
        # Parse comments
        comments = []
        for c_data in data.get("comments", []):
            comments.append(DocumentComment.from_dict(c_data))
        
        return cls(
            uaw_id=uaw_id,
            name=data.get("name", ""),
            description=data.get("description"),
            document_type=DocumentType(data.get("document_type", "text")),
            status=DocumentStatus(data.get("status", "draft")),
            visibility=DocumentVisibility(data.get("visibility", "private")),
            content=data.get("content"),
            content_url=data.get("content_url"),
            file_path=data.get("file_path"),
            file_size=data.get("file_size", 0),
            mime_type=data.get("mime_type"),
            author_id=data.get("author_id"),
            owner_id=data.get("owner_id"),
            project_id=data.get("project_id"),
            issue_id=data.get("issue_id"),
            task_id=data.get("task_id"),
            repository_id=data.get("repository_id"),
            parent_document_id=data.get("parent_document_id"),
            children=data.get("children", []),
            versions=versions,
            comments=comments,
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
    
    def get_notion_page_id(self) -> Optional[str]:
        """Get Notion page ID if available"""
        return self.external_ids.get("notion")
    
    def get_box_file_id(self) -> Optional[str]:
        """Get Box file ID if available"""
        return self.external_ids.get("box")
    
    def get_google_drive_id(self) -> Optional[str]:
        """Get Google Drive file ID if available"""
        return self.external_ids.get("google_drive")
    
    def get_figma_file_key(self) -> Optional[str]:
        """Get Figma file key if available"""
        return self.external_ids.get("figma")


@dataclass
class DocumentBuilder:
    """Builder for creating Document instances"""
    
    name: str
    document_type: DocumentType = DocumentType.TEXT
    
    def with_description(self, description: str) -> "DocumentBuilder":
        """Set description"""
        self._description = description
        return self
    
    def with_content(self, content: str, content_url: Optional[str] = None) -> "DocumentBuilder":
        """Set content"""
        self._content = content
        self._content_url = content_url
        return self
    
    def with_file_info(
        self,
        file_path: str,
        file_size: int = 0,
        mime_type: Optional[str] = None
    ) -> "DocumentBuilder":
        """Set file information"""
        self._file_path = file_path
        self._file_size = file_size
        self._mime_type = mime_type
        return self
    
    def with_author(self, author_id: str) -> "DocumentBuilder":
        """Set author"""
        self._author_id = author_id
        return self
    
    def with_project(self, project_id: str) -> "DocumentBuilder":
        """Set related project"""
        self._project_id = project_id
        return self
    
    def with_external_id(self, system: str, external_id: str) -> "DocumentBuilder":
        """Add external ID"""
        self._external_ids = getattr(self, "_external_ids", {})
        self._external_ids[system] = external_id
        return self
    
    def build(self) -> Document:
        """Build Document instance"""
        return Document(
            uaw_id=Document.generate_id(),
            name=self.name,
            description=getattr(self, "_description", None),
            document_type=self.document_type,
            content=getattr(self, "_content", None),
            content_url=getattr(self, "_content_url", None),
            file_path=getattr(self, "_file_path", None),
            file_size=getattr(self, "_file_size", 0),
            mime_type=getattr(self, "_mime_type", None),
            author_id=getattr(self, "_author_id", None),
            project_id=getattr(self, "_project_id", None),
            external_ids=getattr(self, "_external_ids", {})
        )
