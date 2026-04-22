"""
Document Vault API endpoints for FinLife Personal Finance SaaS.

All endpoints require BearerAuth (JWT) and filter by request.user.
List endpoints use paginate_queryset from common.pagination.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from ninja import Router

from common.pagination import PaginatedResponse, PaginationSchema, paginate_queryset
from common.permissions import BearerAuth

from .models import DocumentVaultItem, DocumentVersion
from .schemas import (
    DocumentVaultItemCreate,
    DocumentVaultItemOut,
    DocumentVaultItemUpdate,
    DocumentVersionCreate,
    DocumentVersionOut,
    MessageOut,
)

router = Router(tags=["Document"])


# ==================== Field Mapping ====================
# camelCase schema key → snake_case model field

DOC_FIELDS = {
    "name": "name",
    "description": "description",
    "category": "category",
    "format": "format",
    "status": "status",
    "fileSize": "file_size",
    "fileName": "file_name",
    "folderId": "folder_id",
    "tags": "tags",
    "isFavorite": "is_favorite",
    "isImportant": "is_important",
    "reminderBeforeDays": "reminder_before_days",
    "linkedEntityId": "linked_entity_id",
    "linkedEntityType": "linked_entity_type",
    "sharedWith": "shared_with",
    "isEncrypted": "is_encrypted",
    "uploadedBy": "uploaded_by",
    "source": "source",
    "notes": "notes",
}

DATE_FIELDS = ("documentDate", "expiryDate")


# ==================== Helpers ====================


def _parse_date(d):
    """Parse a date from string or datetime."""
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


# ==================== Document CRUD ====================


@router.get("/", auth=BearerAuth(), response=PaginatedResponse[DocumentVaultItemOut])
async def list_documents(
    request,
    category: Optional[str] = None,
    status: Optional[str] = None,
    format: Optional[str] = None,
    search: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    folder_id: Optional[str] = None,
    pagination: PaginationSchema = PaginationSchema(),
):
    """List all documents for the authenticated user (paginated, filterable)."""
    qs = DocumentVaultItem.objects.filter(owner=request.user)
    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)
    if format:
        qs = qs.filter(format=format)
    if is_favorite is not None:
        qs = qs.filter(is_favorite=is_favorite)
    if folder_id:
        qs = qs.filter(folder_id=folder_id)
    if search:
        qs = qs.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(notes__icontains=search)
            | Q(file_name__icontains=search)
        )

    qs = qs.prefetch_related("versions")

    items, total, total_pages = paginate_queryset(
        qs, pagination.page, pagination.per_page
    )
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": total_pages,
    }


@router.post("/", auth=BearerAuth(), response={201: DocumentVaultItemOut})
async def create_document(request, data: DocumentVaultItemCreate):
    """Create a new document vault item."""
    payload = data.model_dump()

    # Map camelCase → snake_case for model fields
    create_fields = {}
    for schema_key, model_field in DOC_FIELDS.items():
        if schema_key in payload and payload[schema_key] is not None:
            create_fields[model_field] = payload[schema_key]

    # Handle date fields
    for date_key in DATE_FIELDS:
        if date_key in payload and payload[date_key] is not None:
            field_name = DOC_FIELDS.get(date_key)
            if field_name:
                create_fields[field_name] = _parse_date(payload[date_key])

    if "tags" not in create_fields:
        create_fields["tags"] = []

    doc = DocumentVaultItem.objects.create(owner=request.user, **create_fields)
    return 201, doc


@router.get("/{doc_id}/", auth=BearerAuth(), response=DocumentVaultItemOut)
async def get_document(request, doc_id: uuid.UUID):
    """Get a single document by ID with embedded versions."""
    doc = get_object_or_404(
        DocumentVaultItem.objects.prefetch_related("versions"),
        id=doc_id,
        owner=request.user,
    )
    return doc


@router.put("/{doc_id}/", auth=BearerAuth(), response=DocumentVaultItemOut)
async def update_document(request, doc_id: uuid.UUID, data: DocumentVaultItemUpdate):
    """Update a document vault item."""
    doc = get_object_or_404(DocumentVaultItem, id=doc_id, owner=request.user)
    payload = data.model_dump(exclude_unset=True)

    for schema_key, model_field in DOC_FIELDS.items():
        if schema_key in payload:
            setattr(doc, model_field, payload[schema_key])

    # Handle date fields
    for date_key in DATE_FIELDS:
        if date_key in payload and payload[date_key] is not None:
            field_name = DOC_FIELDS.get(date_key)
            if field_name:
                setattr(doc, field_name, _parse_date(payload[date_key]))

    doc.save()
    return doc


@router.delete("/{doc_id}/", auth=BearerAuth(), response=MessageOut)
async def delete_document(request, doc_id: uuid.UUID):
    """Delete a document vault item and all its versions."""
    doc = get_object_or_404(DocumentVaultItem, id=doc_id, owner=request.user)
    doc.delete()
    return {"message": "Document deleted successfully"}


# ==================== Toggle Actions ====================


@router.post(
    "/{doc_id}/toggle-favorite/", auth=BearerAuth(), response=DocumentVaultItemOut
)
async def toggle_favorite(request, doc_id: uuid.UUID):
    """Toggle the favorite status of a document."""
    doc = get_object_or_404(DocumentVaultItem, id=doc_id, owner=request.user)
    doc.is_favorite = not doc.is_favorite
    doc.save()
    return doc


@router.post(
    "/{doc_id}/toggle-important/", auth=BearerAuth(), response=DocumentVaultItemOut
)
async def toggle_important(request, doc_id: uuid.UUID):
    """Toggle the important status of a document."""
    doc = get_object_or_404(DocumentVaultItem, id=doc_id, owner=request.user)
    doc.is_important = not doc.is_important
    doc.save()
    return doc


@router.post("/{doc_id}/archive/", auth=BearerAuth(), response=DocumentVaultItemOut)
async def archive_document(request, doc_id: uuid.UUID):
    """Archive a document."""
    doc = get_object_or_404(DocumentVaultItem, id=doc_id, owner=request.user)
    doc.status = "archived"
    doc.save()
    return doc


# ==================== Version Endpoints ====================


@router.post(
    "/{doc_id}/versions/", auth=BearerAuth(), response={201: DocumentVersionOut}
)
async def create_document_version(
    request, doc_id: uuid.UUID, data: DocumentVersionCreate
):
    """Add a new version to a document."""
    with db_transaction.atomic():
        doc = get_object_or_404(DocumentVaultItem, id=doc_id, owner=request.user)

        version = DocumentVersion.objects.create(
            owner=request.user,
            document=doc,
            version_number=data.versionNumber,
            date=data.date,
            note=data.note or "",
            file_size=data.fileSize,
        )

        # Update the parent document's current version
        doc.current_version = data.versionNumber
        doc.file_size = data.fileSize
        doc.save()

    return 201, version


@router.get(
    "/{doc_id}/versions/",
    auth=BearerAuth(),
    response=PaginatedResponse[DocumentVersionOut],
)
async def list_document_versions(
    request,
    doc_id: uuid.UUID,
    pagination: PaginationSchema = PaginationSchema(),
):
    """List all versions of a document."""
    get_object_or_404(DocumentVaultItem, id=doc_id, owner=request.user)

    qs = DocumentVersion.objects.filter(
        owner=request.user, document_id=doc_id
    ).order_by("-version_number")

    items, total, total_pages = paginate_queryset(
        qs, pagination.page, pagination.per_page
    )
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": total_pages,
    }


@router.delete(
    "/{doc_id}/versions/{version_id}/", auth=BearerAuth(), response=MessageOut
)
async def delete_document_version(request, doc_id: uuid.UUID, version_id: uuid.UUID):
    """Delete a specific document version."""
    version = get_object_or_404(
        DocumentVersion, id=version_id, document_id=doc_id, owner=request.user
    )
    version.delete()
    return {"message": "Document version deleted successfully"}
