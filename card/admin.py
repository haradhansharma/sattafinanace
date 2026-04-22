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
        "is_active",
        "currency",
        "current_balance",
        "owner",
        "created_at",
    )
    list_filter = ("type", "brand", "is_active", "currency")
    search_fields = ("name", "card_number", "holder_name")
    raw_id_fields = ("owner",)
    readonly_fields = ("id", "created_at", "updated_at")
