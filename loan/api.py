"""
Loan API endpoints (Django Ninja).

All endpoints require BearerAuth and filter by request.user.

**NEW**: Payment creation endpoint (`POST /{loan_id}/payments/`) that was
previously missing.  Creating a payment also atomically updates the parent
Loan's aggregated fields (paid_amount, paid_installments, current_balance,
next_payment_date).
"""

from calendar import monthrange
from datetime import date
from typing import Optional

from django.db import models, transaction
from django.shortcuts import get_object_or_404
from ninja import Router

from common.pagination import PaginatedResponse, PaginationSchema, paginate_queryset
from common.permissions import BearerAuth

from .models import Loan, LoanPayment
from .schemas import (
    LoanOut,
    LoanCreate,
    LoanUpdate,
    LoanPaymentOut,
    LoanPaymentCreate,
    LoanPaymentUpdate,
    MessageOut,
)

router = Router(tags=["Loan"], auth=BearerAuth())


# ==================== Helpers ====================

# camelCase → snake_case field mapping for Loan partial updates
_LOAN_FIELD_MAP = {
    "name": "name",
    "type": "type",
    "lenderName": "lender_name",
    "principalAmount": "principal_amount",
    "currentBalance": "current_balance",
    "interestRate": "interest_rate",
    "termMonths": "term_months",
    "emiAmount": "emi_amount",
    "startDate": "start_date",
    "nextPaymentDate": "next_payment_date",
    "nextPaymentAmount": "next_payment_amount",
    "totalInstallments": "total_installments",
    "status": "status",
    "bankAccountId": "bank_account_id",
    "currency": "currency",
    "notes": "notes",
}

_PAYMENT_FIELD_MAP = {
    "amount": "amount",
    "principalComponent": "principal_component",
    "interestComponent": "interest_component",
    "paymentDate": "payment_date",
    "paymentNumber": "payment_number",
    "bankAccountId": "bank_account_id",
}


def _advance_next_payment(loan: Loan):
    """Push next_payment_date to the following month (same day-of-month)."""
    if not loan.next_payment_date:
        return
    try:
        cur = loan.next_payment_date
        if cur.month == 12:
            nxt = date(cur.year + 1, 1, cur.day)
        else:
            max_day = monthrange(cur.year, cur.month + 1)[1]
            nxt = date(cur.year, cur.month + 1, min(cur.day, max_day))
        loan.next_payment_date = nxt
    except Exception:
        pass  # leave unchanged if calculation fails


def _check_loan_completion(loan: Loan):
    """Auto-mark loan as completed if all installments are paid or balance is zero."""
    if (
        loan.paid_installments >= loan.total_installments
        and loan.total_installments > 0
    ):
        loan.status = Loan.LoanStatus.COMPLETED
        loan.current_balance = 0
    elif loan.current_balance <= 0 and loan.principal_amount > 0:
        loan.status = Loan.LoanStatus.COMPLETED
        loan.current_balance = 0


# ==================== Loan CRUD ====================


@router.get("/", response=PaginatedResponse[LoanOut])
async def list_loans(
    request,
    type: Optional[str] = None,
    status: Optional[str] = None,
    pagination: PaginationSchema = PaginationSchema(),
):
    """List all loans for the authenticated user."""
    qs = Loan.objects.filter(owner=request.user)
    if type:
        qs = qs.filter(type=type)
    if status:
        qs = qs.filter(status=status)
    qs = qs.order_by("-created_at")

    items, total, total_pages = paginate_queryset(
        qs, pagination.page, pagination.per_page
    )
    return PaginatedResponse(
        items=[LoanOut.from_orm(obj) for obj in items],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=total_pages,
    )


@router.post("/", response={201: LoanOut})
async def create_loan(request, data: LoanCreate):
    """Create a new loan."""
    loan = Loan.objects.create(
        owner=request.user,
        name=data.name,
        type=data.type,
        lender_name=data.lenderName,
        principal_amount=data.principalAmount,
        current_balance=data.currentBalance,
        interest_rate=data.interestRate,
        term_months=data.termMonths,
        emi_amount=data.emiAmount,
        start_date=data.startDate,
        next_payment_date=data.nextPaymentDate,
        next_payment_amount=data.nextPaymentAmount,
        total_installments=data.totalInstallments,
        status=data.status,
        bank_account_id=data.bankAccountId,
        currency=data.currency,
        notes=data.notes,
    )
    return 201, LoanOut.from_orm(loan)


@router.get("/{loan_id}/", response=LoanOut)
async def get_loan(request, loan_id: str):
    """Get a specific loan by ID (with embedded payments)."""
    loan = get_object_or_404(Loan, id=loan_id, owner=request.user)
    return LoanOut.from_orm(loan)


@router.put("/{loan_id}/", response=LoanOut)
async def update_loan(request, loan_id: str, data: LoanUpdate):
    """Update a loan (partial — only supplied fields are changed)."""
    loan = get_object_or_404(Loan, id=loan_id, owner=request.user)
    payload = data.model_dump(exclude_unset=True)
    for schema_key, model_field in _LOAN_FIELD_MAP.items():
        if schema_key in payload:
            setattr(loan, model_field, payload[schema_key])
    loan.save()
    return LoanOut.from_orm(loan)


@router.delete("/{loan_id}/", response=MessageOut)
async def delete_loan(request, loan_id: str):
    """Delete a loan and all its payments."""
    loan = get_object_or_404(Loan, id=loan_id, owner=request.user)
    loan.delete()
    return MessageOut(message="Loan deleted successfully")


# ==================== Loan Payment CRUD ====================


@router.get("/{loan_id}/payments/", response=PaginatedResponse[LoanPaymentOut])
async def list_payments(
    request,
    loan_id: str,
    pagination: PaginationSchema = PaginationSchema(),
):
    """List all payments for a specific loan."""
    loan = get_object_or_404(Loan, id=loan_id, owner=request.user)
    qs = loan.payments.filter(owner=request.user).order_by("payment_number")

    items, total, total_pages = paginate_queryset(
        qs, pagination.page, pagination.per_page
    )
    return PaginatedResponse(
        items=[LoanPaymentOut.from_orm(p) for p in items],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=total_pages,
    )


@router.post("/{loan_id}/payments/", response={201: LoanPaymentOut})
@transaction.atomic
async def create_payment(request, loan_id: str, data: LoanPaymentCreate):
    """Create a payment for a loan.

    Atomically updates the parent Loan's aggregated counters:
    - paid_amount += amount
    - paid_installments += 1
    - current_balance -= principal_component
    - Advances next_payment_date to the following month
    - Auto-completes the loan if all installments are paid
    """
    loan = get_object_or_404(Loan, id=loan_id, owner=request.user)

    if loan.status == Loan.LoanStatus.COMPLETED:
        from ninja.errors import HttpError

        raise HttpError(400, "Cannot add payment to a completed loan")

    payment = LoanPayment.objects.create(
        owner=request.user,
        loan=loan,
        amount=data.amount,
        principal_component=data.principalComponent,
        interest_component=data.interestComponent,
        payment_date=data.paymentDate,
        payment_number=data.paymentNumber,
        bank_account_id=data.bankAccountId,
    )

    # Update parent loan aggregates
    loan.paid_amount = (loan.paid_amount or 0) + data.amount
    loan.paid_installments = (loan.paid_installments or 0) + 1
    loan.current_balance = max((loan.current_balance or 0) - data.principalComponent, 0)

    _advance_next_payment(loan)
    _check_loan_completion(loan)
    loan.save()

    return 201, LoanPaymentOut.from_orm(payment)


@router.get("/{loan_id}/payments/{payment_id}/", response=LoanPaymentOut)
async def get_payment(request, loan_id: str, payment_id: str):
    """Get a specific loan payment."""
    payment = get_object_or_404(
        LoanPayment, id=payment_id, loan_id=loan_id, owner=request.user
    )
    return LoanPaymentOut.from_orm(payment)


@router.put("/{loan_id}/payments/{payment_id}/", response=LoanPaymentOut)
@transaction.atomic
async def update_payment(
    request, loan_id: str, payment_id: str, data: LoanPaymentUpdate
):
    """Update a loan payment.

    If ``amount`` or ``principalComponent`` change, the parent Loan's
    aggregates are recalculated from all payments for consistency.
    """
    payment = get_object_or_404(
        LoanPayment, id=payment_id, loan_id=loan_id, owner=request.user
    )
    loan = payment.loan

    payload = data.model_dump(exclude_unset=True)
    amount_changed = "amount" in payload or "principalComponent" in payload

    for schema_key, model_field in _PAYMENT_FIELD_MAP.items():
        if schema_key in payload:
            setattr(payment, model_field, payload[schema_key])
    payment.save()

    # Recalculate loan aggregates from all payments
    if amount_changed:
        agg = loan.payments.aggregate(
            total_amount=models.Sum("amount"),
            total_principal=models.Sum("principal_component"),
            count=models.Count("id"),
        )
        loan.paid_amount = agg["total_amount"] or 0
        loan.paid_installments = agg["count"] or 0
        loan.current_balance = max(
            (loan.principal_amount or 0) - (agg["total_principal"] or 0), 0
        )
        _check_loan_completion(loan)
        loan.save()

    return LoanPaymentOut.from_orm(payment)


@router.delete("/{loan_id}/payments/{payment_id}/", response=MessageOut)
@transaction.atomic
async def delete_payment(request, loan_id: str, payment_id: str):
    """Delete a loan payment and recalculate parent loan aggregates."""
    payment = get_object_or_404(
        LoanPayment, id=payment_id, loan_id=loan_id, owner=request.user
    )
    loan = payment.loan

    payment.delete()

    # Recalculate loan aggregates from remaining payments
    agg = loan.payments.aggregate(
        total_amount=models.Sum("amount"),
        total_principal=models.Sum("principal_component"),
        count=models.Count("id"),
    )
    loan.paid_amount = agg["total_amount"] or 0
    loan.paid_installments = agg["count"] or 0
    loan.current_balance = max(
        (loan.principal_amount or 0) - (agg["total_principal"] or 0), 0
    )

    # Re-activate if was completed but no longer fully paid
    if (
        loan.status == Loan.LoanStatus.COMPLETED
        and loan.paid_installments < loan.total_installments
    ):
        loan.status = Loan.LoanStatus.ACTIVE

    loan.save()
    return MessageOut(message="Loan payment deleted successfully")
