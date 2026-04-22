"""
Card app schemas for FinLife Personal Finance SaaS.

All schema fields use camelCase to match the frontend TypeScript interfaces exactly.
Ninja's resolve_X static methods handle camelCase → snake_case model mapping.
"""

from typing import Optional

from ninja import Schema


# ==================== Message ====================


class MessageOut(Schema):
    """Generic message response."""

    message: str


# ==================== Billing Cycle ====================


class BillingCycleOut(Schema):
    """Nested billingCycle: {start: number, end: number}"""

    start: int
    end: int


class BillingCycleIn(Schema):
    """Input for nested billingCycle."""

    start: int
    end: int


# ==================== Card Schemas ====================


class CardOut(Schema):
    """
    Card response matching frontend interface:
      id, createdAt, updatedAt, bankAccountId (FK→BankAccount),
      name, type ('debit'|'credit'), cardNumber, holderName,
      expiryDate, brand ('visa'|'mastercard'|'amex'|'discover'),
      creditLimit?, currentBalance,
      billingCycle ({start, end}), dueDate, isActive,
      color?, currency?, secondaryCurrency?,
      secondaryCreditLimit?, secondaryCurrentBalance?
    """

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
    def resolve_bankAccountId(obj):
        return str(obj.bank_account_id)

    @staticmethod
    def resolve_cardNumber(obj):
        return obj.card_number

    @staticmethod
    def resolve_holderName(obj):
        return obj.holder_name

    @staticmethod
    def resolve_expiryDate(obj):
        return obj.expiry_date

    @staticmethod
    def resolve_creditLimit(obj):
        return obj.credit_limit

    @staticmethod
    def resolve_currentBalance(obj):
        return obj.current_balance

    @staticmethod
    def resolve_billingCycle(obj):
        cycle = obj.billing_cycle or {"start": 0, "end": 0}
        return BillingCycleOut(start=cycle.get("start", 0), end=cycle.get("end", 0))

    @staticmethod
    def resolve_dueDate(obj):
        return obj.due_date

    @staticmethod
    def resolve_isActive(obj):
        return obj.is_active

    @staticmethod
    def resolve_secondaryCurrency(obj):
        return obj.secondary_currency

    @staticmethod
    def resolve_secondaryCreditLimit(obj):
        return obj.secondary_credit_limit

    @staticmethod
    def resolve_secondaryCurrentBalance(obj):
        return obj.secondary_current_balance


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
