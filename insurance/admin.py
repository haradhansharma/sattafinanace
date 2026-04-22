from django.contrib import admin

from .models import (
    Insurance,
    InsuranceBeneficiary,
    InsurancePremiumPayment,
    InsuranceClaim,
)


@admin.register(Insurance)
class InsuranceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "provider",
        "policy_number",
        "status",
        "owner",
        "created_at",
    )
    list_filter = ("category", "status", "premium_frequency", "created_at")
    search_fields = ("name", "provider", "policy_number", "group_policy_number")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(InsuranceBeneficiary)
class InsuranceBeneficiaryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "relationship", "percentage", "insurance", "owner")
    list_filter = ("relationship",)
    search_fields = ("name", "insurance__name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(InsurancePremiumPayment)
class InsurancePremiumPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "amount",
        "payment_date",
        "payment_number",
        "insurance",
        "owner",
        "created_at",
    )
    list_filter = ("payment_date",)
    search_fields = ("insurance__name", "insurance__policy_number", "note")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "claim_number",
        "claim_amount",
        "approved_amount",
        "status",
        "insurance",
        "owner",
        "created_at",
    )
    list_filter = ("status", "claim_date")
    search_fields = (
        "claim_number",
        "insurance__name",
        "insurance__policy_number",
        "description",
    )
    readonly_fields = ("id", "created_at", "updated_at")
