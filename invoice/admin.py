from django.contrib import admin

from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    """Inline admin for InvoiceItem — shows items directly on Invoice page."""

    model = InvoiceItem
    extra = 1
    readonly_fields = ("id",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin for Invoice model."""

    list_display = (
        "id",
        "invoice_number",
        "type",
        "client_name",
        "total_amount",
        "status",
        "currency",
        "owner",
        "created_at",
    )
    list_filter = ("type", "status", "currency", "created_at")
    search_fields = ("invoice_number", "client_name", "client_email", "owner__email")
    ordering = ("-created_at",)

    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [InvoiceItemInline]


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    """Admin for InvoiceItem model."""

    list_display = (
        "id",
        "description",
        "quantity",
        "unit_price",
        "total",
        "invoice",
    )
    search_fields = ("description", "invoice__invoice_number")
    readonly_fields = ("id",)
