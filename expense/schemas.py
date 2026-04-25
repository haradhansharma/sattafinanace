"""
Expense app schemas for FinLife Personal Finance SaaS.

All schema fields use camelCase to match the frontend TypeScript interfaces exactly.
Uses model_validator(mode='before') to handle Django model instances via
Pydantic v2.  This avoids the resolve_ static method issue where Pydantic v2
cannot map camelCase schema fields to snake_case Django attributes.

Each Out schema detects whether it received a Django model or a plain dict
and normalises accordingly.

Frontend interfaces:
  ExpenseCategory: id, createdAt, updatedAt, name, icon, color,
                   type ('needs'|'wants'|'savings'|'investments'),
                   budgetLimit?, currency?
  Expense:         id, createdAt, updatedAt, amount, date,
                   bankAccountId?, cardId?, categoryId, transactionId?,
                   description, isRecurring, recurringCycle?, tags?, currency?
"""

from typing import Optional, Any, List

from ninja import Schema
from pydantic import model_validator


# ──────────────────────────────────────────────────────────────────────────────
# Shared
# ──────────────────────────────────────────────────────────────────────────────


class MessageOut(Schema):
    """Generic message response."""

    message: str


# ──────────────────────────────────────────────────────────────────────────────
# Expense Category Schemas
# ──────────────────────────────────────────────────────────────────────────────


class ExpenseCategoryOut(Schema):
    id: str
    createdAt: str
    updatedAt: str
    name: str
    icon: str
    color: str
    type: str
    budgetLimit: Optional[int] = None
    currency: Optional[str] = None

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
                "budgetLimit": data.budget_limit,
                "currency": getattr(data, "currency", "BDT") or None,
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


class ExpenseCategoryCreate(Schema):
    """Create an expense category."""

    name: str
    icon: str = ""
    color: str = ""
    type: str = "needs"
    budgetLimit: Optional[int] = None
    currency: str = "BDT"


class ExpenseCategoryUpdate(Schema):
    """Update an expense category — all fields optional."""

    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    type: Optional[str] = None
    budgetLimit: Optional[int] = None
    currency: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Expense Schemas
# ──────────────────────────────────────────────────────────────────────────────


class ExpenseOut(Schema):
    id: str
    createdAt: str
    updatedAt: str
    amount: int
    date: str
    bankAccountId: Optional[str] = None
    cardId: Optional[str] = None
    categoryId: str
    transactionId: Optional[str] = None
    description: str
    isRecurring: bool
    recurringCycle: Optional[str] = None
    tags: List[str]
    currency: str

    @model_validator(mode="before")
    @classmethod
    def _from_django(cls, data: Any) -> Any:
        """Convert Django model instance to a dict with camelCase keys."""
        if hasattr(data, "_meta"):
            return {
                "id": str(data.id),
                "amount": data.amount,
                "date": (
                    data.date.isoformat()
                    if hasattr(data.date, "isoformat")
                    else str(data.date)
                ),
                "bankAccountId": (
                    str(data.bank_account_id) if data.bank_account_id else None
                ),
                "cardId": str(data.card_id) if data.card_id else None,
                "categoryId": str(data.category_id),
                "transactionId": (
                    str(data.transaction_id) if data.transaction_id else None
                ),
                "description": data.description,
                "isRecurring": data.is_recurring,
                "recurringCycle": data.recurring_cycle,
                "tags": data.tags or [],
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


class ExpenseCreate(Schema):
    """Create an expense."""

    amount: int
    date: str
    bankAccountId: Optional[str] = None
    cardId: Optional[str] = None
    categoryId: str
    transactionId: Optional[str] = None
    description: str = ""
    isRecurring: bool = False
    recurringCycle: Optional[str] = None
    tags: List[str] = []
    currency: str = "BDT"


class ExpenseUpdate(Schema):
    """Update an expense — all fields optional."""

    amount: Optional[int] = None
    date: Optional[str] = None
    bankAccountId: Optional[str] = None
    cardId: Optional[str] = None
    categoryId: Optional[str] = None
    transactionId: Optional[str] = None
    description: Optional[str] = None
    isRecurring: Optional[bool] = None
    recurringCycle: Optional[str] = None
    tags: Optional[List[str]] = None
    currency: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Category Breakdown
# ──────────────────────────────────────────────────────────────────────────────


class CategoryBreakdownOut(Schema):
    """Expense breakdown by category with totals and percentages."""

    category: ExpenseCategoryOut
    total: int
    percentage: float
