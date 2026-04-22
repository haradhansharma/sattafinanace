from django.contrib import admin

from .models import Investment, InvestmentTransaction


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    """Admin for Investment model."""

    list_display = (
        "id",
        "owner",
        "name",
        "category",
        "institution",
        "status",
        "invested_amount",
        "current_value",
        "currency",
        "created_at",
    )
    list_filter = ("category", "status", "currency", "created_at")
    search_fields = ("name", "institution", "account_number", "owner__email")
    ordering = ("-created_at",)

    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(InvestmentTransaction)
class InvestmentTransactionAdmin(admin.ModelAdmin):
    """Admin for InvestmentTransaction model."""

    list_display = (
        "id",
        "owner",
        "investment",
        "type",
        "amount",
        "units",
        "date",
        "unit_price",
        "created_at",
    )
    list_filter = ("type", "date")
    search_fields = ("investment__name", "note", "owner__email")
    ordering = ("-date", "-created_at")

    readonly_fields = ("id", "created_at", "updated_at")
