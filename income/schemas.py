"""
Schemas for the Income app — all field names in camelCase matching frontend exactly.

Frontend interfaces:
  IncomeSource:   id, name, type, isActive, monthlyAmount?, createdAt, updatedAt
  IncomeCategory: id, name, icon, color, type, createdAt, updatedAt
  Income:         id, sourceId, amount, date, bankAccountId, categoryId,
                  transactionId?, description, isRecurring, recurringCycle?,
                  currency?, createdAt, updatedAt
"""

from typing import Optional

from ninja import Schema


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

    @staticmethod
    def resolve_id(obj) -> str:
        return str(obj.id)

    @staticmethod
    def resolve_createdAt(obj) -> str:
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj) -> str:
        return obj.updated_at.isoformat()


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
    createdAt: str
    updatedAt: str

    @staticmethod
    def resolve_id(obj) -> str:
        return str(obj.id)

    @staticmethod
    def resolve_isActive(obj) -> bool:
        return obj.is_active

    @staticmethod
    def resolve_monthlyAmount(obj) -> Optional[int]:
        return obj.monthly_amount

    @staticmethod
    def resolve_createdAt(obj) -> str:
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj) -> str:
        return obj.updated_at.isoformat()


class IncomeSourceCreate(Schema):
    name: str
    type: str = "salary"
    isActive: bool = True
    monthlyAmount: Optional[int] = None


class IncomeSourceUpdate(Schema):
    name: Optional[str] = None
    type: Optional[str] = None
    isActive: Optional[bool] = None
    monthlyAmount: Optional[int] = None


# ──────────────────────────────────────────────────────────────────────────────
# Income Schemas
# ──────────────────────────────────────────────────────────────────────────────


class IncomeOut(Schema):
    id: str
    sourceId: str
    amount: int
    date: str
    bankAccountId: str
    categoryId: str
    transactionId: Optional[str] = None
    description: str
    isRecurring: bool
    recurringCycle: Optional[str] = None
    currency: str
    createdAt: str
    updatedAt: str

    @staticmethod
    def resolve_id(obj) -> str:
        return str(obj.id)

    @staticmethod
    def resolve_sourceId(obj) -> str:
        return str(obj.source_id)

    @staticmethod
    def resolve_date(obj) -> str:
        return obj.date.isoformat()

    @staticmethod
    def resolve_bankAccountId(obj) -> str:
        return str(obj.bank_account_id)

    @staticmethod
    def resolve_categoryId(obj) -> str:
        return str(obj.category_id)

    @staticmethod
    def resolve_transactionId(obj) -> Optional[str]:
        return str(obj.transaction_id) if obj.transaction_id else None

    @staticmethod
    def resolve_isRecurring(obj) -> bool:
        return obj.is_recurring

    @staticmethod
    def resolve_recurringCycle(obj) -> Optional[str]:
        return obj.recurring_cycle

    @staticmethod
    def resolve_createdAt(obj) -> str:
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj) -> str:
        return obj.updated_at.isoformat()


class IncomeCreate(Schema):
    sourceId: str
    amount: int
    date: str
    bankAccountId: str
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
