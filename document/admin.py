"""
Django admin configuration for Document Vault models.
"""

from django.contrib import admin

from .models import DocumentVaultItem, DocumentVersion


class DocumentVersionInline(admin.TabularInline):
    """Inline for document versions on the document detail page."""

    model = DocumentVersion
    extra = 1
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(DocumentVaultItem)
class DocumentVaultItemAdmin(admin.ModelAdmin):
    """Admin for DocumentVaultItem model."""

    list_display = (
        "id",
        "name",
        "category",
        "format",
        "status",
        "file_size",
        "is_favorite",
        "is_important",
        "is_encrypted",
        "current_version",
        "owner",
        "created_at",
    )
    list_filter = (
        "category",
        "format",
        "status",
        "is_favorite",
        "is_important",
        "is_encrypted",
    )
    search_fields = (
        "name",
        "description",
        "file_name",
        "notes",
        "owner__email",
    )
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [DocumentVersionInline]


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    """Admin for DocumentVersion model."""

    list_display = (
        "id",
        "document",
        "version_number",
        "date",
        "file_size",
        "owner",
    )
    list_filter = ("version_number", "date")
    search_fields = ("document__name", "note", "owner__email")
    readonly_fields = ("id", "created_at", "updated_at")
