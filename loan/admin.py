from django.contrib import admin

from .models import Loan, LoanPayment


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "type",
        "lender_name",
        "principal_amount",
        "current_balance",
        "status",
        "owner",
        "created_at",
    )
    list_filter = ("type", "status", "currency")
    search_fields = ("name", "lender_name")
    raw_id_fields = ("owner",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(LoanPayment)
class LoanPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "loan",
        "amount",
        "principal_component",
        "interest_component",
        "payment_date",
        "payment_number",
        "owner",
    )
    list_filter = ("payment_date",)
    search_fields = ("loan__name",)
    raw_id_fields = ("loan", "owner")
    readonly_fields = ("id", "created_at", "updated_at")
