"""
Insurance schemas for FinLife SaaS.

All schemas use camelCase matching the frontend TypeScript interfaces exactly.
Django Ninja's resolve_ methods handle the snake_case → camelCase transformation.
"""

from typing import Optional, List
from datetime import date
from decimal import Decimal

from ninja import Schema


# ==================== InsuranceBeneficiary ====================


class InsuranceBeneficiaryOut(Schema):
    """Matches frontend InsuranceBeneficiary interface (output)."""

    id: str
    name: str
    relationship: str
    percentage: int
    phone: Optional[str] = None
    createdAt: str
    updatedAt: str

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
    def resolve_phone(obj):
        return obj.phone or None


class InsuranceBeneficiaryCreate(Schema):
    """Create a beneficiary (input)."""

    name: str
    relationship: str
    percentage: int = 0
    phone: Optional[str] = None


class InsuranceBeneficiaryUpdate(Schema):
    """Update a beneficiary (input)."""

    name: Optional[str] = None
    relationship: Optional[str] = None
    percentage: Optional[int] = None
    phone: Optional[str] = None


# ==================== InsurancePremiumPayment ====================


class InsurancePremiumPaymentOut(Schema):
    """Matches frontend InsurancePremiumPayment interface (output)."""

    id: str
    createdAt: str
    updatedAt: str
    insuranceId: str
    amount: int
    paymentDate: Optional[str] = None
    paymentNumber: int
    note: Optional[str] = None
    bankAccountId: Optional[str] = None

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
    def resolve_insuranceId(obj):
        return str(obj.insurance_id)

    @staticmethod
    def resolve_paymentDate(obj):
        return obj.payment_date.isoformat() if obj.payment_date else None

    @staticmethod
    def resolve_bankAccountId(obj):
        return obj.bank_account_id or None

    @staticmethod
    def resolve_note(obj):
        return obj.note or None

    @staticmethod
    def resolve_paymentNumber(obj):
        return obj.payment_number


class InsurancePremiumPaymentCreate(Schema):
    """Create a premium payment (input)."""

    amount: int = 0
    paymentDate: Optional[date] = None
    paymentNumber: int = 1
    note: Optional[str] = None
    bankAccountId: Optional[str] = None


# ==================== InsuranceClaim ====================


class InsuranceClaimOut(Schema):
    """Matches frontend InsuranceClaim interface (output)."""

    id: str
    createdAt: str
    updatedAt: str
    insuranceId: str
    claimNumber: Optional[str] = None
    claimDate: Optional[str] = None
    claimAmount: int
    approvedAmount: int = 0
    status: str
    description: str = ""
    documents: Optional[str] = None
    resolutionDate: Optional[str] = None
    resolutionNote: Optional[str] = None

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
    def resolve_insuranceId(obj):
        return str(obj.insurance_id)

    @staticmethod
    def resolve_claimDate(obj):
        return obj.claim_date.isoformat() if obj.claim_date else None

    @staticmethod
    def resolve_resolutionDate(obj):
        return obj.resolution_date.isoformat() if obj.resolution_date else None

    @staticmethod
    def resolve_documents(obj):
        return obj.documents or None

    @staticmethod
    def resolve_resolutionNote(obj):
        return obj.resolution_note or None

    @staticmethod
    def resolve_description(obj):
        return obj.description or ""

    @staticmethod
    def resolve_claimNumber(obj):
        return obj.claim_number or None

    @staticmethod
    def resolve_claimAmount(obj):
        return obj.claim_amount

    @staticmethod
    def resolve_approvedAmount(obj):
        return obj.approved_amount


class InsuranceClaimCreate(Schema):
    """Create a claim (input)."""

    claimNumber: Optional[str] = None
    claimDate: Optional[date] = None
    claimAmount: int = 0
    description: str = ""
    documents: Optional[str] = None


class InsuranceClaimUpdate(Schema):
    """Update a claim status/details (input)."""

    status: Optional[str] = None
    approvedAmount: Optional[int] = None
    description: Optional[str] = None
    documents: Optional[str] = None
    resolutionDate: Optional[date] = None
    resolutionNote: Optional[str] = None


# ==================== Insurance ====================


class InsuranceOut(Schema):
    """Matches frontend Insurance interface (output) — 40+ fields."""

    id: str
    createdAt: str
    updatedAt: str

    # --- Core ---
    name: str
    category: str
    provider: str
    policyNumber: str
    groupPolicyNumber: Optional[str] = None

    coverageAmount: int
    premiumAmount: int
    premiumFrequency: str

    # --- Dates ---
    issueDate: Optional[str] = None
    startDate: Optional[str] = None
    expiryDate: Optional[str] = None
    maturityDate: Optional[str] = None
    nextPremiumDueDate: Optional[str] = None

    # --- Totals ---
    totalPremiumPaid: int
    paidPremiumsCount: int
    totalClaimedAmount: int

    status: str
    autoRenew: bool = False

    # --- Life specific ---
    policyTerm: Optional[int] = None
    maturityBenefit: int = 0
    riderNames: List[str] = []

    # --- Health specific ---
    deductibleAmount: int = 0
    copayPercent: Optional[Decimal] = None
    networkHospitals: Optional[str] = None

    # --- Vehicle specific ---
    vehicleType: Optional[str] = None
    vehicleRegistration: Optional[str] = None
    vehicleModel: Optional[str] = None

    # --- Property specific ---
    propertyType: Optional[str] = None
    propertyAddress: Optional[str] = None
    propertyValue: int = 0

    # --- Common ---
    bankAccountId: Optional[str] = None
    currency: str = "BDT"
    notes: Optional[str] = None
    tags: List[str] = []

    # --- Related (embedded FK) ---
    premiumPayments: List[InsurancePremiumPaymentOut] = []
    claims: List[InsuranceClaimOut] = []
    beneficiaries: List[InsuranceBeneficiaryOut] = []

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
    def resolve_policyNumber(obj):
        return obj.policy_number

    @staticmethod
    def resolve_groupPolicyNumber(obj):
        return obj.group_policy_number or None

    @staticmethod
    def resolve_coverageAmount(obj):
        return obj.coverage_amount

    @staticmethod
    def resolve_premiumAmount(obj):
        return obj.premium_amount

    @staticmethod
    def resolve_premiumFrequency(obj):
        return obj.premium_frequency

    @staticmethod
    def resolve_issueDate(obj):
        return obj.issue_date.isoformat() if obj.issue_date else None

    @staticmethod
    def resolve_startDate(obj):
        return obj.start_date.isoformat() if obj.start_date else None

    @staticmethod
    def resolve_expiryDate(obj):
        return obj.expiry_date.isoformat() if obj.expiry_date else None

    @staticmethod
    def resolve_maturityDate(obj):
        return obj.maturity_date.isoformat() if obj.maturity_date else None

    @staticmethod
    def resolve_nextPremiumDueDate(obj):
        return (
            obj.next_premium_due_date.isoformat() if obj.next_premium_due_date else None
        )

    @staticmethod
    def resolve_totalPremiumPaid(obj):
        return obj.total_premium_paid

    @staticmethod
    def resolve_paidPremiumsCount(obj):
        return obj.paid_premiums_count

    @staticmethod
    def resolve_totalClaimedAmount(obj):
        return obj.total_claimed_amount

    @staticmethod
    def resolve_autoRenew(obj):
        return obj.auto_renew

    @staticmethod
    def resolve_policyTerm(obj):
        return obj.policy_term

    @staticmethod
    def resolve_maturityBenefit(obj):
        return obj.maturity_benefit

    @staticmethod
    def resolve_riderNames(obj):
        return obj.rider_names or []

    @staticmethod
    def resolve_deductibleAmount(obj):
        return obj.deductible_amount

    @staticmethod
    def resolve_copayPercent(obj):
        return float(obj.copay_percent) if obj.copay_percent is not None else None

    @staticmethod
    def resolve_networkHospitals(obj):
        return obj.network_hospitals or None

    @staticmethod
    def resolve_vehicleType(obj):
        return obj.vehicle_type

    @staticmethod
    def resolve_vehicleRegistration(obj):
        return obj.vehicle_registration or None

    @staticmethod
    def resolve_vehicleModel(obj):
        return obj.vehicle_model or None

    @staticmethod
    def resolve_propertyType(obj):
        return obj.property_type

    @staticmethod
    def resolve_propertyAddress(obj):
        return obj.property_address or None

    @staticmethod
    def resolve_propertyValue(obj):
        return obj.property_value

    @staticmethod
    def resolve_bankAccountId(obj):
        return obj.bank_account_id or None

    @staticmethod
    def resolve_notes(obj):
        return obj.notes or None

    @staticmethod
    def resolve_tags(obj):
        return obj.tags or []

    @staticmethod
    def resolve_premiumPayments(obj):
        return list(obj.premium_payments.all())

    @staticmethod
    def resolve_claims(obj):
        return list(obj.claims.all())

    @staticmethod
    def resolve_beneficiaries(obj):
        return list(obj.beneficiaries.all())


class InsuranceCreate(Schema):
    """Create an insurance policy (input)."""

    name: str
    category: str
    provider: str
    policyNumber: str
    groupPolicyNumber: Optional[str] = None

    coverageAmount: int = 0
    premiumAmount: int = 0
    premiumFrequency: str = "monthly"

    issueDate: Optional[date] = None
    startDate: Optional[date] = None
    expiryDate: Optional[date] = None
    maturityDate: Optional[date] = None
    nextPremiumDueDate: Optional[date] = None

    totalPremiumPaid: int = 0
    paidPremiumsCount: int = 0
    totalClaimedAmount: int = 0

    status: str = "active"
    autoRenew: bool = False

    # Life specific
    policyTerm: Optional[int] = None
    maturityBenefit: int = 0
    riderNames: List[str] = []

    # Health specific
    deductibleAmount: int = 0
    copayPercent: Optional[Decimal] = None
    networkHospitals: Optional[str] = None

    # Vehicle specific
    vehicleType: Optional[str] = None
    vehicleRegistration: Optional[str] = None
    vehicleModel: Optional[str] = None

    # Property specific
    propertyType: Optional[str] = None
    propertyAddress: Optional[str] = None
    propertyValue: int = 0

    # Common
    bankAccountId: Optional[str] = None
    currency: str = "BDT"
    notes: Optional[str] = None
    tags: List[str] = []


class InsuranceUpdate(Schema):
    """Partial update for an insurance policy (input)."""

    name: Optional[str] = None
    category: Optional[str] = None
    provider: Optional[str] = None
    policyNumber: Optional[str] = None
    groupPolicyNumber: Optional[str] = None

    coverageAmount: Optional[int] = None
    premiumAmount: Optional[int] = None
    premiumFrequency: Optional[str] = None

    issueDate: Optional[date] = None
    startDate: Optional[date] = None
    expiryDate: Optional[date] = None
    maturityDate: Optional[date] = None
    nextPremiumDueDate: Optional[date] = None

    totalPremiumPaid: Optional[int] = None
    paidPremiumsCount: Optional[int] = None
    totalClaimedAmount: Optional[int] = None

    status: Optional[str] = None
    autoRenew: Optional[bool] = None

    # Life specific
    policyTerm: Optional[int] = None
    maturityBenefit: Optional[int] = None
    riderNames: Optional[List[str]] = None

    # Health specific
    deductibleAmount: Optional[int] = None
    copayPercent: Optional[Decimal] = None
    networkHospitals: Optional[str] = None

    # Vehicle specific
    vehicleType: Optional[str] = None
    vehicleRegistration: Optional[str] = None
    vehicleModel: Optional[str] = None

    # Property specific
    propertyType: Optional[str] = None
    propertyAddress: Optional[str] = None
    propertyValue: Optional[int] = None

    # Common
    bankAccountId: Optional[str] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


# ==================== Shared ====================


class MessageOut(Schema):
    message: str
