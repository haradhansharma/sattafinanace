"""
Card app admin configuration for FinLife Personal Finance SaaS.
"""

from django.contrib import admin

from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "type",
        "brand",
        "card_number",
        "holder_name",
        "bank_account",
        "is_active",
        "currency",
        "current_balance",
        "owner",
        "created_at",
    )
    list_filter = ("type", "brand", "is_active", "currency")
    search_fields = ("name", "card_number", "holder_name")
    raw_id_fields = ("owner", "bank_account")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        (
            None,
            {
                "fields": ("name", "type", "brand", "bank_account", "is_active"),
            },
        ),
        (
            "Card Details",
            {
                "fields": ("card_number", "holder_name", "expiry_date"),
            },
        ),
        (
            "Financial",
            {
                "fields": ("credit_limit", "current_balance", "currency", "color"),
                "classes": ("collapse",),
            },
        ),
        (
            "Billing",
            {
                "fields": ("billing_cycle", "due_date"),
                "classes": ("collapse",),
            },
        ),
        (
            "Secondary Currency",
            {
                "fields": (
                    "secondary_currency",
                    "secondary_credit_limit",
                    "secondary_current_balance",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "System",
            {
                "fields": ("id", "owner", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
