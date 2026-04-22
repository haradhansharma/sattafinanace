"""
Expense app admin configuration for FinLife Personal Finance SaaS.
"""

from django.contrib import admin

from .models import Expense, ExpenseCategory


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "icon",
        "color",
        "type",
        "budget_limit",
        "owner",
        "created_at",
    )
    list_filter = ("type",)
    search_fields = ("name",)
    raw_id_fields = ("owner",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "amount",
        "date",
        "currency",
        "description",
        "category",
        "owner",
        "created_at",
    )
    list_filter = ("currency", "is_recurring", "recurring_cycle", "date")
    search_fields = ("description",)
    raw_id_fields = ("category", "owner")
    readonly_fields = ("id", "created_at", "updated_at")
