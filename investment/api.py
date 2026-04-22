import uuid

from django.shortcuts import get_object_or_404
from ninja import Router, Query
from typing import Optional

from common.permissions import BearerAuth
from common.pagination import PaginatedResponse, PaginationSchema
from common.pagination import paginate_queryset

from .models import Investment, InvestmentTransaction
from .schemas import (
    InvestmentOut,
    InvestmentCreate,
    InvestmentUpdate,
    InvestmentTransactionOut,
    InvestmentTransactionCreate,
    InvestmentTransactionUpdate,
    MessageOut,
)

router = Router(tags=["Investment"])
auth = BearerAuth()

# ==================== Field Mapping: camelCase → snake_case ====================

INVESTMENT_FIELD_MAP = {
    "accountNumber": "account_number",
    "purchaseDate": "purchase_date",
    "maturityDate": "maturity_date",
    "investedAmount": "invested_amount",
    "currentValue": "current_value",
    "totalReturns": "total_returns",
    "avgBuyPrice": "avg_buy_price",
    "currentUnitPrice": "current_unit_price",
    "interestRate": "interest_rate",
    "taxOnInterest": "tax_on_interest",
    "monthlyDepositAmount": "monthly_deposit_amount",
    "totalDepositedSoFar": "total_deposited_so_far",
    "depositCount": "deposit_count",
    "stockSymbol": "stock_symbol",
    "stockExchange": "stock_exchange",
    "dividendYield": "dividend_yield",
    "weightGrams": "weight_grams",
    "autoRenew": "auto_renew",
    "bankAccountId": "bank_account_id",
}

TRANSACTION_FIELD_MAP = {
    "unitPrice": "unit_price",
    "bankAccountId": "bank_account_id",
}


def _map_payload(payload: dict, field_map: dict) -> dict:
    """Convert camelCase keys to snake_case using the given mapping."""
    result = {}
    for key, value in payload.items():
        mapped = field_map.get(key, key)
        result[mapped] = value
    return result


# ==================== Investment CRUD ====================


@router.get("/", auth=auth, response=PaginatedResponse[InvestmentOut])
async def list_investments(
    request,
    pagination: PaginationSchema = Query(...),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """
    List all investments for the authenticated user (paginated).
    Supports filtering by category and status.
    """
    qs = Investment.objects.filter(owner=request.user)

    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)

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


@router.post("/", auth=auth, response={201: InvestmentOut, 400: MessageOut})
async def create_investment(request, payload: InvestmentCreate):
    """Create a new investment."""
    try:
        data = _map_payload(payload.model_dump(), INVESTMENT_FIELD_MAP)
        investment = Investment.objects.create(owner=request.user, **data)
    except Exception as e:
        return 400, {"message": str(e)}

    return 201, investment


@router.get(
    "/{investment_id}/", auth=auth, response={200: InvestmentOut, 404: MessageOut}
)
async def get_investment(request, investment_id: uuid.UUID):
    """Get a single investment by ID with embedded transactions."""
    investment = get_object_or_404(Investment, id=investment_id, owner=request.user)
    return investment


@router.put(
    "/{investment_id}/", auth=auth, response={200: InvestmentOut, 404: MessageOut}
)
async def update_investment(
    request, investment_id: uuid.UUID, payload: InvestmentUpdate
):
    """Update an investment."""
    investment = get_object_or_404(Investment, id=investment_id, owner=request.user)

    data = _map_payload(payload.model_dump(exclude_unset=True), INVESTMENT_FIELD_MAP)
    for field, value in data.items():
        setattr(investment, field, value)

    investment.save()
    investment.refresh_from_db()
    return investment


@router.delete(
    "/{investment_id}/", auth=auth, response={200: MessageOut, 404: MessageOut}
)
async def delete_investment(request, investment_id: uuid.UUID):
    """Delete an investment and all its transactions."""
    investment = get_object_or_404(Investment, id=investment_id, owner=request.user)
    investment.delete()
    return {"message": "Investment deleted successfully"}


# ==================== Investment Transaction CRUD ====================


@router.get(
    "/{investment_id}/transactions/",
    auth=auth,
    response=PaginatedResponse[InvestmentTransactionOut],
)
async def list_investment_transactions(
    request,
    investment_id: uuid.UUID,
    pagination: PaginationSchema = Query(...),
    type: Optional[str] = Query(None),
):
    """
    List transactions for a specific investment (paginated).
    Supports filtering by transaction type.
    """
    get_object_or_404(Investment, id=investment_id, owner=request.user)

    qs = InvestmentTransaction.objects.filter(
        owner=request.user,
        investment_id=investment_id,
    )
    if type:
        qs = qs.filter(type=type)

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
    "/{investment_id}/transactions/",
    auth=auth,
    response={201: InvestmentTransactionOut, 404: MessageOut, 400: MessageOut},
)
async def create_transaction(
    request,
    investment_id: uuid.UUID,
    payload: InvestmentTransactionCreate,
):
    """Create a new transaction for an investment."""
    try:
        investment = get_object_or_404(Investment, id=investment_id, owner=request.user)
        data = _map_payload(payload.model_dump(), TRANSACTION_FIELD_MAP)
        transaction = InvestmentTransaction.objects.create(
            owner=request.user,
            investment=investment,
            **data,
        )
    except Exception as e:
        return 400, {"message": str(e)}

    return 201, transaction


@router.get(
    "/{investment_id}/transactions/{transaction_id}/",
    auth=auth,
    response={200: InvestmentTransactionOut, 404: MessageOut},
)
async def get_transaction(
    request,
    investment_id: uuid.UUID,
    transaction_id: uuid.UUID,
):
    """Get a specific transaction by ID."""
    get_object_or_404(Investment, id=investment_id, owner=request.user)
    txn = get_object_or_404(
        InvestmentTransaction,
        id=transaction_id,
        owner=request.user,
        investment_id=investment_id,
    )
    return txn


@router.put(
    "/{investment_id}/transactions/{transaction_id}/",
    auth=auth,
    response={200: InvestmentTransactionOut, 404: MessageOut, 400: MessageOut},
)
async def update_transaction(
    request,
    investment_id: uuid.UUID,
    transaction_id: uuid.UUID,
    payload: InvestmentTransactionUpdate,
):
    """Update a transaction."""
    get_object_or_404(Investment, id=investment_id, owner=request.user)
    txn = get_object_or_404(
        InvestmentTransaction,
        id=transaction_id,
        owner=request.user,
        investment_id=investment_id,
    )

    data = _map_payload(payload.model_dump(exclude_unset=True), TRANSACTION_FIELD_MAP)
    for field, value in data.items():
        setattr(txn, field, value)

    txn.save()
    txn.refresh_from_db()
    return txn


@router.delete(
    "/{investment_id}/transactions/{transaction_id}/",
    auth=auth,
    response={200: MessageOut, 404: MessageOut},
)
async def delete_transaction(
    request,
    investment_id: uuid.UUID,
    transaction_id: uuid.UUID,
):
    """Delete a transaction."""
    get_object_or_404(Investment, id=investment_id, owner=request.user)
    txn = get_object_or_404(
        InvestmentTransaction,
        id=transaction_id,
        owner=request.user,
        investment_id=investment_id,
    )
    txn.delete()
    return {"message": "Transaction deleted successfully"}
