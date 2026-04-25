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
        "current_balance",
        "created_at",
    )
    list_filter = ("type", "currency", "is_active")
    search_fields = ("bank_name", "account_name", "account_number", "owner__email")
    ordering = ("-created_at",)
    readonly_fields = ("id", "current_balance", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("bank_name", "account_number", "account_name", "type")}),
        ("Financial", {"fields": ("opening_balance", "currency", "current_balance")}),
        ("Appearance", {"fields": ("icon", "color")}),
        ("Status", {"fields": ("is_active",)}),
        (
            "System",
            {
                "fields": ("owner", "id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "bank_account",
        "type",
        "amount",
        "direction",
        "category",
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
    readonly_fields = ("id", "direction", "created_at", "updated_at")
    raw_id_fields = ("bank_account", "to_bank_account", "category", "owner")

    fieldsets = (
        (None, {"fields": ("bank_account", "to_bank_account", "type", "direction")}),
        (
            "Details",
            {"fields": ("amount", "currency", "category", "date", "description")},
        ),
        (
            "Extra",
            {
                "fields": ("reference_id", "tags"),
                "classes": ("collapse",),
            },
        ),
        (
            "System",
            {
                "fields": ("owner", "id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """Auto-set direction from type if not explicitly provided."""
        if obj.type in ("income", "expense"):
            obj.direction = "credit" if obj.type == "income" else "debit"
        super().save_model(request, obj, form, change)
