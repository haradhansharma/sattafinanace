from datetime import date
from typing import List, Optional

from ninja import Schema


# ==================== Message ====================


class MessageOut(Schema):
    """Generic message response."""

    message: str


# ==================== Lending Payment Schemas ====================


class LendingPaymentOut(Schema):
    """Lending payment response matching frontend LendingPayment type."""

    id: str
    lendingId: str
    amount: int
    paymentDate: str
    paymentNumber: int
    note: Optional[str] = None
    createdAt: str
    updatedAt: str

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_lendingId(obj):
        return str(obj.lending_id)

    @staticmethod
    def resolve_paymentDate(obj):
        return obj.payment_date.isoformat()

    @staticmethod
    def resolve_note(obj):
        return obj.note or None

    @staticmethod
    def resolve_createdAt(obj):
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj):
        return obj.updated_at.isoformat()


class LendingPaymentCreate(Schema):
    """Create a lending payment (repayment)."""

    amount: int
    paymentDate: date
    note: Optional[str] = None


class LendingPaymentUpdate(Schema):
    """Update a lending payment — all fields optional."""

    amount: Optional[int] = None
    paymentDate: Optional[date] = None
    note: Optional[str] = None


# ==================== Lending Schemas ====================


class LendingOut(Schema):
    """Full lending response matching frontend Lending type."""

    id: str
    borrowerName: str
    borrowerPhone: Optional[str] = None
    borrowerEmail: Optional[str] = None
    relationship: str
    principalAmount: int
    currentBalance: int
    interestRate: float
    totalInterestAmount: int
    totalRepayableAmount: int
    totalRepaidAmount: int
    issuedDate: str
    dueDate: Optional[str] = None
    repaymentSchedule: Optional[str] = None
    status: str
    notes: Optional[str] = None
    tags: List[str] = []
    currency: str = "BDT"
    createdAt: str
    updatedAt: str
    payments: List[LendingPaymentOut] = []

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_borrowerName(obj):
        return obj.borrower_name

    @staticmethod
    def resolve_borrowerPhone(obj):
        return obj.borrower_phone or None

    @staticmethod
    def resolve_borrowerEmail(obj):
        return obj.borrower_email or None

    @staticmethod
    def resolve_interestRate(obj):
        return float(obj.interest_rate)

    @staticmethod
    def resolve_issuedDate(obj):
        return obj.issued_date.isoformat()

    @staticmethod
    def resolve_dueDate(obj):
        return obj.due_date.isoformat() if obj.due_date else None

    @staticmethod
    def resolve_repaymentSchedule(obj):
        return obj.repayment_schedule or None

    @staticmethod
    def resolve_notes(obj):
        return obj.notes or None

    @staticmethod
    def resolve_createdAt(obj):
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj):
        return obj.updated_at.isoformat()


class LendingCreate(Schema):
    """Create a new lending record."""

    borrowerName: str
    borrowerPhone: Optional[str] = None
    borrowerEmail: Optional[str] = None
    relationship: str
    principalAmount: int
    currentBalance: Optional[int] = None
    interestRate: float = 0.0
    totalInterestAmount: int = 0
    totalRepayableAmount: Optional[int] = None
    issuedDate: date
    dueDate: Optional[date] = None
    repaymentSchedule: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    currency: str = "BDT"


class LendingUpdate(Schema):
    """Update a lending record — all fields optional."""

    borrowerName: Optional[str] = None
    borrowerPhone: Optional[str] = None
    borrowerEmail: Optional[str] = None
    relationship: Optional[str] = None
    principalAmount: Optional[int] = None
    currentBalance: Optional[int] = None
    interestRate: Optional[float] = None
    totalInterestAmount: Optional[int] = None
    totalRepayableAmount: Optional[int] = None
    dueDate: Optional[date] = None
    repaymentSchedule: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    currency: Optional[str] = None
