from django.contrib import admin

from .models import Budget, BudgetCategory


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "month",
        "currency",
        "total_budget_amount",
        "owner",
        "created_at",
    )
    list_filter = ("month", "currency")
    search_fields = ("name", "month")
    raw_id_fields = ("owner",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "budget",
        "category_id",
        "budget_amount",
        "owner",
    )
    list_filter = ()
    search_fields = ("name",)
    raw_id_fields = ("budget", "owner")
    readonly_fields = ("id", "created_at", "updated_at")
