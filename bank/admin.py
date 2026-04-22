from django.contrib import admin

from .models import BankAccount, Transaction


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "bank_name",
        "account_name",
        "account_number",
        "type",
        "opening_balance",
        "currency",
        "is_active",
        "created_at",
    )
    list_filter = ("type", "currency", "is_active")
    search_fields = ("bank_name", "account_name", "account_number", "owner__email")
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "bank_account",
        "type",
        "amount",
        "direction",
        "category_id",
        "date",
        "currency",
        "created_at",
    )
    list_filter = ("type", "direction", "currency", "date")
    search_fields = (
        "description",
        "reference_id",
        "owner__email",
        "bank_account__bank_name",
    )
    ordering = ("-date", "-created_at")
    readonly_fields = ("id", "created_at", "updated_at")
