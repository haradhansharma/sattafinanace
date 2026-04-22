"""
Income Source, Income Category, and Income models for FinLife.

All models inherit from TenantMixin to enforce tenant isolation.
TenantMixin adds `owner = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE)`.
"""

import uuid

from django.db import models

from common.models import TenantMixin


# ──────────────────────────────────────────────────────────────────────────────
# Choice constants — must match frontend TypeScript union types EXACTLY
# ──────────────────────────────────────────────────────────────────────────────

INCOME_SOURCE_TYPE_CHOICES = [
    ("salary", "Salary"),
    ("freelance", "Freelance"),
    ("business", "Business"),
    ("investment", "Investment"),
    ("rental", "Rental"),
    ("other", "Other"),
]

INCOME_CATEGORY_TYPE_CHOICES = [
    ("salary", "Salary"),
    ("freelance", "Freelance"),
    ("business", "Business"),
    ("investment", "Investment"),
    ("rental", "Rental"),
    ("refund", "Refund"),
    ("gift", "Gift"),
    ("other", "Other"),
]

RECURRING_CYCLE_CHOICES = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
    ("yearly", "Yearly"),
]


# ──────────────────────────────────────────────────────────────────────────────
# IncomeSource
# Frontend: id, name, type, isActive, monthlyAmount?, createdAt, updatedAt
# ──────────────────────────────────────────────────────────────────────────────


class IncomeSource(TenantMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    type = models.CharField(
        max_length=20, choices=INCOME_SOURCE_TYPE_CHOICES, default="salary"
    )
    is_active = models.BooleanField(default=True)
    monthly_amount = models.BigIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_active", "name")
        verbose_name = "Income Source"
        verbose_name_plural = "Income Sources"

    def __str__(self) -> str:
        return f"{self.name} ({self.type})"


# ──────────────────────────────────────────────────────────────────────────────
# IncomeCategory
# Frontend: id, name, icon, color, type, createdAt, updatedAt
# ──────────────────────────────────────────────────────────────────────────────


class IncomeCategory(TenantMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    icon = models.CharField(max_length=100, blank=True, default="")
    color = models.CharField(max_length=50, blank=True, default="")
    type = models.CharField(
        max_length=20, choices=INCOME_CATEGORY_TYPE_CHOICES, default="salary"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Income Category"
        verbose_name_plural = "Income Categories"

    def __str__(self) -> str:
        return self.name


# ──────────────────────────────────────────────────────────────────────────────
# Income
# Frontend: id, sourceId, amount, date, bankAccountId, categoryId,
#           transactionId?, description, isRecurring, recurringCycle?,
#           currency?, createdAt, updatedAt
# ──────────────────────────────────────────────────────────────────────────────


class Income(TenantMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    source = models.ForeignKey(
        IncomeSource,
        on_delete=models.CASCADE,
        related_name="incomes",
    )
    amount = models.BigIntegerField(default=0)
    date = models.DateField()
    bank_account_id = models.UUIDField()  # references BankAccount id
    category = models.ForeignKey(
        IncomeCategory,
        on_delete=models.CASCADE,
        related_name="incomes",
    )
    transaction_id = models.UUIDField(null=True, blank=True)
    description = models.TextField(blank=True, default="")
    is_recurring = models.BooleanField(default=False)
    recurring_cycle = models.CharField(
        max_length=20, choices=RECURRING_CYCLE_CHOICES, null=True, blank=True
    )
    currency = models.CharField(max_length=3, default="BDT")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-date", "-created_at")
        verbose_name = "Income"
        verbose_name_plural = "Incomes"

    def __str__(self) -> str:
        return f"Income {self.amount} on {self.date}"
