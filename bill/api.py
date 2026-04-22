"""
Bill API — Django Ninja endpoints.

All endpoints are authenticated via BearerAuth and scoped to request.user.
List endpoints use paginate_queryset for standard pagination.
"""

import uuid

from django.http import HttpRequest
from ninja import Router

from common.permissions import BearerAuth
from common.pagination import paginate_queryset, PaginationSchema, PaginatedResponse

from .models import Bill, BillPaymentHistory
from .schemas import (
    BillOut,
    BillCreate,
    BillUpdate,
    MarkPaidIn,
    MessageOut,
    BillPaymentHistoryOut,
    BillPaymentHistoryIn,
    to_snake_case,
    _parse_date,
)

router = Router(auth=BearerAuth())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DATE_FIELDS = ("due_date", "end_date")


def _apply_bill_attrs(bill: Bill, data: dict) -> None:
    """Apply a snake_case data dict to a Bill instance, parsing dates."""
    for field in _DATE_FIELDS:
        val = data.get(field)
        if val is not None:
            data[field] = _parse_date(val)
    for key, value in data.items():
        setattr(bill, key, value)


def _hydrate_payment(obj: Bill, payments) -> BillOut:
    """Attach prefetched payments to the Bill instance before serialising."""
    obj._prefetched_payments = payments
    return BillOut.from_model(obj)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("/", response=PaginatedResponse[BillOut], summary="List bills")
async def list_bills(
    request: HttpRequest,
    page: int = 1,
    per_page: int = 20,
    category: str = None,
    status: str = None,
    priority: str = None,
):
    qs = Bill.objects.filter(owner=request.user)
    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)

    items, total, total_pages = paginate_queryset(qs, page, per_page)

    # Batch-prefetch payments for the page
    bill_ids = [b.id for b in items]
    payments_map: dict = {}
    if bill_ids:
        for p in BillPaymentHistory.objects.filter(bill_id__in=bill_ids):
            payments_map.setdefault(p.bill_id, []).append(p)

    results = [_hydrate_payment(b, payments_map.get(b.id, [])) for b in items]
    return {
        "items": results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.post("/", response={201: BillOut}, summary="Create a bill")
async def create_bill(request: HttpRequest, payload: BillCreate):
    data = to_snake_case(payload.model_dump())
    if data.get("tags") is None:
        data["tags"] = []
    if data.get("description") is None:
        data["description"] = ""
    bill = Bill(owner=request.user, **data)
    bill.full_clean()
    bill.save()
    bill.refresh_from_db()
    return BillOut.from_model(bill)


@router.get("/{bill_id}", response=BillOut, summary="Get bill by ID")
async def get_bill(request: HttpRequest, bill_id: uuid.UUID):
    bill = Bill.objects.get(id=bill_id, owner=request.user)
    return BillOut.from_model(bill)


@router.put("/{bill_id}", response=BillOut, summary="Update a bill")
async def update_bill(request: HttpRequest, bill_id: uuid.UUID, payload: BillUpdate):
    bill = Bill.objects.get(id=bill_id, owner=request.user)
    data = to_snake_case(payload.model_dump(exclude_unset=True))
    _apply_bill_attrs(bill, data)
    bill.full_clean()
    bill.save()
    bill.refresh_from_db()
    return BillOut.from_model(bill)


@router.delete("/{bill_id}", response=MessageOut, summary="Delete a bill")
async def delete_bill(request: HttpRequest, bill_id: uuid.UUID):
    bill = Bill.objects.get(id=bill_id, owner=request.user)
    bill_id_str = str(bill.id)
    bill.delete()
    return MessageOut(message=f"Bill {bill_id_str} deleted successfully")


# ---------------------------------------------------------------------------
# Payment history (embedded sub-resource)
# ---------------------------------------------------------------------------


@router.get(
    "/{bill_id}/payments",
    response=list[BillPaymentHistoryOut],
    summary="List bill payment history",
)
async def list_payments(request: HttpRequest, bill_id: uuid.UUID):
    Bill.objects.get(id=bill_id, owner=request.user)  # ownership check
    payments = BillPaymentHistory.objects.filter(bill_id=bill_id)
    return [
        BillPaymentHistoryOut(
            id=str(p.id),
            paymentDate=p.payment_date.isoformat(),
            amount=p.amount,
            paymentMethod=p.payment_method,
            referenceNumber=p.reference_number or None,
            note=p.note or None,
        )
        for p in payments
    ]


@router.post(
    "/{bill_id}/mark-paid",
    response=BillOut,
    summary="Mark bill as paid (creates payment record)",
)
async def mark_paid(request: HttpRequest, bill_id: uuid.UUID, payload: MarkPaidIn):
    bill = Bill.objects.get(id=bill_id, owner=request.user)
    data = to_snake_case(payload.model_dump())
    payment = BillPaymentHistory(
        bill=bill,
        payment_date=_parse_date(data["payment_date"]),
        amount=data["amount"],
        payment_method=data["payment_method"],
        reference_number=data.get("reference_number", "") or "",
        note=data.get("note", "") or "",
    )
    payment.full_clean()
    payment.save()
    payment.refresh_from_db()

    # Update denormalised aggregates
    bill.total_paid_amount = (bill.total_paid_amount or 0) + payment.amount
    bill.total_payments_count = (bill.total_payments_count or 0) + 1
    bill.last_paid_date = payment.payment_date
    bill.last_paid_amount = payment.amount
    bill.status = "paid"
    bill.save()
    bill.refresh_from_db()
    return BillOut.from_model(bill)


@router.post(
    "/{bill_id}/payments",
    response=BillPaymentHistoryOut,
    summary="Add a payment record",
)
async def add_payment(
    request: HttpRequest, bill_id: uuid.UUID, payload: BillPaymentHistoryIn
):
    bill = Bill.objects.get(id=bill_id, owner=request.user)
    data = to_snake_case(payload.model_dump())
    payment = BillPaymentHistory(
        bill=bill,
        payment_date=_parse_date(data["payment_date"]),
        amount=data["amount"],
        payment_method=data["payment_method"],
        reference_number=data.get("reference_number", "") or "",
        note=data.get("note", "") or "",
    )
    payment.full_clean()
    payment.save()
    payment.refresh_from_db()
    # Update denormalised aggregates
    bill.total_paid_amount = (bill.total_paid_amount or 0) + payment.amount
    bill.total_payments_count = (bill.total_payments_count or 0) + 1
    bill.last_paid_date = payment.payment_date
    bill.last_paid_amount = payment.amount
    await bill.asave()

    return BillPaymentHistoryOut(
        id=str(payment.id),
        paymentDate=payment.payment_date.isoformat(),
        amount=payment.amount,
        paymentMethod=payment.payment_method,
        referenceNumber=payment.reference_number or None,
        note=payment.note or None,
    )


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------


@router.post("/{bill_id}/skip", response=BillOut, summary="Skip a bill")
async def skip_bill(request: HttpRequest, bill_id: uuid.UUID):
    bill = Bill.objects.get(id=bill_id, owner=request.user)
    bill.status = "skipped"
    bill.save()
    bill.refresh_from_db()
    return BillOut.from_model(bill)


@router.post("/{bill_id}/cancel", response=BillOut, summary="Cancel a bill")
async def cancel_bill(request: HttpRequest, bill_id: uuid.UUID):
    bill = Bill.objects.get(id=bill_id, owner=request.user)
    bill.status = "cancelled"
    bill.save()
    bill.refresh_from_db()
    return BillOut.from_model(bill)
