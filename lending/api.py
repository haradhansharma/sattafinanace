import uuid
from datetime import date
from typing import Optional

from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from ninja import Router, Query

from common.permissions import BearerAuth
from common.pagination import PaginatedResponse, PaginationSchema
from common.pagination import paginate_queryset

from .models import Lending, LendingPayment
from .schemas import (
    LendingOut,
    LendingCreate,
    LendingUpdate,
    LendingPaymentOut,
    LendingPaymentCreate,
    LendingPaymentUpdate,
    MessageOut,
)

router = Router(tags=["Lending"])
auth = BearerAuth()

# ==================== Field Mapping: camelCase → snake_case ====================

LENDING_FIELD_MAP = {
    "borrowerName": "borrower_name",
    "borrowerPhone": "borrower_phone",
    "borrowerEmail": "borrower_email",
    "relationship": "relationship",
    "principalAmount": "principal_amount",
    "currentBalance": "current_balance",
    "interestRate": "interest_rate",
    "totalInterestAmount": "total_interest_amount",
    "totalRepayableAmount": "total_repayable_amount",
    "issuedDate": "issued_date",
    "dueDate": "due_date",
    "repaymentSchedule": "repayment_schedule",
}

LENDING_DATE_FIELDS = {"issuedDate", "dueDate"}

PAYMENT_FIELD_MAP = {
    "paymentDate": "payment_date",
}


def _parse_date(d):
    """Parse a date from ISO string or date object."""
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


def _map_lending_payload(payload: dict) -> dict:
    """Convert camelCase lending payload to snake_case model fields."""
    result = {}
    for key, value in payload.items():
        mapped = LENDING_FIELD_MAP.get(key, key)
        if key in LENDING_DATE_FIELDS and value is not None:
            result[mapped] = _parse_date(value)
        else:
            result[mapped] = value
    return result


# ==================== Lending CRUD ====================


@router.get("/", auth=auth, response=PaginatedResponse[LendingOut])
async def list_lendings(
    request,
    pagination: PaginationSchema = Query(...),
    status: Optional[str] = Query(None),
    relationship: Optional[str] = Query(None),
):
    """
    List all lending records for the authenticated user (paginated).
    Supports filtering by status and relationship.
    """
    qs = Lending.objects.filter(owner=request.user)

    if status:
        qs = qs.filter(status=status)
    if relationship:
        qs = qs.filter(relationship=relationship)

    items, total, total_pages = paginate_queryset(
        qs, pagination.page, pagination.per_page
    )

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": total_pages,
    }


@router.post("/", auth=auth, response={201: LendingOut, 400: MessageOut})
async def create_lending(request, payload: LendingCreate):
    """
    Create a new lending record.
    Defaults: currentBalance = principalAmount, totalRepaidAmount = 0.
    If totalRepayableAmount is not provided, it's computed as principal + interest.
    """
    raw = payload.model_dump()

    try:
        fields = _map_lending_payload(raw)

        # Defaults
        if fields.get("current_balance") is None:
            fields["current_balance"] = fields.get("principal_amount", 0)
        if fields.get("total_repayable_amount") is None:
            principal = fields.get("principal_amount", 0)
            interest = fields.get("total_interest_amount", 0)
            fields["total_repayable_amount"] = principal + interest
        if fields.get("tags") is None:
            fields["tags"] = []

        lending = Lending.objects.create(owner=request.user, **fields)
    except Exception as e:
        return 400, {"message": str(e)}

    return 201, lending


@router.get("/{lending_id}/", auth=auth, response={200: LendingOut, 404: MessageOut})
async def get_lending(request, lending_id: uuid.UUID):
    """Get a single lending record by ID with embedded payments."""
    lending = get_object_or_404(Lending, id=lending_id, owner=request.user)
    return lending


@router.put(
    "/{lending_id}/",
    auth=auth,
    response={200: LendingOut, 404: MessageOut, 400: MessageOut},
)
async def update_lending(request, lending_id: uuid.UUID, payload: LendingUpdate):
    """Update a lending record."""
    lending = get_object_or_404(Lending, id=lending_id, owner=request.user)
    raw = payload.model_dump(exclude_unset=True)

    try:
        fields = _map_lending_payload(raw)
        for field, value in fields.items():
            setattr(lending, field, value)
        lending.save()
    except Exception as e:
        return 400, {"message": str(e)}

    lending.refresh_from_db()
    return lending


@router.delete("/{lending_id}/", auth=auth, response={200: MessageOut, 404: MessageOut})
async def delete_lending(request, lending_id: uuid.UUID):
    """Delete a lending record and all its payments."""
    lending = get_object_or_404(Lending, id=lending_id, owner=request.user)
    lending.delete()
    return {"message": "Lending record deleted successfully"}


# ==================== Lending Payment CRUD ====================


@router.get(
    "/{lending_id}/payments/",
    auth=auth,
    response=PaginatedResponse[LendingPaymentOut],
)
async def list_lending_payments(
    request,
    lending_id: uuid.UUID,
    pagination: PaginationSchema = Query(...),
):
    """List payments for a specific lending record (paginated)."""
    get_object_or_404(Lending, id=lending_id, owner=request.user)

    qs = LendingPayment.objects.filter(
        owner=request.user,
        lending_id=lending_id,
    )

    items, total, total_pages = paginate_queryset(
        qs, pagination.page, pagination.per_page
    )

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": total_pages,
    }


@router.post(
    "/{lending_id}/payments/",
    auth=auth,
    response={201: LendingPaymentOut, 404: MessageOut, 400: MessageOut},
)
async def create_payment(
    request,
    lending_id: uuid.UUID,
    payload: LendingPaymentCreate,
):
    """
    Record a repayment against a lending record.
    Automatically updates the lending's totalRepaidAmount, currentBalance,
    and status based on repayment progress.
    """
    try:
        lending = get_object_or_404(Lending, id=lending_id, owner=request.user)

        # Determine next payment number
        last_payment = (
            LendingPayment.objects.filter(lending=lending)
            .order_by("-payment_number")
            .first()
        )
        next_number = (last_payment.payment_number + 1) if last_payment else 1

        # Create the payment record
        raw = payload.model_dump()
        raw["paymentDate"] = _parse_date(raw["paymentDate"])
        fields = {}
        for key, value in raw.items():
            mapped = PAYMENT_FIELD_MAP.get(key, key)
            fields[mapped] = value

        with db_transaction.atomic():
            payment = LendingPayment.objects.create(
                owner=request.user,
                lending=lending,
                payment_number=next_number,
                **fields,
            )

            # Update lending aggregate fields
            lending.total_repaid_amount += payload.amount
            lending.current_balance = max(
                0, lending.total_repayable_amount - lending.total_repaid_amount
            )

            if lending.current_balance <= 0:
                lending.status = "fully_repaid"
            elif lending.total_repaid_amount > 0:
                lending.status = "partially_repaid"

            lending.save()

    except Exception as e:
        return 400, {"message": str(e)}

    return 201, payment


@router.get(
    "/{lending_id}/payments/{payment_id}/",
    auth=auth,
    response={200: LendingPaymentOut, 404: MessageOut},
)
async def get_payment(
    request,
    lending_id: uuid.UUID,
    payment_id: uuid.UUID,
):
    """Get a specific payment by ID."""
    get_object_or_404(Lending, id=lending_id, owner=request.user)
    payment = get_object_or_404(
        LendingPayment, id=payment_id, owner=request.user, lending_id=lending_id
    )
    return payment


@router.put(
    "/{lending_id}/payments/{payment_id}/",
    auth=auth,
    response={200: LendingPaymentOut, 404: MessageOut, 400: MessageOut},
)
async def update_payment(
    request,
    lending_id: uuid.UUID,
    payment_id: uuid.UUID,
    payload: LendingPaymentUpdate,
):
    """Update a payment."""
    get_object_or_404(Lending, id=lending_id, owner=request.user)
    payment = get_object_or_404(
        LendingPayment, id=payment_id, owner=request.user, lending_id=lending_id
    )

    raw = payload.model_dump(exclude_unset=True)
    try:
        fields = {}
        for key, value in raw.items():
            mapped = PAYMENT_FIELD_MAP.get(key, key)
            if key == "paymentDate" and value is not None:
                value = _parse_date(value)
            fields[mapped] = value

        for field, value in fields.items():
            setattr(payment, field, value)

        payment.save()
    except Exception as e:
        return 400, {"message": str(e)}

    payment.refresh_from_db()
    return payment


@router.delete(
    "/{lending_id}/payments/{payment_id}/",
    auth=auth,
    response={200: MessageOut, 404: MessageOut},
)
async def delete_payment(
    request,
    lending_id: uuid.UUID,
    payment_id: uuid.UUID,
):
    """Delete a payment."""
    get_object_or_404(Lending, id=lending_id, owner=request.user)
    payment = get_object_or_404(
        LendingPayment, id=payment_id, owner=request.user, lending_id=lending_id
    )
    payment.delete()
    return {"message": "Payment deleted successfully"}


# ==================== Lending Actions ====================


@router.post(
    "/{lending_id}/mark-defaulted/",
    auth=auth,
    response={200: LendingOut, 404: MessageOut},
)
async def mark_defaulted(request, lending_id: uuid.UUID):
    """Mark a lending record as defaulted."""
    lending = get_object_or_404(Lending, id=lending_id, owner=request.user)
    lending.status = "defaulted"
    lending.save()
    lending.refresh_from_db()
    return lending


@router.post(
    "/{lending_id}/cancel/", auth=auth, response={200: LendingOut, 404: MessageOut}
)
async def cancel_lending(request, lending_id: uuid.UUID):
    """Cancel a lending record."""
    lending = get_object_or_404(Lending, id=lending_id, owner=request.user)
    lending.status = "cancelled"
    lending.save()
    lending.refresh_from_db()
    return lending
