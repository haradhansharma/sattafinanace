"""
Bill schemas — camelCase fields matching the frontend Bill interface exactly.

Conversion helpers:
  • to_snake_case  – camelCase dict → snake_case dict (for Django model kwargs)
  • to_camel_case  – snake_case dict → camelCase dict (for schema output)
"""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

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


def _to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def to_camel_case(data: dict) -> dict:
    return {_to_camel(k): v for k, v in data.items()}


# ---------------------------------------------------------------------------
# Date helper
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
# BillPaymentHistory
# ---------------------------------------------------------------------------


class BillPaymentHistoryOut(Schema):
    id: str
    paymentDate: str
    amount: int
    paymentMethod: str
    referenceNumber: Optional[str] = None
    note: Optional[str] = None


class BillPaymentHistoryIn(Schema):
    paymentDate: str
    amount: int
    paymentMethod: str
    referenceNumber: Optional[str] = None
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Bill
# ---------------------------------------------------------------------------


class BillOut(Schema):
    id: str
    createdAt: str
    updatedAt: str

    name: str
    description: Optional[str] = None
    category: str
    status: str
    amount: int
    currency: str

    payeeName: str
    payeeAccount: Optional[str] = None
    payeeWebsite: Optional[str] = None

    dueDate: str
    dueDateDayOfMonth: Optional[int] = None
    gracePeriodDays: Optional[int] = None
    lateFeeAmount: Optional[int] = None
    lateFeePercent: Optional[float] = None

    recurrence: str
    recurrenceDayOfMonth: Optional[int] = None
    endDate: Optional[str] = None

    autoPayEnabled: bool
    autoPayMethod: Optional[str] = None
    autoPayDayBefore: Optional[int] = None

    # Embedded payment history
    paymentHistory: List[BillPaymentHistoryOut]

    totalPaidAmount: int
    totalPaymentsCount: int
    lastPaidDate: Optional[str] = None
    lastPaidAmount: Optional[int] = None

    reminderDaysBefore: int
    reminderEnabled: bool

    priority: str

    linkedEntityId: Optional[str] = None
    linkedEntityType: Optional[str] = None
    linkedCalendarEventId: Optional[str] = None
    preferredPaymentAccountId: Optional[str] = None

    notes: Optional[str] = None
    tags: list

    @classmethod
    def from_model(cls, obj: "Bill") -> "BillOut":
        from .models import BillPaymentHistory  # avoid circular at module-level

        payments = [
            BillPaymentHistoryOut(
                id=str(p.id),
                paymentDate=_fmt_date(p.payment_date),
                amount=p.amount,
                paymentMethod=p.payment_method,
                referenceNumber=p.reference_number or None,
                note=p.note or None,
            )
            for p in getattr(obj, "_prefetched_payments", obj.payment_history_set.all())
        ]
        return cls(
            id=str(obj.id),
            createdAt=obj.created_at.isoformat(),
            updatedAt=obj.updated_at.isoformat(),
            name=obj.name,
            description=obj.description or None,
            category=obj.category,
            status=obj.status,
            amount=obj.amount,
            currency=obj.currency,
            payeeName=obj.payee_name,
            payeeAccount=obj.payee_account or None,
            payeeWebsite=obj.payee_website or None,
            dueDate=_fmt_date(obj.due_date),
            dueDateDayOfMonth=obj.due_date_day_of_month,
            gracePeriodDays=obj.grace_period_days,
            lateFeeAmount=obj.late_fee_amount,
            lateFeePercent=(
                float(obj.late_fee_percent)
                if obj.late_fee_percent is not None
                else None
            ),
            recurrence=obj.recurrence,
            recurrenceDayOfMonth=obj.recurrence_day_of_month,
            endDate=_fmt_date(obj.end_date),
            autoPayEnabled=obj.auto_pay_enabled,
            autoPayMethod=obj.auto_pay_method or None,
            autoPayDayBefore=obj.auto_pay_day_before,
            paymentHistory=payments,
            totalPaidAmount=obj.total_paid_amount,
            totalPaymentsCount=obj.total_payments_count,
            lastPaidDate=_fmt_date(obj.last_paid_date),
            lastPaidAmount=obj.last_paid_amount,
            reminderDaysBefore=obj.reminder_days_before,
            reminderEnabled=obj.reminder_enabled,
            priority=obj.priority,
            linkedEntityId=str(obj.linked_entity_id) if obj.linked_entity_id else None,
            linkedEntityType=obj.linked_entity_type,
            linkedCalendarEventId=(
                str(obj.linked_calendar_event_id)
                if obj.linked_calendar_event_id
                else None
            ),
            preferredPaymentAccountId=(
                str(obj.preferred_payment_account_id)
                if obj.preferred_payment_account_id
                else None
            ),
            notes=obj.notes or None,
            tags=obj.tags or [],
        )


class BillCreate(Schema):
    name: str
    description: Optional[str] = None
    category: str
    amount: int
    currency: str = "BDT"
    payeeName: str
    payeeAccount: Optional[str] = None
    payeeWebsite: Optional[str] = None
    dueDate: str
    dueDateDayOfMonth: Optional[int] = None
    gracePeriodDays: Optional[int] = None
    lateFeeAmount: Optional[int] = None
    lateFeePercent: Optional[float] = None
    recurrence: str = "none"
    recurrenceDayOfMonth: Optional[int] = None
    endDate: Optional[str] = None
    autoPayEnabled: bool = False
    autoPayMethod: Optional[str] = None
    autoPayDayBefore: Optional[int] = None
    reminderDaysBefore: int = 3
    reminderEnabled: bool = True
    priority: str = "medium"
    linkedEntityId: Optional[str] = None
    linkedEntityType: Optional[str] = None
    linkedCalendarEventId: Optional[str] = None
    preferredPaymentAccountId: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list] = None


class BillUpdate(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    payeeName: Optional[str] = None
    payeeAccount: Optional[str] = None
    payeeWebsite: Optional[str] = None
    dueDate: Optional[str] = None
    dueDateDayOfMonth: Optional[int] = None
    gracePeriodDays: Optional[int] = None
    lateFeeAmount: Optional[int] = None
    lateFeePercent: Optional[float] = None
    recurrence: Optional[str] = None
    recurrenceDayOfMonth: Optional[int] = None
    endDate: Optional[str] = None
    autoPayEnabled: Optional[bool] = None
    autoPayMethod: Optional[str] = None
    autoPayDayBefore: Optional[int] = None
    reminderDaysBefore: Optional[int] = None
    reminderEnabled: Optional[bool] = None
    priority: Optional[str] = None
    linkedEntityId: Optional[str] = None
    linkedEntityType: Optional[str] = None
    linkedCalendarEventId: Optional[str] = None
    preferredPaymentAccountId: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list] = None


class MarkPaidIn(Schema):
    paymentDate: str
    amount: int
    paymentMethod: str
    referenceNumber: Optional[str] = None
    note: Optional[str] = None


class MessageOut(Schema):
    message: str
