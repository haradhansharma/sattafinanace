"""
Loan schemas (Django Ninja) — camelCase matching the frontend exactly.

LoanPaymentOut is embedded inside LoanOut via the ``payments`` list.
"""

from datetime import date
from typing import List, Optional

from ninja import Schema


# ==================== Loan Payment Schemas ====================


class LoanPaymentOut(Schema):
    """Output schema for a single loan payment."""

    id: str
    createdAt: str
    updatedAt: str
    loanId: str
    amount: int
    principalComponent: int
    interestComponent: int
    paymentDate: str
    paymentNumber: int
    bankAccountId: Optional[str] = None

    @classmethod
    def from_orm(cls, obj) -> "LoanPaymentOut":
        return cls(
            id=str(obj.id),
            createdAt=obj.created_at.isoformat(),
            updatedAt=obj.updated_at.isoformat(),
            loanId=str(obj.loan_id),
            amount=obj.amount,
            principalComponent=obj.principal_component,
            interestComponent=obj.interest_component,
            paymentDate=obj.payment_date.isoformat() if obj.payment_date else "",
            paymentNumber=obj.payment_number,
            bankAccountId=obj.bank_account_id or None,
        )


class LoanPaymentCreate(Schema):
    """Payload for creating a loan payment."""

    amount: int
    principalComponent: int = 0
    interestComponent: int = 0
    paymentDate: date
    paymentNumber: int
    bankAccountId: Optional[str] = None


class LoanPaymentUpdate(Schema):
    """Payload for patching a loan payment (all optional)."""

    amount: Optional[int] = None
    principalComponent: Optional[int] = None
    interestComponent: Optional[int] = None
    paymentDate: Optional[date] = None
    paymentNumber: Optional[int] = None
    bankAccountId: Optional[str] = None


# ==================== Loan Schemas ====================


class LoanOut(Schema):
    """Full output for a loan with embedded payments."""

    id: str
    createdAt: str
    updatedAt: str
    name: str
    type: str
    lenderName: str
    principalAmount: int
    currentBalance: int
    interestRate: float
    termMonths: int
    emiAmount: int
    startDate: str
    nextPaymentDate: Optional[str] = None
    nextPaymentAmount: int
    paidAmount: int
    paidInstallments: int
    totalInstallments: int
    status: str
    bankAccountId: Optional[str] = None
    currency: str = "BDT"
    notes: Optional[str] = None
    payments: List[LoanPaymentOut] = []

    @classmethod
    def from_orm(cls, obj) -> "LoanOut":
        return cls(
            id=str(obj.id),
            createdAt=obj.created_at.isoformat(),
            updatedAt=obj.updated_at.isoformat(),
            name=obj.name,
            type=obj.type,
            lenderName=obj.lender_name,
            principalAmount=obj.principal_amount,
            currentBalance=obj.current_balance,
            interestRate=float(obj.interest_rate),
            termMonths=obj.term_months,
            emiAmount=obj.emi_amount,
            startDate=obj.start_date.isoformat() if obj.start_date else "",
            nextPaymentDate=(
                obj.next_payment_date.isoformat() if obj.next_payment_date else None
            ),
            nextPaymentAmount=obj.next_payment_amount,
            paidAmount=obj.paid_amount,
            paidInstallments=obj.paid_installments,
            totalInstallments=obj.total_installments,
            status=obj.status,
            bankAccountId=obj.bank_account_id or None,
            currency=obj.currency,
            notes=obj.notes or None,
            payments=[LoanPaymentOut.from_orm(p) for p in obj.payments.all()],
        )


class LoanCreate(Schema):
    """Payload for creating a loan."""

    name: str
    type: str
    lenderName: str
    principalAmount: int
    currentBalance: int = 0
    interestRate: float
    termMonths: int
    emiAmount: int = 0
    startDate: date
    nextPaymentDate: Optional[date] = None
    nextPaymentAmount: int = 0
    totalInstallments: int
    status: str = "active"
    bankAccountId: Optional[str] = None
    currency: str = "BDT"
    notes: Optional[str] = None


class LoanUpdate(Schema):
    """Payload for patching a loan (all optional)."""

    name: Optional[str] = None
    type: Optional[str] = None
    lenderName: Optional[str] = None
    principalAmount: Optional[int] = None
    currentBalance: Optional[int] = None
    interestRate: Optional[float] = None
    termMonths: Optional[int] = None
    emiAmount: Optional[int] = None
    startDate: Optional[date] = None
    nextPaymentDate: Optional[date] = None
    nextPaymentAmount: Optional[int] = None
    totalInstallments: Optional[int] = None
    status: Optional[str] = None
    bankAccountId: Optional[str] = None
    currency: Optional[str] = None
    notes: Optional[str] = None


# ==================== Shared ====================


class MessageOut(Schema):
    message: str
