"""
Mortgage API endpoints for FinLife SaaS.

All endpoints are authenticated via BearerAuth (JWT).
All queries are filtered by request.user (tenant isolation).
List endpoints use paginate_queryset from common.pagination.
"""

from django.shortcuts import get_object_or_404
from ninja import Router

from common.permissions import BearerAuth
from common.pagination import (
    PaginationSchema,
    PaginatedResponse,
    paginate_queryset,
)

from .models import Mortgage, HeldMortgage, HeldMortgagePayment
from .schemas import (
    MortgageOut,
    MortgageCreate,
    MortgageUpdate,
    HeldMortgageOut,
    HeldMortgageCreate,
    HeldMortgageUpdate,
    HeldMortgagePaymentOut,
    HeldMortgagePaymentCreate,
    MessageOut,
)

router = Router(tags=["Mortgage"], auth=BearerAuth())


# ==================== Field mapping helpers ====================

MORTGAGE_FIELD_MAP = {
    "lenderName": "lender_name",
    "loanAmount": "loan_amount",
    "downPayment": "down_payment",
    "downPaymentPercent": "down_payment_percent",
    "currentBalance": "current_balance",
    "interestRate": "interest_rate",
    "interestType": "interest_type",
    "termMonths": "term_months",
    "emiAmount": "emi_amount",
    "startDate": "start_date",
    "nextPaymentDate": "next_payment_date",
    "totalInstallments": "total_installments",
    "status": "status",
    "bankAccountId": "bank_account_id",
    "currency": "currency",
    "notes": "notes",
}

HELD_MORTGAGE_FIELD_MAP = {
    "borrowerName": "borrower_name",
    "borrowerPhone": "borrower_phone",
    "borrowerEmail": "borrower_email",
    "borrowerAddress": "borrower_address",
    "relationship": "relationship",
    "loanAmount": "loan_amount",
    "currentBalance": "current_balance",
    "interestRate": "interest_rate",
    "interestType": "interest_type",
    "termMonths": "term_months",
    "expectedMonthlyPayment": "expected_monthly_payment",
    "startDate": "start_date",
    "nextPaymentDueDate": "next_payment_due_date",
    "totalInstallments": "total_installments",
    "status": "status",
    "latePaymentPenaltyRate": "late_payment_penalty_rate",
    "gracePeriodDays": "grace_period_days",
    "bankAccountId": "bank_account_id",
    "currency": "currency",
    "notes": "notes",
}

HELD_PAYMENT_FIELD_MAP = {
    "amount": "amount",
    "principalComponent": "principal_component",
    "interestComponent": "interest_component",
    "paymentDate": "payment_date",
    "paymentNumber": "payment_number",
    "note": "note",
}


def _apply_field_map(payload: dict, field_map: dict) -> dict:
    """Convert camelCase payload keys to snake_case model field names."""
    result = {}
    for key, value in payload.items():
        model_field = field_map.get(key, key)
        result[model_field] = value
    return result


# ==================== Mortgage CRUD ====================


@router.get("/", response=PaginatedResponse[MortgageOut])
async def list_mortgages(request, pagination: PaginationSchema):
    """List all mortgages for the authenticated user."""
    qs = Mortgage.objects.filter(owner=request.user).order_by("-created_at")
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


@router.post("/", response={201: MortgageOut})
async def create_mortgage(request, data: MortgageCreate):
    """Create a new mortgage."""
    payload = data.model_dump(exclude_unset=True)

    # Separate JSONField sub-objects
    property_data = payload.pop("property", None)
    escrow_data = payload.pop("escrow", None)

    db_fields = _apply_field_map(payload, MORTGAGE_FIELD_MAP)

    mortgage = Mortgage.objects.create(
        owner=request.user,
        property=property_data if property_data else {},
        escrow=escrow_data if escrow_data else {},
        **db_fields,
    )
    return 201, mortgage


@router.get("/{mortgage_id}", response=MortgageOut)
async def get_mortgage(request, mortgage_id: str):
    """Get a single mortgage by ID."""
    mortgage = get_object_or_404(Mortgage, id=mortgage_id, owner=request.user)
    return mortgage


@router.put("/{mortgage_id}", response=MortgageOut)
async def update_mortgage(request, mortgage_id: str, data: MortgageUpdate):
    """Update a mortgage (partial)."""
    mortgage = get_object_or_404(Mortgage, id=mortgage_id, owner=request.user)
    payload = data.model_dump(exclude_unset=True)

    # Handle JSONField sub-objects
    if "property" in payload:
        mortgage.property = payload.pop("property") or {}
    if "escrow" in payload:
        mortgage.escrow = payload.pop("escrow") or {}

    db_fields = _apply_field_map(payload, MORTGAGE_FIELD_MAP)
    for field, value in db_fields.items():
        setattr(mortgage, field, value)

    mortgage.save()
    return mortgage


@router.delete("/{mortgage_id}", response=MessageOut)
async def delete_mortgage(request, mortgage_id: str):
    """Delete a mortgage."""
    mortgage = get_object_or_404(Mortgage, id=mortgage_id, owner=request.user)
    mortgage.delete()
    return MessageOut(message="Mortgage deleted successfully")


# ==================== Held Mortgage CRUD ====================


@router.get("/held/", response=PaginatedResponse[HeldMortgageOut])
async def list_held_mortgages(request, pagination: PaginationSchema):
    """List all held mortgages for the authenticated user."""
    qs = HeldMortgage.objects.filter(owner=request.user).order_by("-created_at")
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


@router.post("/held/", response={201: HeldMortgageOut})
async def create_held_mortgage(request, data: HeldMortgageCreate):
    """Create a new held mortgage."""
    payload = data.model_dump(exclude_unset=True)

    # Separate JSONField sub-object
    collateral_data = payload.pop("collateral", None)

    db_fields = _apply_field_map(payload, HELD_MORTGAGE_FIELD_MAP)

    held = HeldMortgage.objects.create(
        owner=request.user,
        collateral=collateral_data if collateral_data else {},
        **db_fields,
    )
    return 201, held


@router.get("/held/{held_id}", response=HeldMortgageOut)
async def get_held_mortgage(request, held_id: str):
    """Get a single held mortgage by ID."""
    held = get_object_or_404(HeldMortgage, id=held_id, owner=request.user)
    return held


@router.put("/held/{held_id}", response=HeldMortgageOut)
async def update_held_mortgage(request, held_id: str, data: HeldMortgageUpdate):
    """Update a held mortgage (partial)."""
    held = get_object_or_404(HeldMortgage, id=held_id, owner=request.user)
    payload = data.model_dump(exclude_unset=True)

    # Handle JSONField sub-object
    if "collateral" in payload:
        held.collateral = payload.pop("collateral") or {}

    db_fields = _apply_field_map(payload, HELD_MORTGAGE_FIELD_MAP)
    for field, value in db_fields.items():
        setattr(held, field, value)

    held.save()
    return held


@router.delete("/held/{held_id}", response=MessageOut)
async def delete_held_mortgage(request, held_id: str):
    """Delete a held mortgage."""
    held = get_object_or_404(HeldMortgage, id=held_id, owner=request.user)
    held.delete()
    return MessageOut(message="Held mortgage deleted successfully")


# ==================== Held Mortgage Payments ====================


@router.post("/held/{held_id}/payments/", response={201: HeldMortgagePaymentOut})
async def create_held_mortgage_payment(
    request, held_id: str, data: HeldMortgagePaymentCreate
):
    """Record a payment received for a held mortgage."""
    held = get_object_or_404(HeldMortgage, id=held_id, owner=request.user)

    payload = data.model_dump(exclude_unset=True)
    db_fields = _apply_field_map(payload, HELD_PAYMENT_FIELD_MAP)

    payment = HeldMortgagePayment.objects.create(
        owner=request.user,
        held_mortgage=held,
        **db_fields,
    )

    # Update held mortgage aggregates
    held.total_received_amount = (held.total_received_amount or 0) + payment.amount
    held.total_interest_earned = (
        held.total_interest_earned or 0
    ) + payment.interest_component
    held.received_installments = (held.received_installments or 0) + 1
    held.current_balance = max(
        0, (held.current_balance or 0) - payment.principal_component
    )
    held.save()

    return 201, payment


@router.get(
    "/held/{held_id}/payments/", response=PaginatedResponse[HeldMortgagePaymentOut]
)
async def list_held_mortgage_payments(
    request, held_id: str, pagination: PaginationSchema
):
    """List all payments for a held mortgage."""
    held = get_object_or_404(HeldMortgage, id=held_id, owner=request.user)
    qs = held.payments.all().order_by("payment_number")
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


@router.delete("/held/{held_id}/payments/{payment_id}", response=MessageOut)
async def delete_held_mortgage_payment(request, held_id: str, payment_id: str):
    """Delete a held mortgage payment and update aggregates."""
    held = get_object_or_404(HeldMortgage, id=held_id, owner=request.user)
    payment = get_object_or_404(
        HeldMortgagePayment, id=payment_id, held_mortgage=held, owner=request.user
    )

    # Reverse the aggregates
    held.total_received_amount = max(
        0, (held.total_received_amount or 0) - payment.amount
    )
    held.total_interest_earned = max(
        0, (held.total_interest_earned or 0) - payment.interest_component
    )
    held.received_installments = max(0, (held.received_installments or 0) - 1)
    held.current_balance = (held.current_balance or 0) + payment.principal_component
    held.save()

    payment.delete()
    return MessageOut(message="Held mortgage payment deleted successfully")
