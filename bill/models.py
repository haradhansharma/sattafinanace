"""
Bill tracking for FinLife Personal Finance SaaS.

Bill — recurring and one-time bill management with payment history.
BillPaymentHistory — lightweight FK child of Bill (no TenantMixin, no timestamps).
"""

import uuid

from django.db import models

from common.models import TenantMixin


class Bill(TenantMixin):
    """Track recurring / one-time bills with auto-pay, reminders, and linkage."""

    # --- Choices ---
    CATEGORY_CHOICES = [
        ("rent", "Rent"),
        ("utilities", "Utilities"),
        ("subscriptions", "Subscriptions"),
        ("loan_emi", "Loan EMI"),
        ("insurance_premium", "Insurance Premium"),
        ("credit_card", "Credit Card"),
        ("medical", "Medical"),
        ("education", "Education"),
        ("vehicle", "Vehicle"),
        ("service_contract", "Service Contract"),
        ("tax", "Tax"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("due_soon", "Due Soon"),
        ("overdue", "Overdue"),
        ("paid", "Paid"),
        ("skipped", "Skipped"),
        ("cancelled", "Cancelled"),
    ]
    RECURRENCE_CHOICES = [
        ("none", "None"),
        ("weekly", "Weekly"),
        ("biweekly", "Biweekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("semiannually", "Semiannually"),
        ("annually", "Annually"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]
    LINKED_ENTITY_TYPE_CHOICES = [
        ("loan", "Loan"),
        ("mortgage", "Mortgage"),
        ("insurance", "Insurance"),
        ("investment", "Investment"),
        ("card", "Card"),
        ("invoice", "Invoice"),
        ("calendar", "Calendar"),
        ("other", "Other"),
    ]

    # --- Core ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")
    amount = models.BigIntegerField()
    currency = models.CharField(max_length=10, default="BDT")

    # --- Payee ---
    payee_name = models.CharField(max_length=255)
    payee_account = models.CharField(max_length=255, blank=True, default="")
    payee_website = models.URLField(blank=True, default="")

    # --- Due / Late Fees ---
    due_date = models.DateField()
    due_date_day_of_month = models.IntegerField(null=True, blank=True)
    grace_period_days = models.IntegerField(null=True, blank=True)
    late_fee_amount = models.BigIntegerField(null=True, blank=True)
    late_fee_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    # --- Recurrence ---
    recurrence = models.CharField(
        max_length=20, choices=RECURRENCE_CHOICES, default="none"
    )
    recurrence_day_of_month = models.IntegerField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # --- Auto-pay ---
    auto_pay_enabled = models.BooleanField(default=False)
    auto_pay_method = models.CharField(max_length=100, blank=True, default="")
    auto_pay_day_before = models.IntegerField(null=True, blank=True)

    # --- Payment aggregates (denormalised for fast reads) ---
    total_paid_amount = models.BigIntegerField(default=0)
    total_payments_count = models.IntegerField(default=0)
    last_paid_date = models.DateField(null=True, blank=True)
    last_paid_amount = models.BigIntegerField(null=True, blank=True)

    # --- Reminders ---
    reminder_days_before = models.IntegerField(default=3)
    reminder_enabled = models.BooleanField(default=True)

    # --- Priority & Linking ---
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    linked_entity_id = models.UUIDField(null=True, blank=True)
    linked_entity_type = models.CharField(
        max_length=50, choices=LINKED_ENTITY_TYPE_CHOICES, null=True, blank=True
    )
    linked_calendar_event_id = models.UUIDField(null=True, blank=True)
    preferred_payment_account_id = models.UUIDField(null=True, blank=True)

    # --- Metadata ---
    notes = models.TextField(blank=True, default="")
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} — {self.currency} {self.amount}"


class BillPaymentHistory(models.Model):
    """
    Individual payment record for a Bill.
    No TenantMixin, no created_at / updated_at — lives and dies with its Bill.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bill = models.ForeignKey(
        Bill, on_delete=models.CASCADE, related_name="payment_history_set"
    )

    payment_date = models.DateField()
    amount = models.BigIntegerField()
    payment_method = models.CharField(max_length=100)
    reference_number = models.CharField(max_length=255, blank=True, default="")
    note = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-payment_date"]

    def __str__(self) -> str:
        return f"Payment {self.amount} on {self.payment_date} for {self.bill.name}"
