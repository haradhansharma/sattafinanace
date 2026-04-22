from datetime import date
from decimal import Decimal
from typing import List, Optional

from ninja import Schema


# ==================== Message ====================


class MessageOut(Schema):
    """Generic message response."""

    message: str


# ==================== Investment Transaction Schemas ====================


class InvestmentTransactionOut(Schema):
    """Investment transaction response matching frontend."""

    id: str
    investmentId: str
    type: str
    amount: int
    units: Optional[Decimal] = None
    unitPrice: int = 0
    date: str
    note: Optional[str] = None
    bankAccountId: Optional[str] = None
    createdAt: str
    updatedAt: str

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_investmentId(obj):
        return str(obj.investment_id)

    @staticmethod
    def resolve_date(obj):
        return obj.date.isoformat() if obj.date else ""

    @staticmethod
    def resolve_bankAccountId(obj):
        return str(obj.bank_account_id) if obj.bank_account_id else None

    @staticmethod
    def resolve_createdAt(obj):
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj):
        return obj.updated_at.isoformat()


class InvestmentTransactionCreate(Schema):
    """Create an investment transaction."""

    type: str
    amount: int = 0
    units: Optional[Decimal] = None
    unitPrice: int = 0
    date: date
    note: Optional[str] = None
    bankAccountId: Optional[str] = None


class InvestmentTransactionUpdate(Schema):
    """Update an investment transaction — all fields optional."""

    type: Optional[str] = None
    amount: Optional[int] = None
    units: Optional[Decimal] = None
    unitPrice: Optional[int] = None
    date: Optional[date] = None
    note: Optional[str] = None
    bankAccountId: Optional[str] = None


# ==================== Investment Schemas ====================


class InvestmentOut(Schema):
    """Full investment response matching frontend Investment type."""

    id: str
    name: str
    category: str
    institution: str
    accountNumber: Optional[str] = None
    purchaseDate: str
    maturityDate: Optional[str] = None
    investedAmount: int
    currentValue: int
    totalReturns: int
    quantity: Optional[Decimal] = None
    avgBuyPrice: int = 0
    currentUnitPrice: int = 0
    interestRate: Optional[Decimal] = None
    compounding: Optional[str] = None
    taxOnInterest: bool = False
    monthlyDepositAmount: int = 0
    totalDepositedSoFar: int = 0
    depositCount: int = 0
    stockSymbol: Optional[str] = None
    stockExchange: Optional[str] = None
    dividendYield: Optional[Decimal] = None
    purity: Optional[str] = None
    weightGrams: Optional[Decimal] = None
    status: str
    autoRenew: bool = False
    bankAccountId: Optional[str] = None
    currency: str = "BDT"
    notes: Optional[str] = None
    tags: List[str] = []
    createdAt: str
    updatedAt: str
    transactions: List[InvestmentTransactionOut] = []

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_accountNumber(obj):
        return obj.account_number or None

    @staticmethod
    def resolve_purchaseDate(obj):
        return obj.purchase_date.isoformat() if obj.purchase_date else ""

    @staticmethod
    def resolve_maturityDate(obj):
        return obj.maturity_date.isoformat() if obj.maturity_date else None

    @staticmethod
    def resolve_compounding(obj):
        return obj.compounding or None

    @staticmethod
    def resolve_stockSymbol(obj):
        return obj.stock_symbol or None

    @staticmethod
    def resolve_stockExchange(obj):
        return obj.stock_exchange or None

    @staticmethod
    def resolve_purity(obj):
        return obj.purity or None

    @staticmethod
    def resolve_bankAccountId(obj):
        return str(obj.bank_account_id) if obj.bank_account_id else None

    @staticmethod
    def resolve_notes(obj):
        return obj.notes or None

    @staticmethod
    def resolve_createdAt(obj):
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj):
        return obj.updated_at.isoformat()


class InvestmentCreate(Schema):
    """Create a new investment."""

    name: str
    category: str
    institution: str
    accountNumber: Optional[str] = None
    purchaseDate: date
    maturityDate: Optional[date] = None
    investedAmount: int = 0
    currentValue: int = 0
    totalReturns: int = 0
    quantity: Optional[Decimal] = None
    avgBuyPrice: int = 0
    currentUnitPrice: int = 0
    interestRate: Optional[Decimal] = None
    compounding: Optional[str] = None
    taxOnInterest: bool = False
    monthlyDepositAmount: int = 0
    totalDepositedSoFar: int = 0
    depositCount: int = 0
    stockSymbol: Optional[str] = None
    stockExchange: Optional[str] = None
    dividendYield: Optional[Decimal] = None
    purity: Optional[str] = None
    weightGrams: Optional[Decimal] = None
    status: str = "active"
    autoRenew: bool = False
    bankAccountId: Optional[str] = None
    currency: str = "BDT"
    notes: Optional[str] = None
    tags: List[str] = []


class InvestmentUpdate(Schema):
    """Update an investment — all fields optional."""

    name: Optional[str] = None
    category: Optional[str] = None
    institution: Optional[str] = None
    accountNumber: Optional[str] = None
    purchaseDate: Optional[date] = None
    maturityDate: Optional[date] = None
    investedAmount: Optional[int] = None
    currentValue: Optional[int] = None
    totalReturns: Optional[int] = None
    quantity: Optional[Decimal] = None
    avgBuyPrice: Optional[int] = None
    currentUnitPrice: Optional[int] = None
    interestRate: Optional[Decimal] = None
    compounding: Optional[str] = None
    taxOnInterest: Optional[bool] = None
    monthlyDepositAmount: Optional[int] = None
    totalDepositedSoFar: Optional[int] = None
    depositCount: Optional[int] = None
    stockSymbol: Optional[str] = None
    stockExchange: Optional[str] = None
    dividendYield: Optional[Decimal] = None
    purity: Optional[str] = None
    weightGrams: Optional[Decimal] = None
    status: Optional[str] = None
    autoRenew: Optional[bool] = None
    bankAccountId: Optional[str] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
