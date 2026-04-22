from django.contrib import admin

from .models import Lending, LendingPayment


class LendingPaymentInline(admin.TabularInline):
    """Inline admin for LendingPayment — shows payments directly on Lending page."""

    model = LendingPayment
    extra = 1
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Lending)
class LendingAdmin(admin.ModelAdmin):
    """Admin for Lending model."""

    list_display = (
        "id",
        "borrower_name",
        "relationship",
        "principal_amount",
        "current_balance",
        "total_repaid_amount",
        "status",
        "currency",
        "owner",
        "created_at",
    )
    list_filter = ("relationship", "status", "currency", "created_at")
    search_fields = (
        "borrower_name",
        "borrower_phone",
        "borrower_email",
        "owner__email",
    )
    ordering = ("-created_at",)

    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [LendingPaymentInline]


@admin.register(LendingPayment)
class LendingPaymentAdmin(admin.ModelAdmin):
    """Admin for LendingPayment model."""

    list_display = (
        "id",
        "lending",
        "amount",
        "payment_number",
        "payment_date",
        "owner",
        "created_at",
    )
    list_filter = ("payment_date",)
    search_fields = ("lending__borrower_name", "note", "owner__email")
    ordering = ("-payment_date", "-created_at")

    readonly_fields = ("id", "created_at", "updated_at")
