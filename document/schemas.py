"""
Document Vault schemas for FinLife Personal Finance SaaS.

All schemas use camelCase field names matching the frontend TypeScript interfaces.
"""

from datetime import date
from typing import List, Optional

from ninja import Schema


# ==================== Message ====================


class MessageOut(Schema):
    """Generic message response."""

    message: str


# ==================== DocumentVersion Schemas ====================


class DocumentVersionOut(Schema):
    """Version output matching frontend DocumentVersion interface."""

    id: str
    versionNumber: int
    date: str
    note: Optional[str] = None
    fileSize: int

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_date(obj):
        return obj.date.isoformat() if obj.date else ""

    @staticmethod
    def resolve_fileSize(obj):
        return obj.file_size


class DocumentVersionCreate(Schema):
    """Create a document version."""

    versionNumber: int
    date: date
    note: Optional[str] = None
    fileSize: int = 0


# ==================== DocumentVaultItem Schemas ====================


class DocumentVaultItemOut(Schema):
    """Full document output matching frontend DocumentVaultItem interface."""

    id: str
    name: str
    description: Optional[str] = None
    category: str
    format: str
    status: str
    fileSize: int
    filePath: Optional[str] = None
    fileName: Optional[str] = None
    folderId: Optional[str] = None
    tags: List[str] = []
    isFavorite: bool
    isImportant: bool
    documentDate: Optional[str] = None
    expiryDate: Optional[str] = None
    reminderBeforeDays: Optional[int] = None
    linkedEntityId: Optional[str] = None
    linkedEntityType: Optional[str] = None
    currentVersion: int
    # Embedded related objects
    versions: List[DocumentVersionOut] = []
    sharedWith: Optional[str] = None
    isEncrypted: bool
    uploadedBy: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    createdAt: str
    updatedAt: str

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_filePath(obj):
        return obj.file_path.url if obj.file_path else None

    @staticmethod
    def resolve_documentDate(obj):
        return obj.document_date.isoformat() if obj.document_date else None

    @staticmethod
    def resolve_expiryDate(obj):
        return obj.expiry_date.isoformat() if obj.expiry_date else None

    @staticmethod
    def resolve_versions(obj):
        return list(obj.versions.all())

    @staticmethod
    def resolve_createdAt(obj):
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj):
        return obj.updated_at.isoformat()


class DocumentVaultItemCreate(Schema):
    """Create a document vault item."""

    name: str
    description: Optional[str] = None
    category: str = "other"
    format: str = "pdf"
    status: str = "active"
    fileSize: int = 0
    fileName: Optional[str] = None
    folderId: Optional[str] = None
    tags: Optional[List[str]] = None
    isFavorite: bool = False
    isImportant: bool = False
    documentDate: Optional[date] = None
    expiryDate: Optional[date] = None
    reminderBeforeDays: Optional[int] = None
    linkedEntityId: Optional[str] = None
    linkedEntityType: Optional[str] = None
    sharedWith: Optional[str] = None
    isEncrypted: bool = False
    uploadedBy: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class DocumentVaultItemUpdate(Schema):
    """Update a document vault item — all fields optional."""

    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    format: Optional[str] = None
    status: Optional[str] = None
    fileSize: Optional[int] = None
    fileName: Optional[str] = None
    folderId: Optional[str] = None
    tags: Optional[List[str]] = None
    isFavorite: Optional[bool] = None
    isImportant: Optional[bool] = None
    documentDate: Optional[date] = None
    expiryDate: Optional[date] = None
    reminderBeforeDays: Optional[int] = None
    linkedEntityId: Optional[str] = None
    linkedEntityType: Optional[str] = None
    sharedWith: Optional[str] = None
    isEncrypted: Optional[bool] = None
    uploadedBy: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
