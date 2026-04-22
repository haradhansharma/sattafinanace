from django.contrib import admin

from .models import Mortgage, HeldMortgage, HeldMortgagePayment


@admin.register(Mortgage)
class MortgageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "lender_name",
        "loan_amount",
        "current_balance",
        "interest_rate",
        "status",
        "owner",
    )
    list_filter = ("status", "interest_type", "currency")
    search_fields = ("lender_name",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(HeldMortgage)
class HeldMortgageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "borrower_name",
        "loan_amount",
        "current_balance",
        "interest_rate",
        "status",
        "owner",
    )
    list_filter = ("status", "relationship", "interest_type", "currency")
    search_fields = ("borrower_name", "borrower_email")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(HeldMortgagePayment)
class HeldMortgagePaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "held_mortgage",
        "amount",
        "payment_date",
        "payment_number",
        "owner",
    )
    list_filter = ("payment_date",)
    search_fields = ("held_mortgage__borrower_name",)
    readonly_fields = ("id", "created_at", "updated_at")
