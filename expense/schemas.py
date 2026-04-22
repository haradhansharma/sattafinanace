"""
Expense app schemas for FinLife Personal Finance SaaS.

All schema fields use camelCase to match the frontend TypeScript interfaces exactly.
Ninja's resolve_X static methods handle camelCase → snake_case model mapping.
"""

from typing import List, Optional

from ninja import Schema


# ==================== Message ====================


class MessageOut(Schema):
    """Generic message response."""

    message: str


# ==================== Expense Category Schemas ====================


class ExpenseCategoryOut(Schema):
    """
    ExpenseCategory response matching frontend interface:
      id, createdAt, updatedAt, name, icon, color,
      type ('needs'|'wants'|'savings'|'investments'), budgetLimit?
    """

    id: str
    createdAt: str
    updatedAt: str
    name: str
    icon: str
    color: str
    type: str
    budgetLimit: Optional[int] = None

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_createdAt(obj):
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj):
        return obj.updated_at.isoformat()

    @staticmethod
    def resolve_budgetLimit(obj):
        return obj.budget_limit


class ExpenseCategoryCreate(Schema):
    """Create an expense category."""

    name: str
    icon: str = ""
    color: str = ""
    type: str = "needs"
    budgetLimit: Optional[int] = None


class ExpenseCategoryUpdate(Schema):
    """Update an expense category — all fields optional."""

    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    type: Optional[str] = None
    budgetLimit: Optional[int] = None


# ==================== Expense Schemas ====================


class ExpenseOut(Schema):
    """
    Expense response matching frontend interface:
      id, createdAt, updatedAt, amount, date,
      bankAccountId (FK→BankAccount), cardId? (FK→Card),
      categoryId (FK→ExpenseCategory), transactionId?,
      description, isRecurring, recurringCycle?, tags?, currency?
    """

    id: str
    createdAt: str
    updatedAt: str
    amount: int
    date: str
    bankAccountId: str
    cardId: Optional[str] = None
    categoryId: str
    transactionId: Optional[str] = None
    description: str
    isRecurring: bool
    recurringCycle: Optional[str] = None
    tags: List[str]
    currency: str

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_createdAt(obj):
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj):
        return obj.updated_at.isoformat()

    @staticmethod
    def resolve_date(obj):
        return obj.date.isoformat()

    @staticmethod
    def resolve_bankAccountId(obj):
        return str(obj.bank_account_id)

    @staticmethod
    def resolve_cardId(obj):
        return str(obj.card_id) if obj.card_id else None

    @staticmethod
    def resolve_categoryId(obj):
        return str(obj.category_id)

    @staticmethod
    def resolve_transactionId(obj):
        return str(obj.transaction_id) if obj.transaction_id else None

    @staticmethod
    def resolve_recurringCycle(obj):
        return obj.recurring_cycle

    @staticmethod
    def resolve_tags(obj):
        return obj.tags or []


class ExpenseCreate(Schema):
    """Create an expense."""

    amount: int
    date: str
    bankAccountId: str
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


# ==================== Category Breakdown ====================


class CategoryBreakdownOut(Schema):
    """Expense breakdown by category with totals and percentages."""

    category: ExpenseCategoryOut
    total: int
    percentage: float
