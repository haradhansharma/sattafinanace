"""
Django admin configuration for Savings Goal models.
"""

from django.contrib import admin

from .models import SavingsGoal, SavingsGoalContribution, SavingsGoalMilestone


class SavingsGoalContributionInline(admin.TabularInline):
    """Inline for contributions on the savings goal detail page."""

    model = SavingsGoalContribution
    extra = 1
    readonly_fields = ("id", "created_at", "updated_at")


class SavingsGoalMilestoneInline(admin.TabularInline):
    """Inline for milestones on the savings goal detail page."""

    model = SavingsGoalMilestone
    extra = 1
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    """Admin for SavingsGoal model."""

    list_display = (
        "id",
        "name",
        "category",
        "target_amount",
        "current_amount",
        "status",
        "priority",
        "currency",
        "owner",
        "created_at",
    )
    list_filter = ("status", "category", "priority", "currency")
    search_fields = ("name", "description", "owner__email")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [SavingsGoalMilestoneInline, SavingsGoalContributionInline]


@admin.register(SavingsGoalContribution)
class SavingsGoalContributionAdmin(admin.ModelAdmin):
    """Admin for SavingsGoalContribution model."""

    list_display = (
        "id",
        "goal",
        "amount",
        "date",
        "owner",
        "created_at",
    )
    list_filter = ("date",)
    search_fields = ("goal__name", "note", "owner__email")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(SavingsGoalMilestone)
class SavingsGoalMilestoneAdmin(admin.ModelAdmin):
    """Admin for SavingsGoalMilestone model."""

    list_display = (
        "id",
        "goal",
        "percent",
        "label",
        "achieved",
        "owner",
    )
    list_filter = ("achieved",)
    search_fields = ("goal__name", "label", "owner__email")
    readonly_fields = ("id", "created_at", "updated_at")
