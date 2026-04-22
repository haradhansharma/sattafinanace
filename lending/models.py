import uuid

from django.db import models

from common.models import TenantMixin


class Lending(TenantMixin):
    """
    Lending model matching frontend Lending type.
    Tracks money lent to individuals with repayment tracking.
    """

    RELATIONSHIP_CHOICES = [
        ("family", "Family"),
        ("friend", "Friend"),
        ("colleague", "Colleague"),
        ("business", "Business"),
        ("other", "Other"),
    ]

    REPAYMENT_SCHEDULE_CHOICES = [
        ("lump_sum", "Lump Sum"),
        ("monthly", "Monthly"),
        ("weekly", "Weekly"),
        ("custom", "Custom"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("partially_repaid", "Partially Repaid"),
        ("fully_repaid", "Fully Repaid"),
        ("overdue", "Overdue"),
        ("defaulted", "Defaulted"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Borrower details
    borrower_name = models.CharField(max_length=255)
    borrower_phone = models.CharField(max_length=50, blank=True, default="")
    borrower_email = models.EmailField(blank=True, default="")
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)

    # Financial details
    principal_amount = models.BigIntegerField()
    current_balance = models.BigIntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_interest_amount = models.BigIntegerField(default=0)
    total_repayable_amount = models.BigIntegerField()
    total_repaid_amount = models.BigIntegerField(default=0)

    # Dates and schedule
    issued_date = models.DateField()
    due_date = models.DateField(blank=True, null=True)
    repayment_schedule = models.CharField(
        max_length=20, choices=REPAYMENT_SCHEDULE_CHOICES, blank=True, default=""
    )

    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    notes = models.TextField(blank=True, default="")
    tags = models.JSONField(default=list, blank=True)
    currency = models.CharField(max_length=10, default="BDT")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lendings"
        verbose_name = "Lending"
        verbose_name_plural = "Lendings"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Lending to {self.borrower_name} — {self.currency} {self.principal_amount}"
        )


class LendingPayment(TenantMixin):
    """
    Lending payment model — tracks individual repayments against a lending record.
    FK → Lending, scoped to owner via TenantMixin.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    lending = models.ForeignKey(
        Lending,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    amount = models.BigIntegerField()
    payment_date = models.DateField()
    payment_number = models.IntegerField(default=1)
    note = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lending_payments"
        verbose_name = "Lending Payment"
        verbose_name_plural = "Lending Payments"
        ordering = ["-payment_date", "-created_at"]

    def __str__(self):
        return f"Payment #{self.payment_number} — {self.amount} for {self.lending.borrower_name}"
