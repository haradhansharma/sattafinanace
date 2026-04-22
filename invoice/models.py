import uuid

from django.db import models

from common.models import TenantMixin


class Invoice(TenantMixin):
    """
    Invoice model matching frontend Invoice type.
    Supports 'sent' and 'received' invoices with line items.
    Auto-generates invoice number: INV-{year}-{sequential_number}.
    """

    TYPE_CHOICES = [
        ("sent", "Sent"),
        ("received", "Received"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("viewed", "Viewed"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # Client details
    client_name = models.CharField(max_length=255)
    client_email = models.EmailField(blank=True, default="")
    client_phone = models.CharField(max_length=50, blank=True, default="")
    client_address = models.TextField(blank=True, default="")

    # Financials
    subtotal = models.BigIntegerField(default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.BigIntegerField(default=0)
    discount_amount = models.BigIntegerField(default=0)
    total_amount = models.BigIntegerField(default=0)

    currency = models.CharField(max_length=10, default="BDT")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Dates
    issue_date = models.DateField()
    due_date = models.DateField()
    paid_date = models.DateField(blank=True, null=True)

    # Metadata
    notes = models.TextField(blank=True, default="")
    bank_account_id = models.UUIDField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoices"
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.invoice_number} — {self.client_name}"


class InvoiceItem(models.Model):
    """
    Invoice line item — embedded in Invoice via FK.
    No owner FK or timestamps per frontend spec (NO BaseModel).
    Tenant isolation enforced through parent Invoice.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )

    description = models.TextField()
    quantity = models.IntegerField()
    unit_price = models.BigIntegerField()
    total = models.BigIntegerField()

    class Meta:
        db_table = "invoice_items"
        verbose_name = "Invoice Item"
        verbose_name_plural = "Invoice Items"
        ordering = ["id"]

    def __str__(self):
        return f"{self.description} (x{self.quantity})"
