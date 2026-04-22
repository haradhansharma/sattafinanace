"""
Schemas for the Bank app — all field names in camelCase matching frontend exactly.

Frontend interfaces:
  BankAccount:   id, bankName, accountNumber, accountName, type, openingBalance,
                 icon?, color?, currency?, isActive, createdAt, updatedAt
  Transaction:   id, type, amount, direction, bankAccountId, toBankAccountId?,
                 categoryId, date, description, referenceId?, tags?, currency?,
                 createdAt, updatedAt
"""

from typing import List, Optional

from ninja import Schema


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

    @staticmethod
    def resolve_id(obj) -> str:
        return str(obj.id)

    @staticmethod
    def resolve_bankName(obj) -> str:
        return obj.bank_name

    @staticmethod
    def resolve_accountNumber(obj) -> str:
        return obj.masked_account_number

    @staticmethod
    def resolve_accountName(obj) -> str:
        return obj.account_name

    @staticmethod
    def resolve_openingBalance(obj) -> int:
        return obj.opening_balance

    @staticmethod
    def resolve_isActive(obj) -> bool:
        return obj.is_active

    @staticmethod
    def resolve_createdAt(obj) -> str:
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj) -> str:
        return obj.updated_at.isoformat()


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
    categoryId: str
    date: str
    description: str
    referenceId: Optional[str] = ""
    tags: Optional[List[str]] = []
    currency: str
    createdAt: str
    updatedAt: str

    @staticmethod
    def resolve_id(obj) -> str:
        return str(obj.id)

    @staticmethod
    def resolve_bankAccountId(obj) -> str:
        return str(obj.bank_account_id)

    @staticmethod
    def resolve_toBankAccountId(obj) -> Optional[str]:
        if obj.to_bank_account_id:
            return str(obj.to_bank_account_id)
        return None

    @staticmethod
    def resolve_categoryId(obj) -> str:
        return str(obj.category_id)

    @staticmethod
    def resolve_referenceId(obj) -> str:
        return obj.reference_id

    @staticmethod
    def resolve_date(obj) -> str:
        return obj.date.isoformat()

    @staticmethod
    def resolve_createdAt(obj) -> str:
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj) -> str:
        return obj.updated_at.isoformat()


class TransactionCreate(Schema):
    type: str
    amount: int
    direction: str
    bankAccountId: str
    toBankAccountId: Optional[str] = None
    categoryId: str
    date: str
    description: str = ""
    referenceId: Optional[str] = ""
    tags: Optional[List[str]] = []
    currency: str = "BDT"


class TransactionUpdate(Schema):
    type: Optional[str] = None
    amount: Optional[int] = None
    direction: Optional[str] = None
    bankAccountId: Optional[str] = None
    toBankAccountId: Optional[str] = None
    categoryId: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None
    referenceId: Optional[str] = None
    tags: Optional[List[str]] = None
    currency: Optional[str] = None
