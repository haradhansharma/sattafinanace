"""
Budget models for FinLife SaaS.

Budget — top-level monthly budget owned by a user.
BudgetCategory — individual category allocation within a budget.

Computed fields (allocatedAmount, availableBalance, remainingBalance, spentAmount,
isOverBudget, overAmount, forecastedSpend, forecastGap, dailySafeSpend,
requiredDailyReduction, requiredExtraIncome) are NOT stored in the database.
They are calculated in the API response layer.
"""

import uuid

from django.db import models

from common.models import TenantMixin


class Budget(TenantMixin):
    """Monthly budget for the authenticated user."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    month = models.CharField(max_length=7)  # format "YYYY-MM"
    currency = models.CharField(max_length=10, default="BDT")
    total_budget_amount = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-month", "-created_at"]
        indexes = [
            models.Index(fields=["owner", "month"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.month})"


class BudgetCategory(TenantMixin):
    """Category allocation within a Budget.

    ``category_id`` stores the UUID of the related ExpenseCategory (kept as a
    plain UUIDField rather than a FK to avoid cross-app migration coupling).
    Only ``budget_amount`` is persisted — all spending-derived fields are
    computed at serialization time.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget = models.ForeignKey(
        Budget, on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=255)
    category_id = models.UUIDField()  # references ExpenseCategory.id
    budget_amount = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("budget", "category_id")
        indexes = [
            models.Index(fields=["owner", "budget"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.budget.name})"
