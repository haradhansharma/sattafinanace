from django.contrib import admin

from .models import Income, IncomeCategory, IncomeSource


@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "icon", "color", "type", "owner", "created_at")
    list_filter = ("type",)
    search_fields = ("name",)
    raw_id_fields = ("owner",)


@admin.register(IncomeSource)
class IncomeSourceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "type",
        "is_active",
        "monthly_amount",
        "owner",
        "created_at",
    )
    list_filter = ("type", "is_active")
    search_fields = ("name",)
    raw_id_fields = ("owner",)


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "amount",
        "date",
        "currency",
        "source",
        "category",
        "owner",
        "created_at",
    )
    list_filter = ("currency", "is_recurring", "recurring_cycle", "date")
    search_fields = ("description",)
    raw_id_fields = ("source", "category", "owner")
