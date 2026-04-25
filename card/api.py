"""
Card API — full CRUD for Card.

All endpoints require BearerAuth (JWT).
All querysets are filtered by `request.user` (tenant isolation).
List endpoints use `apaginate_queryset` from `common.pagination`.

Routes (prefixed with /api/card):
  GET    /                 List cards (paginated, filterable)
  POST   /                 Create card
  GET    /{card_id}/       Retrieve card
  PUT    /{card_id}/       Update card
  DELETE /{card_id}/       Delete card
"""

from typing import Optional

from django.shortcuts import aget_object_or_404
from ninja import Router

from common.pagination import (
    PaginatedResponse,
    PaginationSchema,
    apaginate_queryset,
)
from common.permissions import BearerAuth

from bank.models import BankAccount
from .models import Card
from .schemas import (
    CardCreate,
    CardOut,
    CardUpdate,
    MessageOut,
)

router = Router(tags=["Card"])
auth = BearerAuth()


# ══════════════════════════════════════════════════════════════════════════════
# Card Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/", auth=auth, response=PaginatedResponse[CardOut])
async def list_cards(
    request,
    page: int = PaginationSchema.__fields__["page"].default,
    per_page: int = PaginationSchema.__fields__["per_page"].default,
    type: Optional[str] = None,
    brand: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """List all cards for the authenticated user (paginated, filterable)."""
    qs = Card.objects.filter(owner=request.user)

    if type:
        qs = qs.filter(type=type)
    if brand:
        qs = qs.filter(brand=brand)
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


@router.post("/", auth=auth, response={201: CardOut, 400: MessageOut})
async def create_card(request, payload: CardCreate):
    """Create a new card."""
    try:
        bank_account = await aget_object_or_404(
            BankAccount, id=payload.bankAccountId, owner=request.user
        )

        billing_cycle = (
            payload.billingCycle.model_dump()
            if payload.billingCycle
            else {"start": 1, "end": 30}
        )

        card = await Card.objects.acreate(
            owner=request.user,
            bank_account=bank_account,
            name=payload.name,
            type=payload.type,
            card_number=payload.cardNumber,
            holder_name=payload.holderName,
            expiry_date=payload.expiryDate,
            brand=payload.brand,
            credit_limit=payload.creditLimit,
            current_balance=payload.currentBalance,
            billing_cycle=billing_cycle,
            due_date=payload.dueDate,
            is_active=payload.isActive,
            color=payload.color,
            currency=payload.currency,
            secondary_currency=payload.secondaryCurrency,
            secondary_credit_limit=payload.secondaryCreditLimit,
            secondary_current_balance=payload.secondaryCurrentBalance,
        )
    except Exception as e:
        return 400, {"message": str(e)}

    return 201, card


@router.get("/{card_id}/", auth=auth, response={200: CardOut, 404: MessageOut})
async def get_card(request, card_id: str):
    """Get a specific card by ID."""
    card = await aget_object_or_404(Card, id=card_id, owner=request.user)
    return card


@router.put("/{card_id}/", auth=auth, response={200: CardOut, 404: MessageOut})
async def update_card(request, card_id: str, payload: CardUpdate):
    """Update a card."""
    card = await aget_object_or_404(Card, id=card_id, owner=request.user)

    if payload.bankAccountId is not None:
        card.bank_account = await aget_object_or_404(
            BankAccount, id=payload.bankAccountId, owner=request.user
        )
    if payload.name is not None:
        card.name = payload.name
    if payload.type is not None:
        card.type = payload.type
    if payload.cardNumber is not None:
        card.card_number = payload.cardNumber
    if payload.holderName is not None:
        card.holder_name = payload.holderName
    if payload.expiryDate is not None:
        card.expiry_date = payload.expiryDate
    if payload.brand is not None:
        card.brand = payload.brand
    if payload.creditLimit is not None:
        card.credit_limit = payload.creditLimit
    if payload.currentBalance is not None:
        card.current_balance = payload.currentBalance
    if payload.billingCycle is not None:
        card.billing_cycle = payload.billingCycle.model_dump()
    if payload.dueDate is not None:
        card.due_date = payload.dueDate
    if payload.isActive is not None:
        card.is_active = payload.isActive
    if payload.color is not None:
        card.color = payload.color
    if payload.currency is not None:
        card.currency = payload.currency
    if payload.secondaryCurrency is not None:
        card.secondary_currency = payload.secondaryCurrency
    if payload.secondaryCreditLimit is not None:
        card.secondary_credit_limit = payload.secondaryCreditLimit
    if payload.secondaryCurrentBalance is not None:
        card.secondary_current_balance = payload.secondaryCurrentBalance

    await card.asave()
    await card.arefresh_from_db()
    return card


@router.delete("/{card_id}/", auth=auth, response={200: MessageOut, 404: MessageOut})
async def delete_card(request, card_id: str):
    """Delete a card."""
    card = await aget_object_or_404(Card, id=card_id, owner=request.user)
    await card.adelete()
    return {"message": "Card deleted successfully"}
