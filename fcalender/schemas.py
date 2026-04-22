"""
Calendar schemas — camelCase fields matching the frontend CalendarEvent interface exactly.
"""

import re
from datetime import date, datetime
from typing import Optional, List

from ninja import Schema

# ---------------------------------------------------------------------------
# Camel ↔ Snake helpers
# ---------------------------------------------------------------------------

_first_cap_re = re.compile(r"(.)([A-Z][a-z]+)")
_all_cap_re = re.compile(r"([a-z0-9])([A-Z])")


def _to_snake(name: str) -> str:
    s1 = _first_cap_re.sub(r"\1_\2", name)
    return _all_cap_re.sub(r"\1_\2", s1).lower()


def to_snake_case(data: dict) -> dict:
    return {_to_snake(k): v for k, v in data.items()}


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


def _fmt_date(d: Optional[date]) -> Optional[str]:
    if d is None:
        return None
    return d.isoformat() if isinstance(d, (date, datetime)) else str(d)


def _parse_date(d):
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


# ---------------------------------------------------------------------------
# CalendarEvent schemas
# ---------------------------------------------------------------------------

_DATE_FIELDS = ("event_date", "end_date", "due_date", "next_occurrence_date")


class CalendarEventOut(Schema):
    id: str
    createdAt: str
    updatedAt: str

    title: str
    description: Optional[str] = None
    category: str
    status: str

    amount: Optional[int] = None
    currency: Optional[str] = None

    eventDate: str
    endDate: Optional[str] = None
    dueDate: Optional[str] = None

    recurrence: str
    customRecurrenceDays: Optional[int] = None
    recurrenceDayOfMonth: Optional[int] = None
    nextOccurrenceDate: Optional[str] = None

    reminderDaysBefore: int
    reminderEnabled: bool
    secondReminderDaysBefore: Optional[int] = None

    color: Optional[str] = None

    linkedEntityId: Optional[str] = None
    linkedEntityType: Optional[str] = None
    linkedBillId: Optional[str] = None

    priority: str
    notes: Optional[str] = None
    tags: list

    @classmethod
    def from_model(cls, obj) -> "CalendarEventOut":
        return cls(
            id=str(obj.id),
            createdAt=obj.created_at.isoformat(),
            updatedAt=obj.updated_at.isoformat(),
            title=obj.title,
            description=obj.description or None,
            category=obj.category,
            status=obj.status,
            amount=obj.amount,
            currency=obj.currency or None,
            eventDate=_fmt_date(obj.event_date),
            endDate=_fmt_date(obj.end_date),
            dueDate=_fmt_date(obj.due_date),
            recurrence=obj.recurrence,
            customRecurrenceDays=obj.custom_recurrence_days,
            recurrenceDayOfMonth=obj.recurrence_day_of_month,
            nextOccurrenceDate=_fmt_date(obj.next_occurrence_date),
            reminderDaysBefore=obj.reminder_days_before,
            reminderEnabled=obj.reminder_enabled,
            secondReminderDaysBefore=obj.second_reminder_days_before,
            color=obj.color or None,
            linkedEntityId=str(obj.linked_entity_id) if obj.linked_entity_id else None,
            linkedEntityType=obj.linked_entity_type,
            linkedBillId=str(obj.linked_bill_id) if obj.linked_bill_id else None,
            priority=obj.priority,
            notes=obj.notes or None,
            tags=obj.tags or [],
        )


class CalendarEventCreate(Schema):
    title: str
    description: Optional[str] = None
    category: str
    amount: Optional[int] = None
    currency: Optional[str] = None
    eventDate: str
    endDate: Optional[str] = None
    dueDate: Optional[str] = None
    recurrence: str = "none"
    customRecurrenceDays: Optional[int] = None
    recurrenceDayOfMonth: Optional[int] = None
    nextOccurrenceDate: Optional[str] = None
    reminderDaysBefore: int = 0
    reminderEnabled: bool = True
    secondReminderDaysBefore: Optional[int] = None
    color: Optional[str] = None
    linkedEntityId: Optional[str] = None
    linkedEntityType: Optional[str] = None
    linkedBillId: Optional[str] = None
    priority: str = "medium"
    notes: Optional[str] = None
    tags: Optional[list] = None


class CalendarEventUpdate(Schema):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    eventDate: Optional[str] = None
    endDate: Optional[str] = None
    dueDate: Optional[str] = None
    recurrence: Optional[str] = None
    customRecurrenceDays: Optional[int] = None
    recurrenceDayOfMonth: Optional[int] = None
    nextOccurrenceDate: Optional[str] = None
    reminderDaysBefore: Optional[int] = None
    reminderEnabled: Optional[bool] = None
    secondReminderDaysBefore: Optional[int] = None
    color: Optional[str] = None
    linkedEntityId: Optional[str] = None
    linkedEntityType: Optional[str] = None
    linkedBillId: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list] = None


class MessageOut(Schema):
    message: str
