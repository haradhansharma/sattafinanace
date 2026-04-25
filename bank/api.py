"""
Bank API — full CRUD for BankAccount and Transaction.

All endpoints require BearerAuth (JWT).
All querysets are filtered by `request.user` (tenant isolation).
List endpoints use `apaginate_queryset` from `common.pagination`.

Routes (prefixed with /api/bank):
  ── Accounts ──────────────────────────────────────────────
  GET    /accounts/                        List accounts (paginated, filterable)
  POST   /accounts/                        Create account
  GET    /accounts/{account_id}/           Retrieve account
  PUT    /accounts/{account_id}/           Update account
  DELETE /accounts/{account_id}/           Delete account
  GET    /accounts/{account_id}/balance/   Computed balance

  ── Transactions ──────────────────────────────────────────
  GET    /transactions/                    List transactions (paginated, filterable)
  POST   /transactions/                    Create transaction
  GET    /transactions/recent/             Last 10 transactions
  GET    /transactions/{transaction_id}/   Retrieve transaction
  PUT    /transactions/{transaction_id}/   Update transaction
  DELETE /transactions/{transaction_id}/   Delete transaction
"""

from datetime import date
from typing import Optional

from django.shortcuts import aget_object_or_404
from ninja import Router

from common.pagination import (
    PaginatedResponse,
    PaginationSchema,
    apaginate_queryset,
)
from common.permissions import BearerAuth

from .models import BankAccount, Transaction
from .schemas import (
    AccountBalanceOut,
    BankAccountCreate,
    BankAccountOut,
    BankAccountUpdate,
    MessageOut,
    TransactionCreate,
    TransactionOut,
    TransactionUpdate,
)

router = Router(tags=["Bank"])
auth = BearerAuth()


# ══════════════════════════════════════════════════════════════════════════════
# Bank Account Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/accounts/", auth=auth, response=PaginatedResponse[BankAccountOut])
async def list_accounts(
    request,
    page: int = PaginationSchema.__fields__["page"].default,
    per_page: int = PaginationSchema.__fields__["per_page"].default,
    type: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """List all bank accounts for the authenticated user (paginated)."""
    qs = BankAccount.objects.filter(owner=request.user)
    if type:
        qs = qs.filter(type=type)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    items, total, total_pages = await apaginate_queryset(qs, page, per_page)
    return {
        "items": [item async for item in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.post("/accounts/", auth=auth, response={201: BankAccountOut, 400: MessageOut})
async def create_account(request, payload: BankAccountCreate):
    """Create a new bank account."""
    try:
        account = await BankAccount.objects.acreate(
            owner=request.user,
            bank_name=payload.bankName,
            account_number=payload.accountNumber,
            account_name=payload.accountName,
            type=payload.type,
            opening_balance=payload.openingBalance,
            icon=payload.icon or "",
            color=payload.color or "",
            currency=payload.currency,
            is_active=payload.isActive,
        )
    except Exception as e:
        return 400, {"message": str(e)}

    return 201, account


@router.get(
    "/accounts/{account_id}/",
    auth=auth,
    response={200: BankAccountOut, 404: MessageOut},
)
async def get_account(request, account_id: str):
    """Get a specific bank account by ID."""
    account = await aget_object_or_404(BankAccount, id=account_id, owner=request.user)
    return account


@router.put(
    "/accounts/{account_id}/",
    auth=auth,
    response={200: BankAccountOut, 404: MessageOut},
)
async def update_account(request, account_id: str, payload: BankAccountUpdate):
    """Update a bank account."""
    account = await aget_object_or_404(BankAccount, id=account_id, owner=request.user)

    if payload.bankName is not None:
        account.bank_name = payload.bankName
    if payload.accountNumber is not None:
        account.account_number = payload.accountNumber
    if payload.accountName is not None:
        account.account_name = payload.accountName
    if payload.type is not None:
        account.type = payload.type
    if payload.openingBalance is not None:
        account.opening_balance = payload.openingBalance
    if payload.icon is not None:
        account.icon = payload.icon
    if payload.color is not None:
        account.color = payload.color
    if payload.currency is not None:
        account.currency = payload.currency
    if payload.isActive is not None:
        account.is_active = payload.isActive

    await account.asave()
    await account.arefresh_from_db()
    return account


@router.delete(
    "/accounts/{account_id}/", auth=auth, response={200: MessageOut, 404: MessageOut}
)
async def delete_account(request, account_id: str):
    """Delete a bank account and all its transactions (CASCADE)."""
    account = await aget_object_or_404(BankAccount, id=account_id, owner=request.user)
    await account.adelete()
    return {"message": "Bank account deleted successfully."}


# ── Account Balance ──────────────────────────────────────────────────────────


@router.get(
    "/accounts/{account_id}/balance/",
    auth=auth,
    response={200: AccountBalanceOut, 404: MessageOut},
)
async def get_account_balance(request, account_id: str):
    """Get computed balance for a bank account (opening + credits - debits)."""
    account = await aget_object_or_404(BankAccount, id=account_id, owner=request.user)
    return {"accountId": str(account.id), "balance": account.current_balance}


# ── Account Transactions ─────────────────────────────────────────────────────


@router.get(
    "/accounts/{account_id}/transactions/",
    auth=auth,
    response=PaginatedResponse[TransactionOut],
)
async def list_account_transactions(
    request,
    account_id: str,
    page: int = PaginationSchema.__fields__["page"].default,
    per_page: int = PaginationSchema.__fields__["per_page"].default,
    type: Optional[str] = None,
    direction: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """List transactions for a specific bank account (paginated, filterable)."""
    await aget_object_or_404(BankAccount, id=account_id, owner=request.user)

    qs = Transaction.objects.filter(owner=request.user, bank_account_id=account_id)
    if type:
        qs = qs.filter(type=type)
    if direction:
        qs = qs.filter(direction=direction)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    items, total, total_pages = await apaginate_queryset(qs, page, per_page)
    return {
        "items": [item async for item in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Transaction Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/transactions/", auth=auth, response={201: TransactionOut, 400: MessageOut}
)
async def create_transaction(request, payload: TransactionCreate):
    """Create a new transaction."""
    try:
        bank_account = await aget_object_or_404(
            BankAccount, id=payload.bankAccountId, owner=request.user
        )
        to_bank_account = None
        if payload.toBankAccountId:
            to_bank_account = await aget_object_or_404(
                BankAccount, id=payload.toBankAccountId, owner=request.user
            )

        # direction is optional — model.save() auto-sets for income/expense
        direction = payload.direction
        if not direction and payload.type in ("income", "expense"):
            direction = "credit" if payload.type == "income" else "debit"

        transaction = await Transaction.objects.acreate(
            owner=request.user,
            bank_account=bank_account,
            to_bank_account=to_bank_account,
            type=payload.type,
            amount=payload.amount,
            direction=direction or "debit",
            category_id=payload.categoryId,
            date=payload.date,
            description=payload.description,
            reference_id=payload.referenceId or "",
            tags=payload.tags or [],
            currency=payload.currency,
        )
    except Exception as e:
        return 400, {"message": str(e)}

    return 201, transaction


@router.get("/transactions/", auth=auth, response=PaginatedResponse[TransactionOut])
async def list_transactions(
    request,
    page: int = PaginationSchema.__fields__["page"].default,
    per_page: int = PaginationSchema.__fields__["per_page"].default,
    bankAccountId: Optional[str] = None,
    type: Optional[str] = None,
    direction: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """List all transactions for the authenticated user (paginated, filterable)."""
    qs = Transaction.objects.filter(owner=request.user)

    if bankAccountId:
        qs = qs.filter(bank_account_id=bankAccountId)
    if type:
        qs = qs.filter(type=type)
    if direction:
        qs = qs.filter(direction=direction)
    if date_from:
        qs = qs.filter(date__gte=date_from)
    if date_to:
        qs = qs.filter(date__lte=date_to)

    items, total, total_pages = await apaginate_queryset(qs, page, per_page)
    return {
        "items": [item async for item in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.get("/transactions/recent/", auth=auth)
async def list_recent_transactions(request):
    """Get the 10 most recent transactions for the authenticated user."""
    items = [t async for t in Transaction.objects.filter(owner=request.user)[:10]]
    return items


@router.get(
    "/transactions/{transaction_id}/",
    auth=auth,
    response={200: TransactionOut, 404: MessageOut},
)
async def get_transaction(request, transaction_id: str):
    """Get a specific transaction by ID."""
    txn = await aget_object_or_404(Transaction, id=transaction_id, owner=request.user)
    return txn


@router.put(
    "/transactions/{transaction_id}/",
    auth=auth,
    response={200: TransactionOut, 404: MessageOut},
)
async def update_transaction(request, transaction_id: str, payload: TransactionUpdate):
    """Update a transaction."""
    txn = await aget_object_or_404(Transaction, id=transaction_id, owner=request.user)

    if payload.type is not None:
        txn.type = payload.type
    if payload.amount is not None:
        txn.amount = payload.amount
    if payload.direction is not None:
        txn.direction = payload.direction
    if payload.bankAccountId is not None:
        txn.bank_account = await aget_object_or_404(
            BankAccount, id=payload.bankAccountId, owner=request.user
        )
    if payload.toBankAccountId is not None:
        if payload.toBankAccountId:
            txn.to_bank_account = await aget_object_or_404(
                BankAccount, id=payload.toBankAccountId, owner=request.user
            )
        else:
            txn.to_bank_account = None
    if payload.categoryId is not None:
        txn.category_id = payload.categoryId if payload.categoryId else None
    if payload.date is not None:
        txn.date = payload.date
    if payload.description is not None:
        txn.description = payload.description
    if payload.referenceId is not None:
        txn.reference_id = payload.referenceId
    if payload.tags is not None:
        txn.tags = payload.tags
    if payload.currency is not None:
        txn.currency = payload.currency

    await txn.asave()
    await txn.arefresh_from_db()
    return txn


@router.delete(
    "/transactions/{transaction_id}/",
    auth=auth,
    response={200: MessageOut, 404: MessageOut},
)
async def delete_transaction(request, transaction_id: str):
    """Delete a transaction."""
    txn = await aget_object_or_404(Transaction, id=transaction_id, owner=request.user)
    await txn.adelete()
    return {"message": "Transaction deleted successfully."}
