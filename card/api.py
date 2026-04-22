"""
Card app API endpoints for FinLife Personal Finance SaaS.

All endpoints:
  - Require BearerAuth (JWT) via common.permissions.BearerAuth
  - Filter by request.user for tenant isolation
  - Use paginate_queryset from common.pagination for list endpoints
  - Return camelCase schemas matching frontend interfaces
"""

from typing import Optional

from django.shortcuts import get_object_or_404
from ninja import Query, Router

from common.pagination import PaginatedResponse, PaginationSchema, paginate_queryset
from common.permissions import BearerAuth

from .models import Card
from .schemas import (
    BillingCycleIn,
    CardCreate,
    CardOut,
    CardUpdate,
    MessageOut,
)

router = Router(tags=["Card"])
auth = BearerAuth()

# Mapping: camelCase schema key → snake_case model field
CARD_FIELDS = {
    "bankAccountId": "bank_account_id",
    "name": "name",
    "type": "type",
    "cardNumber": "card_number",
    "holderName": "holder_name",
    "expiryDate": "expiry_date",
    "brand": "brand",
    "creditLimit": "credit_limit",
    "currentBalance": "current_balance",
    "billingCycle": "billing_cycle",
    "dueDate": "due_date",
    "isActive": "is_active",
    "color": "color",
    "currency": "currency",
    "secondaryCurrency": "secondary_currency",
    "secondaryCreditLimit": "secondary_credit_limit",
    "secondaryCurrentBalance": "secondary_current_balance",
}


# ==================== Card Endpoints ====================


@router.get(
    "/",
    auth=auth,
    response=PaginatedResponse[CardOut],
    summary="List all cards",
)
async def list_cards(
    request,
    pagination: PaginationSchema = Query(...),
    type: Optional[str] = Query(None, description="Filter by type: debit|credit"),
    brand: Optional[str] = Query(
        None, description="Filter by brand: visa|mastercard|amex|discover"
    ),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
):
    """
    List all cards for the authenticated user (paginated, filterable).
    Frontend: GET /api/card/
    """
    qs = Card.objects.filter(owner=request.user)

    if type:
        qs = qs.filter(type=type)
    if brand:
        qs = qs.filter(brand=brand)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)

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
    "/",
    auth=auth,
    response={201: CardOut, 400: MessageOut},
    summary="Create a card",
)
async def create_card(request, payload: CardCreate):
    """
    Create a new card.
    Frontend: POST /api/card/
    """
    try:
        data = payload.model_dump()
        create_data = {}
        for schema_key, model_field in CARD_FIELDS.items():
            if schema_key in data:
                val = data[schema_key]
                # Serialize nested BillingCycleIn to dict for JSONField
                if schema_key == "billingCycle" and val is not None:
                    val = val if isinstance(val, dict) else val.model_dump()
                create_data[model_field] = val

        card = Card.objects.create(owner=request.user, **create_data)
    except Exception as e:
        return 400, {"message": str(e)}

    return 201, card


@router.get(
    "/{card_id}/",
    auth=auth,
    response={200: CardOut, 404: MessageOut},
    summary="Get card by ID",
)
async def get_card(request, card_id: str):
    """
    Get a specific card by ID.
    Frontend: GET /api/card/{id}/
    """
    card = get_object_or_404(Card, id=card_id, owner=request.user)
    return card


@router.put(
    "/{card_id}/",
    auth=auth,
    response={200: CardOut, 404: MessageOut},
    summary="Update a card",
)
async def update_card(request, card_id: str, payload: CardUpdate):
    """
    Update a card.
    Frontend: PUT /api/card/{id}/
    """
    card = get_object_or_404(Card, id=card_id, owner=request.user)
    data = payload.model_dump(exclude_unset=True)

    for schema_key, model_field in CARD_FIELDS.items():
        if schema_key in data:
            val = data[schema_key]
            # Serialize nested BillingCycleIn to dict for JSONField
            if schema_key == "billingCycle" and val is not None:
                val = val if isinstance(val, dict) else val.model_dump()
            setattr(card, model_field, val)

    card.save()
    card.refresh_from_db()
    return card


@router.delete(
    "/{card_id}/",
    auth=auth,
    response={200: MessageOut, 404: MessageOut},
    summary="Delete a card",
)
async def delete_card(request, card_id: str):
    """
    Delete a card.
    Frontend: DELETE /api/card/{id}/
    """
    card = get_object_or_404(Card, id=card_id, owner=request.user)
    card.delete()
    return {"message": "Card deleted successfully"}
