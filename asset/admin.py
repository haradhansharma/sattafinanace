from django.contrib import admin

from .models import Asset, AssetValuation


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "current_condition",
        "status",
        "purchase_price",
        "current_value",
        "currency",
        "ownership_percentage",
        "owner",
    )
    list_filter = (
        "category",
        "current_condition",
        "status",
        "currency",
        "depreciation_method",
        "loan_against_asset",
        "property_type",
        "vehicle_type",
    )
    search_fields = (
        "name",
        "description",
        "property_address",
        "vehicle_registration_no",
        "registration_number",
        "serial_number",
        "notes",
    )
    readonly_fields = ("id", "created_at", "updated_at")


class AssetValuationInline(admin.TabularInline):
    model = AssetValuation
    extra = 0
    readonly_fields = ("id",)
    fields = ("date", "value", "note")
