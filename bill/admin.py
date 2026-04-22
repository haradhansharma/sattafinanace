from django.contrib import admin

from .models import Bill, BillPaymentHistory


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "payee_name",
        "amount",
        "currency",
        "status",
        "recurrence",
        "priority",
        "due_date",
        "owner",
    )
    list_filter = (
        "category",
        "status",
        "currency",
        "recurrence",
        "priority",
        "auto_pay_enabled",
        "reminder_enabled",
    )
    search_fields = ("name", "payee_name", "payee_account", "description", "notes")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "total_paid_amount",
        "total_payments_count",
        "last_paid_date",
        "last_paid_amount",
    )
    date_hierarchy = "due_date"


class BillPaymentHistoryInline(admin.TabularInline):
    model = BillPaymentHistory
    extra = 0
    readonly_fields = ("id",)
    fields = ("payment_date", "amount", "payment_method", "reference_number", "note")
