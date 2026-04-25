"""
Expense app models for FinLife Personal Finance SaaS.

All models inherit from TenantMixin which adds an `owner` FK,
ensuring every record is scoped to the authenticated user.
"""

import uuid

from django.db import models

from common.models import TenantMixin


class ExpenseCategory(TenantMixin):
    """
    Expense category with type classification.
    Frontend fields: id, createdAt, updatedAt, name, icon, color,
                     type ('needs'|'wants'|'savings'|'investments'),
                     budgetLimit?
    """

    TYPE_CHOICES = [
        ("needs", "Needs"),
        ("wants", "Wants"),
        ("savings", "Savings"),
        ("investments", "Investments"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    icon = models.CharField(max_length=100, blank=True, default="")
    color = models.CharField(max_length=50, blank=True, default="")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="needs")
    budget_limit = models.BigIntegerField(null=True, blank=True)
    currency = models.CharField(max_length=10, default="BDT")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"

    def __str__(self):
        return self.name


class Expense(TenantMixin):
    """
    Individual expense record.
    Frontend fields: id, createdAt, updatedAt, amount, date,
                     bankAccountId (FK→BankAccount), cardId? (FK→Card),
                     categoryId (FK→ExpenseCategory), transactionId?,
                     description, isRecurring, recurringCycle?,
                     tags?, currency?
    """

    RECURRING_CYCLE_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.BigIntegerField(default=0)
    date = models.DateField()
    bank_account_id = models.UUIDField(
        null=True, blank=True
    )  # FK→BankAccount stored as UUID (optional for cash expenses)
    card_id = models.UUIDField(null=True, blank=True)  # FK→Card stored as UUID
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.CASCADE,
        related_name="expenses",
    )
    transaction_id = models.UUIDField(null=True, blank=True)
    description = models.TextField(blank=True, default="")
    is_recurring = models.BooleanField(default=False)
    recurring_cycle = models.CharField(
        max_length=20, choices=RECURRING_CYCLE_CHOICES, null=True, blank=True
    )
    tags = models.JSONField(default=list, blank=True)
    currency = models.CharField(max_length=10, default="BDT")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"Expense {self.amount} on {self.date}"
