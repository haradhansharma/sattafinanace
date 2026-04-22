"""
Savings Goal models for FinLife Personal Finance SaaS.

Every model inherits from TenantMixin (common.models) which provides
the `owner` FK for multi-tenant isolation.
"""

import uuid

from django.db import models

from common.models import TenantMixin


class SavingsGoal(TenantMixin):
    """
    Savings goal matching the frontend SavingsGoal interface.

    Frontend fields: id, createdAt, updatedAt, name, description, category,
    status, targetAmount, currentAmount, currency, startDate, targetDate,
    completedDate, monthlyContributionAmount, autoContributeEnabled,
    autoContributeDayOfMonth, totalContributed, totalWithdrawn,
    contributionCount, motivationalQuote, coverColor, coverIcon,
    currentStreak, longestStreak, priority, bankAccountId, notes, tags
    """

    class Category(models.TextChoices):
        EMERGENCY_FUND = "emergency_fund", "Emergency Fund"
        VACATION = "vacation", "Vacation"
        HOME = "home", "Home"
        CAR = "car", "Car"
        EDUCATION = "education", "Education"
        WEDDING = "wedding", "Wedding"
        RETIREMENT = "retirement", "Retirement"
        GADGET = "gadget", "Gadget"
        GIFT = "gift", "Gift"
        MEDICAL = "medical", "Medical"
        OTHER = "other", "Other"

    class GoalStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        COMPLETED = "completed", "Completed"
        ABANDONED = "abandoned", "Abandoned"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    category = models.CharField(
        max_length=50, choices=Category.choices, default=Category.OTHER
    )
    status = models.CharField(
        max_length=50, choices=GoalStatus.choices, default=GoalStatus.ACTIVE
    )
    target_amount = models.BigIntegerField(default=0)
    current_amount = models.BigIntegerField(default=0)
    currency = models.CharField(max_length=10, default="BDT")
    start_date = models.DateField()
    target_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    monthly_contribution_amount = models.BigIntegerField(default=0)
    auto_contribute_enabled = models.BooleanField(default=False)
    auto_contribute_day_of_month = models.IntegerField(null=True, blank=True)
    total_contributed = models.BigIntegerField(default=0)
    total_withdrawn = models.BigIntegerField(default=0)
    contribution_count = models.IntegerField(default=0)
    motivational_quote = models.TextField(blank=True, default="")
    cover_color = models.CharField(max_length=7, blank=True, default="")
    cover_icon = models.CharField(max_length=255, blank=True, default="")
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    priority = models.CharField(
        max_length=50, choices=Priority.choices, default=Priority.MEDIUM
    )
    bank_account_id = models.CharField(max_length=255, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Savings Goal"
        verbose_name_plural = "Savings Goals"

    def __str__(self):
        return f"{self.name} — {self.get_category_display()}"


class SavingsGoalContribution(TenantMixin):
    """
    Contribution record linked to a savings goal.

    Frontend fields: id, amount, date, note, bankAccountId
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(
        SavingsGoal, on_delete=models.CASCADE, related_name="contributions"
    )
    amount = models.BigIntegerField(default=0)
    date = models.DateField()
    note = models.TextField(blank=True, default="")
    bank_account_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Savings Goal Contribution"
        verbose_name_plural = "Savings Goal Contributions"

    def __str__(self):
        return f"Contribution to {self.goal.name}: {self.amount}"


class SavingsGoalMilestone(TenantMixin):
    """
    Milestone record linked to a savings goal.

    Frontend fields: id, percent, label, achieved, achievedDate
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(
        SavingsGoal, on_delete=models.CASCADE, related_name="milestones"
    )
    percent = models.IntegerField(default=0)
    label = models.CharField(max_length=255, default="")
    achieved = models.BooleanField(default=False)
    achieved_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["percent"]
        verbose_name = "Savings Goal Milestone"
        verbose_name_plural = "Savings Goal Milestones"

    def __str__(self):
        return f"{self.label} ({self.percent}%)"
