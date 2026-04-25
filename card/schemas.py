"""
Schemas for the Card app — all field names in camelCase matching frontend exactly.

Uses model_validator(mode='before') to handle Django model instances via
Pydantic v2.  This avoids the resolve_ static method issue where Pydantic v2
cannot map camelCase schema fields to snake_case Django attributes.

Frontend interface:
  Card: id, createdAt, updatedAt, bankAccountId, name, type ('debit'|'credit'),
        cardNumber, holderName, expiryDate, brand ('visa'|'mastercard'|'amex'|'discover'),
        creditLimit?, currentBalance, billingCycle ({start, end}), dueDate,
        isActive, color?, currency?, secondaryCurrency?,
        secondaryCreditLimit?, secondaryCurrentBalance?
"""

from typing import Optional, Any

from ninja import Schema
from pydantic import model_validator


# ──────────────────────────────────────────────────────────────────────────────
# Shared
# ──────────────────────────────────────────────────────────────────────────────


class MessageOut(Schema):
    """Generic message response."""

    message: str


# ──────────────────────────────────────────────────────────────────────────────
# Billing Cycle
# ──────────────────────────────────────────────────────────────────────────────


class BillingCycleOut(Schema):
    """Nested billingCycle: {start: number, end: number}"""

    start: int
    end: int


class BillingCycleIn(Schema):
    """Input for nested billingCycle."""

    start: int
    end: int


# ──────────────────────────────────────────────────────────────────────────────
# Card Schemas
# ──────────────────────────────────────────────────────────────────────────────


class CardOut(Schema):
    id: str
    createdAt: str
    updatedAt: str
    bankAccountId: str
    name: str
    type: str
    cardNumber: str
    holderName: str
    expiryDate: str
    brand: str
    creditLimit: Optional[int] = None
    currentBalance: int
    billingCycle: BillingCycleOut
    dueDate: int
    isActive: bool
    color: Optional[str] = None
    currency: str
    secondaryCurrency: Optional[str] = None
    secondaryCreditLimit: Optional[int] = None
    secondaryCurrentBalance: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def _from_django(cls, data: Any) -> Any:
        """Convert Django model instance to a dict with camelCase keys."""
        if hasattr(data, "_meta"):
            cycle = data.billing_cycle or {"start": 0, "end": 0}
            return {
                "id": str(data.id),
                "createdAt": (
                    data.created_at.isoformat()
                    if hasattr(data.created_at, "isoformat")
                    else str(data.created_at)
                ),
                "updatedAt": (
                    data.updated_at.isoformat()
                    if hasattr(data.updated_at, "isoformat")
                    else str(data.updated_at)
                ),
                "bankAccountId": str(data.bank_account_id),
                "name": data.name,
                "type": data.type,
                "cardNumber": data.card_number,
                "holderName": data.holder_name,
                "expiryDate": data.expiry_date,
                "brand": data.brand,
                "creditLimit": data.credit_limit,
                "currentBalance": data.current_balance,
                "billingCycle": BillingCycleOut(
                    start=cycle.get("start", 0),
                    end=cycle.get("end", 0),
                ),
                "dueDate": data.due_date,
                "isActive": data.is_active,
                "color": data.color,
                "currency": data.currency,
                "secondaryCurrency": data.secondary_currency,
                "secondaryCreditLimit": data.secondary_credit_limit,
                "secondaryCurrentBalance": data.secondary_current_balance,
            }
        return data


class CardCreate(Schema):
    """Create a card."""

    bankAccountId: str
    name: str
    type: str
    cardNumber: str
    holderName: str
    expiryDate: str
    brand: str
    creditLimit: Optional[int] = None
    currentBalance: int = 0
    billingCycle: Optional[BillingCycleIn] = None
    dueDate: int = 1
    isActive: bool = True
    color: Optional[str] = None
    currency: str = "BDT"
    secondaryCurrency: Optional[str] = None
    secondaryCreditLimit: Optional[int] = None
    secondaryCurrentBalance: Optional[int] = None


class CardUpdate(Schema):
    """Update a card — all fields optional."""

    bankAccountId: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    cardNumber: Optional[str] = None
    holderName: Optional[str] = None
    expiryDate: Optional[str] = None
    brand: Optional[str] = None
    creditLimit: Optional[int] = None
    currentBalance: Optional[int] = None
    billingCycle: Optional[BillingCycleIn] = None
    dueDate: Optional[int] = None
    isActive: Optional[bool] = None
    color: Optional[str] = None
    currency: Optional[str] = None
    secondaryCurrency: Optional[str] = None
    secondaryCreditLimit: Optional[int] = None
    secondaryCurrentBalance: Optional[int] = None
