"""
Document Vault models for FinLife Personal Finance SaaS.

Every model inherits from TenantMixin (common.models) which provides
the `owner` FK for multi-tenant isolation.
"""

import uuid

from django.db import models

from common.models import TenantMixin


class DocumentVaultItem(TenantMixin):
    """
    Document vault item matching the frontend DocumentVaultItem interface.

    Frontend fields: id, createdAt, updatedAt, name, description, category,
    format, status, fileSize, filePath, fileName, folderId, tags,
    isFavorite, isImportant, documentDate, expiryDate, reminderBeforeDays,
    linkedEntityId, linkedEntityType, currentVersion, sharedWith,
    isEncrypted, uploadedBy, source, notes
    """

    class Category(models.TextChoices):
        TAX_RETURN = "tax_return", "Tax Return"
        INSURANCE_POLICY = "insurance_policy", "Insurance Policy"
        PROPERTY_DEED = "property_deed", "Property Deed"
        BANK_STATEMENT = "bank_statement", "Bank Statement"
        INVESTMENT_STATEMENT = "investment_statement", "Investment Statement"
        LOAN_DOCUMENT = "loan_document", "Loan Document"
        CONTRACT = "contract", "Contract"
        RECEIPT = "receipt", "Receipt"
        INVOICE = "invoice", "Invoice"
        ID_PROOF = "id_proof", "ID Proof"
        MEDICAL_RECORD = "medical_record", "Medical Record"
        EDUCATION_CERTIFICATE = "education_certificate", "Education Certificate"
        VEHICLE_REGISTRATION = "vehicle_registration", "Vehicle Registration"
        OTHER = "other", "Other"

    class Format(models.TextChoices):
        PDF = "pdf", "PDF"
        DOC = "doc", "DOC"
        DOCX = "docx", "DOCX"
        XLS = "xls", "XLS"
        XLSX = "xlsx", "XLSX"
        JPG = "jpg", "JPG"
        JPEG = "jpeg", "JPEG"
        PNG = "png", "PNG"
        CSV = "csv", "CSV"
        TXT = "txt", "TXT"
        ZIP = "zip", "ZIP"
        OTHER = "other", "Other"

    class DocumentStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        ARCHIVED = "archived", "Archived"
        DRAFT = "draft", "Draft"

    class LinkedEntityType(models.TextChoices):
        INSURANCE = "insurance", "Insurance"
        LOAN = "loan", "Loan"
        MORTGAGE = "mortgage", "Mortgage"
        ASSET = "asset", "Asset"
        INVESTMENT = "investment", "Investment"
        LENDING = "lending", "Lending"
        INVOICE = "invoice", "Invoice"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    category = models.CharField(
        max_length=30, choices=Category.choices, default=Category.OTHER
    )
    format = models.CharField(max_length=10, choices=Format.choices, default=Format.PDF)
    status = models.CharField(
        max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.ACTIVE
    )
    file_size = models.BigIntegerField(default=0)
    file_path = models.FileField(upload_to="documents/", null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True, default="")
    folder_id = models.CharField(max_length=36, blank=True, default="")
    tags = models.JSONField(default=list, blank=True)
    is_favorite = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    document_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    reminder_before_days = models.IntegerField(null=True, blank=True)
    linked_entity_id = models.CharField(max_length=36, blank=True, default="")
    linked_entity_type = models.CharField(
        max_length=50,
        choices=LinkedEntityType.choices,
        blank=True,
        default="",
    )
    current_version = models.IntegerField(default=1)
    shared_with = models.CharField(max_length=255, blank=True, default="")
    is_encrypted = models.BooleanField(default=False)
    uploaded_by = models.CharField(max_length=255, blank=True, default="")
    source = models.CharField(max_length=255, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Document Vault Item"
        verbose_name_plural = "Document Vault Items"

    def __str__(self):
        return f"{self.name} — {self.get_category_display()}"


class DocumentVersion(TenantMixin):
    """
    Version record linked to a DocumentVaultItem.

    Frontend fields: versionNumber, date, note, fileSize
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        DocumentVaultItem,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version_number = models.IntegerField(default=1)
    date = models.DateField()
    note = models.TextField(blank=True, default="")
    file_size = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-version_number"]
        verbose_name = "Document Version"
        verbose_name_plural = "Document Versions"

    def __str__(self):
        return f"v{self.version_number} of {self.document.name}"
