"""
Mortgage schemas for FinLife SaaS.

All schemas use camelCase matching the frontend TypeScript interfaces exactly.
Django Ninja's resolve_ methods handle the snake_case → camelCase transformation.
Embedded sub-objects (MortgageProperty, MortgageEscrow, HeldMortgageCollateral)
use separate Schema classes that map from JSONField data.
"""

from typing import Optional, List
from datetime import date

from ninja import Schema


# ==================== MortgageProperty (embedded JSONField) ====================


class MortgagePropertySchema(Schema):
    """Matches frontend MortgageProperty interface."""

    name: str = ""
    propertyType: str = ""
    address: str = ""
    sizeSqft: Optional[int] = None
    purchasePrice: int = 0
    currentMarketValue: Optional[int] = None
    purchaseDate: str = ""


# ==================== MortgageEscrow (embedded JSONField) ====================


class MortgageEscrowSchema(Schema):
    """Matches frontend MortgageEscrow interface."""

    propertyTaxAnnual: int = 0
    insuranceAnnual: int = 0
    monthlyEscrow: int = 0


# ==================== Mortgage Output ====================


class MortgageOut(Schema):
    """Matches frontend Mortgage interface (output)."""

    id: str
    createdAt: str
    updatedAt: str
    property: MortgagePropertySchema
    lenderName: str
    loanAmount: int
    downPayment: int
    downPaymentPercent: float
    currentBalance: int
    interestRate: float
    interestType: str
    termMonths: int
    emiAmount: int
    startDate: Optional[str] = None
    nextPaymentDate: Optional[str] = None
    paidAmount: int
    paidInstallments: int
    totalInstallments: int
    status: str
    escrow: MortgageEscrowSchema
    bankAccountId: Optional[str] = None
    currency: str = "BDT"
    notes: Optional[str] = None

    # --- resolve_ methods (Django Ninja convention) ---

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
    def resolve_property(obj):
        data = obj.property or {}
        return MortgagePropertySchema(
            name=data.get("name", ""),
            propertyType=data.get("propertyType", ""),
            address=data.get("address", ""),
            sizeSqft=data.get("sizeSqft"),
            purchasePrice=data.get("purchasePrice", 0),
            currentMarketValue=data.get("currentMarketValue"),
            purchaseDate=data.get("purchaseDate", ""),
        )

    @staticmethod
    def resolve_lenderName(obj):
        return obj.lender_name

    @staticmethod
    def resolve_loanAmount(obj):
        return obj.loan_amount

    @staticmethod
    def resolve_downPayment(obj):
        return obj.down_payment

    @staticmethod
    def resolve_downPaymentPercent(obj):
        return float(obj.down_payment_percent)

    @staticmethod
    def resolve_currentBalance(obj):
        return obj.current_balance

    @staticmethod
    def resolve_interestRate(obj):
        return float(obj.interest_rate)

    @staticmethod
    def resolve_termMonths(obj):
        return obj.term_months

    @staticmethod
    def resolve_emiAmount(obj):
        return obj.emi_amount

    @staticmethod
    def resolve_startDate(obj):
        return obj.start_date.isoformat() if obj.start_date else None

    @staticmethod
    def resolve_nextPaymentDate(obj):
        return obj.next_payment_date.isoformat() if obj.next_payment_date else None

    @staticmethod
    def resolve_paidAmount(obj):
        return obj.paid_amount

    @staticmethod
    def resolve_paidInstallments(obj):
        return obj.paid_installments

    @staticmethod
    def resolve_totalInstallments(obj):
        return obj.total_installments

    @staticmethod
    def resolve_escrow(obj):
        data = obj.escrow or {}
        return MortgageEscrowSchema(
            propertyTaxAnnual=data.get("propertyTaxAnnual", 0),
            insuranceAnnual=data.get("insuranceAnnual", 0),
            monthlyEscrow=data.get("monthlyEscrow", 0),
        )

    @staticmethod
    def resolve_bankAccountId(obj):
        return obj.bank_account_id or None

    @staticmethod
    def resolve_interestType(obj):
        return obj.interest_type


class MortgageCreate(Schema):
    """Create a new mortgage (input)."""

    property: Optional[MortgagePropertySchema] = None
    lenderName: str
    loanAmount: int = 0
    downPayment: int = 0
    downPaymentPercent: float = 0
    currentBalance: int = 0
    interestRate: float = 0
    interestType: str = "fixed"
    termMonths: int = 0
    emiAmount: int = 0
    startDate: Optional[date] = None
    nextPaymentDate: Optional[date] = None
    totalInstallments: int = 0
    status: str = "active"
    escrow: Optional[MortgageEscrowSchema] = None
    bankAccountId: Optional[str] = None
    currency: str = "BDT"
    notes: Optional[str] = None


class MortgageUpdate(Schema):
    """Partial update for a mortgage (input)."""

    property: Optional[MortgagePropertySchema] = None
    lenderName: Optional[str] = None
    loanAmount: Optional[int] = None
    downPayment: Optional[int] = None
    downPaymentPercent: Optional[float] = None
    currentBalance: Optional[int] = None
    interestRate: Optional[float] = None
    interestType: Optional[str] = None
    termMonths: Optional[int] = None
    emiAmount: Optional[int] = None
    startDate: Optional[date] = None
    nextPaymentDate: Optional[date] = None
    totalInstallments: Optional[int] = None
    status: Optional[str] = None
    escrow: Optional[MortgageEscrowSchema] = None
    bankAccountId: Optional[str] = None
    currency: Optional[str] = None
    notes: Optional[str] = None


# ==================== HeldMortgageCollateral (embedded JSONField) ====================


class HeldMortgageCollateralSchema(Schema):
    """Matches frontend HeldMortgageCollateral interface."""

    name: str = ""
    propertyType: str = ""
    address: str = ""
    sizeSqft: Optional[int] = None
    appraisedValue: int = 0
    currentValue: int = 0
    documents: Optional[str] = None


# ==================== HeldMortgagePayment ====================


class HeldMortgagePaymentOut(Schema):
    """Matches frontend HeldMortgagePayment interface (output)."""

    id: str
    createdAt: str
    updatedAt: str
    heldMortgageId: str
    amount: int
    principalComponent: int
    interestComponent: int
    paymentDate: Optional[str] = None
    paymentNumber: int
    note: Optional[str] = None

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
    def resolve_heldMortgageId(obj):
        return str(obj.held_mortgage_id)

    @staticmethod
    def resolve_paymentDate(obj):
        return obj.payment_date.isoformat() if obj.payment_date else None

    @staticmethod
    def resolve_principalComponent(obj):
        return obj.principal_component

    @staticmethod
    def resolve_interestComponent(obj):
        return obj.interest_component

    @staticmethod
    def resolve_paymentNumber(obj):
        return obj.payment_number


class HeldMortgagePaymentCreate(Schema):
    """Create a held mortgage payment (input)."""

    amount: int = 0
    principalComponent: int = 0
    interestComponent: int = 0
    paymentDate: Optional[date] = None
    paymentNumber: int = 0
    note: Optional[str] = None


# ==================== HeldMortgage ====================


class HeldMortgageOut(Schema):
    """Matches frontend HeldMortgage interface (output)."""

    id: str
    createdAt: str
    updatedAt: str
    borrowerName: str
    borrowerPhone: Optional[str] = None
    borrowerEmail: Optional[str] = None
    borrowerAddress: Optional[str] = None
    relationship: str
    collateral: HeldMortgageCollateralSchema
    loanAmount: int
    currentBalance: int
    interestRate: float
    interestType: str
    termMonths: int
    expectedMonthlyPayment: int
    startDate: Optional[str] = None
    nextPaymentDueDate: Optional[str] = None
    totalReceivedAmount: int
    totalInterestEarned: int
    receivedInstallments: int
    totalInstallments: int
    status: str
    payments: List[HeldMortgagePaymentOut] = []
    latePaymentPenaltyRate: float
    gracePeriodDays: int
    bankAccountId: Optional[str] = None
    currency: str = "BDT"
    notes: Optional[str] = None

    # --- resolve_ methods ---

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
    def resolve_borrowerName(obj):
        return obj.borrower_name

    @staticmethod
    def resolve_borrowerPhone(obj):
        return obj.borrower_phone or None

    @staticmethod
    def resolve_borrowerEmail(obj):
        return obj.borrower_email or None

    @staticmethod
    def resolve_borrowerAddress(obj):
        return obj.borrower_address or None

    @staticmethod
    def resolve_collateral(obj):
        data = obj.collateral or {}
        return HeldMortgageCollateralSchema(
            name=data.get("name", ""),
            propertyType=data.get("propertyType", ""),
            address=data.get("address", ""),
            sizeSqft=data.get("sizeSqft"),
            appraisedValue=data.get("appraisedValue", 0),
            currentValue=data.get("currentValue", 0),
            documents=data.get("documents"),
        )

    @staticmethod
    def resolve_loanAmount(obj):
        return obj.loan_amount

    @staticmethod
    def resolve_currentBalance(obj):
        return obj.current_balance

    @staticmethod
    def resolve_interestRate(obj):
        return float(obj.interest_rate)

    @staticmethod
    def resolve_termMonths(obj):
        return obj.term_months

    @staticmethod
    def resolve_expectedMonthlyPayment(obj):
        return obj.expected_monthly_payment

    @staticmethod
    def resolve_startDate(obj):
        return obj.start_date.isoformat() if obj.start_date else None

    @staticmethod
    def resolve_nextPaymentDueDate(obj):
        return (
            obj.next_payment_due_date.isoformat() if obj.next_payment_due_date else None
        )

    @staticmethod
    def resolve_totalReceivedAmount(obj):
        return obj.total_received_amount

    @staticmethod
    def resolve_totalInterestEarned(obj):
        return obj.total_interest_earned

    @staticmethod
    def resolve_receivedInstallments(obj):
        return obj.received_installments

    @staticmethod
    def resolve_totalInstallments(obj):
        return obj.total_installments

    @staticmethod
    def resolve_latePaymentPenaltyRate(obj):
        return float(obj.late_payment_penalty_rate)

    @staticmethod
    def resolve_gracePeriodDays(obj):
        return obj.grace_period_days

    @staticmethod
    def resolve_bankAccountId(obj):
        return obj.bank_account_id or None

    @staticmethod
    def resolve_interestType(obj):
        return obj.interest_type

    @staticmethod
    def resolve_payments(obj):
        return list(obj.payments.all())


class HeldMortgageCreate(Schema):
    """Create a held mortgage (input)."""

    borrowerName: str
    borrowerPhone: Optional[str] = None
    borrowerEmail: Optional[str] = None
    borrowerAddress: Optional[str] = None
    relationship: str = "other"
    collateral: Optional[HeldMortgageCollateralSchema] = None
    loanAmount: int = 0
    currentBalance: int = 0
    interestRate: float = 0
    interestType: str = "fixed"
    termMonths: int = 0
    expectedMonthlyPayment: int = 0
    startDate: Optional[date] = None
    nextPaymentDueDate: Optional[date] = None
    totalInstallments: int = 0
    status: str = "active"
    latePaymentPenaltyRate: float = 0
    gracePeriodDays: int = 0
    bankAccountId: Optional[str] = None
    currency: str = "BDT"
    notes: Optional[str] = None


class HeldMortgageUpdate(Schema):
    """Partial update for a held mortgage (input)."""

    borrowerName: Optional[str] = None
    borrowerPhone: Optional[str] = None
    borrowerEmail: Optional[str] = None
    borrowerAddress: Optional[str] = None
    relationship: Optional[str] = None
    collateral: Optional[HeldMortgageCollateralSchema] = None
    loanAmount: Optional[int] = None
    currentBalance: Optional[int] = None
    interestRate: Optional[float] = None
    interestType: Optional[str] = None
    termMonths: Optional[int] = None
    expectedMonthlyPayment: Optional[int] = None
    startDate: Optional[date] = None
    nextPaymentDueDate: Optional[date] = None
    totalInstallments: Optional[int] = None
    status: Optional[str] = None
    latePaymentPenaltyRate: Optional[float] = None
    gracePeriodDays: Optional[int] = None
    bankAccountId: Optional[str] = None
    currency: Optional[str] = None
    notes: Optional[str] = None


# ==================== Shared ====================


class MessageOut(Schema):
    message: str
