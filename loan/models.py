"""
Loan models for FinLife SaaS.

Loan — tracks a user's loan (personal, auto, education, business, other).
LoanPayment — individual payment records against a Loan.

Both models inherit from TenantMixin for automatic tenant isolation.
"""

import uuid

from django.db import models

from common.models import TenantMixin


class Loan(TenantMixin):
    """A loan taken by the user."""

    class LoanType(models.TextChoices):
        PERSONAL = "personal", "Personal"
        AUTO = "auto", "Auto"
        EDUCATION = "education", "Education"
        BUSINESS = "business", "Business"
        OTHER = "other", "Other"

    class LoanStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"
        DEFAULTED = "defaulted", "Defaulted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=LoanType.choices)
    lender_name = models.CharField(max_length=255)
    principal_amount = models.BigIntegerField(default=0)
    current_balance = models.BigIntegerField(default=0)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.IntegerField()
    emi_amount = models.BigIntegerField(default=0)
    start_date = models.DateField()
    next_payment_date = models.DateField(null=True, blank=True)
    next_payment_amount = models.BigIntegerField(default=0)
    paid_amount = models.BigIntegerField(default=0)
    paid_installments = models.IntegerField(default=0)
    total_installments = models.IntegerField()
    status = models.CharField(
        max_length=50, choices=LoanStatus.choices, default=LoanStatus.ACTIVE
    )
    bank_account_id = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=10, default="BDT")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Loan"
        verbose_name_plural = "Loans"
        indexes = [
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["owner", "type"]),
        ]

    def __str__(self):
        return f"{self.name} — {self.lender_name}"


class LoanPayment(TenantMixin):
    """A single payment made against a Loan."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="payments")
    amount = models.BigIntegerField(default=0)
    principal_component = models.BigIntegerField(default=0)
    interest_component = models.BigIntegerField(default=0)
    payment_date = models.DateField()
    payment_number = models.IntegerField()
    bank_account_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["payment_number"]
        verbose_name = "Loan Payment"
        verbose_name_plural = "Loan Payments"
        indexes = [
            models.Index(fields=["owner", "loan"]),
        ]

    def __str__(self):
        return f"Payment #{self.payment_number} for {self.loan.name}"
