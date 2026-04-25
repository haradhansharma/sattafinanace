"""
Schemas for the Bank app — all field names in camelCase matching frontend exactly.

Uses model_validator(mode='before') to handle Django model instances via
Pydantic v2.  This avoids the resolve_ static method issue where Pydantic v2
cannot map camelCase schema fields to snake_case Django attributes.

Frontend interfaces:
  BankAccount:   id, bankName, accountNumber, accountName, type, openingBalance,
                 icon?, color?, currency?, isActive, createdAt, updatedAt
  Transaction:   id, type, amount, direction, bankAccountId, toBankAccountId?,
                 categoryId, date, description, referenceId?, tags?, currency?,
                 createdAt, updatedAt
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
# Bank Account Schemas
# ──────────────────────────────────────────────────────────────────────────────


class BankAccountOut(Schema):
    id: str
    bankName: str
    accountNumber: str
    accountName: str
    type: str
    openingBalance: int
    icon: Optional[str] = ""
    color: Optional[str] = ""
    currency: str
    isActive: bool
    createdAt: str
    updatedAt: str

    @model_validator(mode="before")
    @classmethod
    def _from_django(cls, data: Any) -> Any:
        """Convert Django model instance to a dict with camelCase keys."""
        if hasattr(data, "_meta"):
            return {
                "id": str(data.id),
                "bankName": data.bank_name,
                "accountNumber": data.masked_account_number,
                "accountName": data.account_name,
                "type": data.type,
                "openingBalance": data.opening_balance,
                "icon": data.icon,
                "color": data.color,
                "currency": data.currency,
                "isActive": data.is_active,
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


class BankAccountCreate(Schema):
    bankName: str
    accountNumber: str
    accountName: str
    type: str
    openingBalance: int = 0
    icon: Optional[str] = ""
    color: Optional[str] = ""
    currency: str = "BDT"
    isActive: bool = True


class BankAccountUpdate(Schema):
    bankName: Optional[str] = None
    accountNumber: Optional[str] = None
    accountName: Optional[str] = None
    type: Optional[str] = None
    openingBalance: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    currency: Optional[str] = None
    isActive: Optional[bool] = None


# ──────────────────────────────────────────────────────────────────────────────
# Account Balance Schema
# ──────────────────────────────────────────────────────────────────────────────


class AccountBalanceOut(Schema):
    accountId: str
    balance: int


# ──────────────────────────────────────────────────────────────────────────────
# Transaction Schemas
# ──────────────────────────────────────────────────────────────────────────────


class TransactionOut(Schema):
    id: str
    type: str
    amount: int
    direction: str
    bankAccountId: str
    toBankAccountId: Optional[str] = None
    categoryId: Optional[str] = None
    date: str
    description: str
    referenceId: Optional[str] = ""
    tags: Optional[List[str]] = []
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
                "type": data.type,
                "amount": data.amount,
                "direction": data.direction,
                "bankAccountId": str(data.bank_account_id),
                "toBankAccountId": (
                    str(data.to_bank_account_id) if data.to_bank_account_id else None
                ),
                "categoryId": (str(data.category_id) if data.category_id else None),
                "date": (
                    data.date.isoformat()
                    if hasattr(data.date, "isoformat")
                    else str(data.date)
                ),
                "description": data.description,
                "referenceId": data.reference_id,
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


class TransactionCreate(Schema):
    type: str
    amount: int
    direction: Optional[str] = (
        None  # Auto-set from type for income/expense; required for transfer
    )
    bankAccountId: str
    toBankAccountId: Optional[str] = None
    categoryId: Optional[str] = None
    date: str
    description: str = ""
    referenceId: Optional[str] = ""
    tags: Optional[List[str]] = []
    currency: str = "BDT"


class TransactionUpdate(Schema):
    type: Optional[str] = None
    amount: Optional[int] = None
    direction: Optional[str] = None  # Only needed for transfer
    bankAccountId: Optional[str] = None
    toBankAccountId: Optional[str] = None
    categoryId: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None
    referenceId: Optional[str] = None
    tags: Optional[List[str]] = None
    currency: Optional[str] = None
