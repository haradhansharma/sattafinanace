from django.contrib import admin

from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "event_date",
        "status",
        "amount",
        "currency",
        "recurrence",
        "priority",
        "owner",
    )
    list_filter = ("category", "status", "recurrence", "priority", "reminder_enabled")
    search_fields = ("title", "description", "notes")
    readonly_fields = ("id", "created_at", "updated_at")
    date_hierarchy = "event_date"
