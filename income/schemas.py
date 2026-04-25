"""
Schemas for the Income app — all field names in camelCase matching frontend exactly.

Uses model_validator(mode='before') to handle Django model instances via
Pydantic v2 from_attributes.  This avoids the resolve_ static method issue
where Pydantic v2 cannot map camelCase schema fields to snake_case Django
attributes (e.g. isActive → is_active, createdAt → created_at).

Each Out schema detects whether it received a Django model or a plain dict
and normalises accordingly.

Frontend interfaces:
  IncomeSource:   id, name, type, isActive, monthlyAmount?, currency, createdAt, updatedAt
  IncomeCategory: id, name, icon, color, type, createdAt, updatedAt
  Income:         id, sourceId, amount, date, bankAccountId, categoryId,
                  transactionId?, description, isRecurring, recurringCycle?,
                  currency, createdAt, updatedAt
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
# Income Category Schemas
# ──────────────────────────────────────────────────────────────────────────────


class IncomeCategoryOut(Schema):
    id: str
    name: str
    icon: str
    color: str
    type: str
    createdAt: str
    updatedAt: str

    @model_validator(mode="before")
    @classmethod
    def _from_django(cls, data: Any) -> Any:
        """Convert Django model instance to a dict with camelCase keys."""
        if hasattr(data, "_meta"):
            return {
                "id": str(data.id),
                "name": data.name,
                "icon": data.icon,
                "color": data.color,
                "type": data.type,
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
            }
        return data


class IncomeCategoryCreate(Schema):
    name: str
    icon: str = ""
    color: str = ""
    type: str = "salary"


class IncomeCategoryUpdate(Schema):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    type: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Income Source Schemas
# ──────────────────────────────────────────────────────────────────────────────


class IncomeSourceOut(Schema):
    id: str
    name: str
    type: str
    isActive: bool
    monthlyAmount: Optional[int] = None
    currency: str = "BDT"
    createdAt: str
    updatedAt: str

    @model_validator(mode="before")
    @classmethod
    def _from_django(cls, data: Any) -> Any:
        """Convert Django model instance to a dict with camelCase keys."""
        if hasattr(data, "_meta"):
            return {
                "id": str(data.id),
                "name": data.name,
                "type": data.type,
                "isActive": data.is_active,
                "monthlyAmount": data.monthly_amount,
                "currency": data.currency,
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
            }
        return data


class IncomeSourceCreate(Schema):
    name: str
    type: str = "salary"
    isActive: bool = True
    monthlyAmount: Optional[int] = None
    currency: str = "BDT"


class IncomeSourceUpdate(Schema):
    name: Optional[str] = None
    type: Optional[str] = None
    isActive: Optional[bool] = None
    monthlyAmount: Optional[int] = None
    currency: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Income Schemas
# ──────────────────────────────────────────────────────────────────────────────


class IncomeOut(Schema):
    id: str
    sourceId: str
    amount: int
    date: str
    bankAccountId: Optional[str] = None
    categoryId: str
    transactionId: Optional[str] = None
    description: str
    isRecurring: bool
    recurringCycle: Optional[str] = None
    currency: str
    createdAt: str
    updatedAt: str

    @model_validator(mode="before")
    @classmethod
    def _from_django(cls, data: Any) -> Any:
        """Convert Django model instance to a dict with camelCase keys."""
        if hasattr(data, "_meta"):
            return {
                "id": str(data.id),
                "sourceId": str(data.source_id),
                "amount": data.amount,
                "date": (
                    data.date.isoformat()
                    if hasattr(data.date, "isoformat")
                    else str(data.date)
                ),
                "bankAccountId": (
                    str(data.bank_account_id) if data.bank_account_id else None
                ),
                "categoryId": str(data.category_id),
                "transactionId": (
                    str(data.transaction_id) if data.transaction_id else None
                ),
                "description": data.description,
                "isRecurring": data.is_recurring,
                "recurringCycle": data.recurring_cycle,
                "currency": data.currency,
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
            }
        return data


class IncomeCreate(Schema):
    sourceId: str
    amount: int
    date: str
    bankAccountId: Optional[str] = None
    categoryId: str
    transactionId: Optional[str] = None
    description: str = ""
    isRecurring: bool = False
    recurringCycle: Optional[str] = None
    currency: str = "BDT"


class IncomeUpdate(Schema):
    sourceId: Optional[str] = None
    amount: Optional[int] = None
    date: Optional[str] = None
    bankAccountId: Optional[str] = None
    categoryId: Optional[str] = None
    transactionId: Optional[str] = None
    description: Optional[str] = None
    isRecurring: Optional[bool] = None
    recurringCycle: Optional[str] = None
    currency: Optional[str] = None
