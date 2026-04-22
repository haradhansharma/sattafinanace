"""
Insurance API endpoints for FinLife SaaS.

All endpoints are authenticated via BearerAuth (JWT).
All queries are filtered by request.user (tenant isolation).
List endpoints use paginate_queryset from common.pagination.

Endpoints:
  /                  — CRUD for Insurance policies
  /{id}/premium-payments/  — Premium payment CRUD
  /{id}/claims/            — Claim CRUD
  /{id}/beneficiaries/     — Beneficiary CRUD
"""

import uuid
from datetime import date as date_type

from django.shortcuts import get_object_or_404
from ninja import Router

from common.permissions import BearerAuth
from common.pagination import (
    PaginationSchema,
    PaginatedResponse,
    paginate_queryset,
)

from .models import (
    Insurance,
    InsuranceBeneficiary,
    InsurancePremiumPayment,
    InsuranceClaim,
)
from .schemas import (
    InsuranceOut,
    InsuranceCreate,
    InsuranceUpdate,
    InsuranceBeneficiaryOut,
    InsuranceBeneficiaryCreate,
    InsuranceBeneficiaryUpdate,
    InsurancePremiumPaymentOut,
    InsurancePremiumPaymentCreate,
    InsuranceClaimOut,
    InsuranceClaimCreate,
    InsuranceClaimUpdate,
    MessageOut,
)

router = Router(tags=["Insurance"], auth=BearerAuth())


# ==================== Field mapping helper ====================

INSURANCE_FIELD_MAP = {
    "policyNumber": "policy_number",
    "groupPolicyNumber": "group_policy_number",
    "coverageAmount": "coverage_amount",
    "premiumAmount": "premium_amount",
    "premiumFrequency": "premium_frequency",
    "issueDate": "issue_date",
    "startDate": "start_date",
    "expiryDate": "expiry_date",
    "maturityDate": "maturity_date",
    "nextPremiumDueDate": "next_premium_due_date",
    "totalPremiumPaid": "total_premium_paid",
    "paidPremiumsCount": "paid_premiums_count",
    "totalClaimedAmount": "total_claimed_amount",
    "autoRenew": "auto_renew",
    "policyTerm": "policy_term",
    "maturityBenefit": "maturity_benefit",
    "riderNames": "rider_names",
    "deductibleAmount": "deductible_amount",
    "copayPercent": "copay_percent",
    "networkHospitals": "network_hospitals",
    "vehicleType": "vehicle_type",
    "vehicleRegistration": "vehicle_registration",
    "vehicleModel": "vehicle_model",
    "propertyType": "property_type",
    "propertyAddress": "property_address",
    "propertyValue": "property_value",
    "bankAccountId": "bank_account_id",
}

PREMIUM_PAYMENT_FIELD_MAP = {
    "paymentDate": "payment_date",
    "paymentNumber": "payment_number",
    "bankAccountId": "bank_account_id",
}

CLAIM_FIELD_MAP = {
    "claimNumber": "claim_number",
    "claimDate": "claim_date",
    "claimAmount": "claim_amount",
    "approvedAmount": "approved_amount",
    "resolutionDate": "resolution_date",
    "resolutionNote": "resolution_note",
}


def _apply_field_map(payload: dict, field_map: dict) -> dict:
    """Convert camelCase payload keys to snake_case model field names."""
    result = {}
    for key, value in payload.items():
        model_field = field_map.get(key, key)
        result[model_field] = value
    return result


# ==================== Insurance CRUD ====================


@router.get("/", response=PaginatedResponse[InsuranceOut])
async def list_insurances(
    request,
    pagination: PaginationSchema,
    category: str = None,
    status: str = None,
):
    """List all insurance policies for the authenticated user, with optional filters."""
    qs = Insurance.objects.filter(owner=request.user).order_by("-created_at")

    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)

    items, total, total_pages = paginate_queryset(
        qs, pagination.page, pagination.per_page
    )
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": total_pages,
    }


@router.post("/", response={201: InsuranceOut})
async def create_insurance(request, data: InsuranceCreate):
    """Create a new insurance policy."""
    payload = data.model_dump(exclude_unset=True)
    db_fields = _apply_field_map(payload, INSURANCE_FIELD_MAP)

    insurance = Insurance.objects.create(owner=request.user, **db_fields)
    return 201, insurance


@router.get("/{insurance_id}", response=InsuranceOut)
async def get_insurance(request, insurance_id: uuid.UUID):
    """Get a single insurance policy by ID."""
    insurance = get_object_or_404(Insurance, id=insurance_id, owner=request.user)
    return insurance


@router.put("/{insurance_id}", response=InsuranceOut)
async def update_insurance(request, insurance_id: uuid.UUID, data: InsuranceUpdate):
    """Update an insurance policy (partial)."""
    insurance = get_object_or_404(Insurance, id=insurance_id, owner=request.user)

    payload = data.model_dump(exclude_unset=True)
    db_fields = _apply_field_map(payload, INSURANCE_FIELD_MAP)

    for field, value in db_fields.items():
        setattr(insurance, field, value)

    insurance.save()
    return insurance


@router.delete("/{insurance_id}", response=MessageOut)
async def delete_insurance(request, insurance_id: uuid.UUID):
    """Delete an insurance policy and all related records."""
    insurance = get_object_or_404(Insurance, id=insurance_id, owner=request.user)
    insurance.delete()
    return MessageOut(message="Insurance deleted successfully")


# ==================== Premium Payments ====================


@router.get(
    "/{insurance_id}/premium-payments/",
    response=PaginatedResponse[InsurancePremiumPaymentOut],
)
async def list_premium_payments(
    request, insurance_id: uuid.UUID, pagination: PaginationSchema
):
    """List all premium payments for an insurance policy."""
    insurance = get_object_or_404(Insurance, id=insurance_id, owner=request.user)
    qs = insurance.premium_payments.all().order_by("-payment_date", "-created_at")
    items, total, total_pages = paginate_queryset(
        qs, pagination.page, pagination.per_page
    )
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": total_pages,
    }


@router.post(
    "/{insurance_id}/premium-payments/", response={201: InsurancePremiumPaymentOut}
)
async def create_premium_payment(
    request, insurance_id: uuid.UUID, data: InsurancePremiumPaymentCreate
):
    """Record a premium payment for an insurance policy."""
    insurance = get_object_or_404(Insurance, id=insurance_id, owner=request.user)

    payload = data.model_dump(exclude_unset=True)
    db_fields = _apply_field_map(payload, PREMIUM_PAYMENT_FIELD_MAP)

    payment = InsurancePremiumPayment.objects.create(
        owner=request.user,
        insurance=insurance,
        **db_fields,
    )

    # Update insurance totals
    insurance.total_premium_paid = (insurance.total_premium_paid or 0) + payment.amount
    insurance.paid_premiums_count = (insurance.paid_premiums_count or 0) + 1
    insurance.save()

    return 201, payment


@router.delete("/{insurance_id}/premium-payments/{payment_id}", response=MessageOut)
async def delete_premium_payment(
    request, insurance_id: uuid.UUID, payment_id: uuid.UUID
):
    """Delete a premium payment and update totals."""
    insurance = get_object_or_404(Insurance, id=insurance_id, owner=request.user)
    payment = get_object_or_404(
        InsurancePremiumPayment, id=payment_id, insurance=insurance, owner=request.user
    )

    # Reverse the aggregates
    insurance.total_premium_paid = max(
        0, (insurance.total_premium_paid or 0) - payment.amount
    )
    insurance.paid_premiums_count = max(0, (insurance.paid_premiums_count or 0) - 1)
    insurance.save()

    payment.delete()
    return MessageOut(message="Premium payment deleted successfully")


# ==================== Claims ====================


@router.get("/{insurance_id}/claims/", response=PaginatedResponse[InsuranceClaimOut])
async def list_claims(request, insurance_id: uuid.UUID, pagination: PaginationSchema):
    """List all claims for an insurance policy."""
    insurance = get_object_or_404(Insurance, id=insurance_id, owner=request.user)
    qs = insurance.claims.all().order_by("-claim_date", "-created_at")
    items, total, total_pages = paginate_queryset(
        qs, pagination.page, pagination.per_page
    )
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": total_pages,
    }


@router.post("/{insurance_id}/claims/", response={201: InsuranceClaimOut})
async def create_claim(request, insurance_id: uuid.UUID, data: InsuranceClaimCreate):
    """Create a claim for an insurance policy."""
    insurance = get_object_or_404(Insurance, id=insurance_id, owner=request.user)

    payload = data.model_dump(exclude_unset=True)
    db_fields = _apply_field_map(payload, CLAIM_FIELD_MAP)

    claim = InsuranceClaim.objects.create(
        owner=request.user,
        insurance=insurance,
        **db_fields,
    )
    return 201, claim


@router.put("/{insurance_id}/claims/{claim_id}", response=InsuranceClaimOut)
async def update_claim(
    request,
    insurance_id: uuid.UUID,
    claim_id: uuid.UUID,
    data: InsuranceClaimUpdate,
):
    """Update a claim (status, approved amount, resolution)."""
    claim = get_object_or_404(
        InsuranceClaim,
        id=claim_id,
        insurance_id=insurance_id,
        owner=request.user,
    )

    payload = data.model_dump(exclude_unset=True)
    db_fields = _apply_field_map(payload, CLAIM_FIELD_MAP)

    for field, value in db_fields.items():
        setattr(claim, field, value)

    # Auto-set resolution date on terminal statuses
    new_status = payload.get("status")
    if new_status in ("approved", "rejected", "paid"):
        if not claim.resolution_date:
            claim.resolution_date = date_type.today()

        # Update total claimed amount when paid
        if new_status == "paid" and claim.approved_amount:
            claim.insurance.total_claimed_amount = (
                claim.insurance.total_claimed_amount or 0
            ) + claim.approved_amount
            claim.insurance.save()

    claim.save()
    return claim


@router.delete("/{insurance_id}/claims/{claim_id}", response=MessageOut)
async def delete_claim(request, insurance_id: uuid.UUID, claim_id: uuid.UUID):
    """Delete a claim."""
    claim = get_object_or_404(
        InsuranceClaim,
        id=claim_id,
        insurance_id=insurance_id,
        owner=request.user,
    )
    claim.delete()
    return MessageOut(message="Claim deleted successfully")


# ==================== Beneficiaries ====================


@router.get(
    "/{insurance_id}/beneficiaries/",
    response=PaginatedResponse[InsuranceBeneficiaryOut],
)
async def list_beneficiaries(
    request, insurance_id: uuid.UUID, pagination: PaginationSchema
):
    """List all beneficiaries for an insurance policy."""
    insurance = get_object_or_404(Insurance, id=insurance_id, owner=request.user)
    qs = insurance.beneficiaries.all().order_by("-created_at")
    items, total, total_pages = paginate_queryset(
        qs, pagination.page, pagination.per_page
    )
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": total_pages,
    }


@router.post("/{insurance_id}/beneficiaries/", response={201: InsuranceBeneficiaryOut})
async def create_beneficiary(
    request,
    insurance_id: uuid.UUID,
    data: InsuranceBeneficiaryCreate,
):
    """Add a beneficiary to an insurance policy."""
    insurance = get_object_or_404(Insurance, id=insurance_id, owner=request.user)

    payload = data.model_dump(exclude_unset=True)

    beneficiary = InsuranceBeneficiary.objects.create(
        owner=request.user,
        insurance=insurance,
        **payload,
    )
    return 201, beneficiary


@router.put(
    "/{insurance_id}/beneficiaries/{beneficiary_id}", response=InsuranceBeneficiaryOut
)
async def update_beneficiary(
    request,
    insurance_id: uuid.UUID,
    beneficiary_id: uuid.UUID,
    data: InsuranceBeneficiaryUpdate,
):
    """Update a beneficiary."""
    beneficiary = get_object_or_404(
        InsuranceBeneficiary,
        id=beneficiary_id,
        insurance_id=insurance_id,
        owner=request.user,
    )

    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(beneficiary, field, value)

    beneficiary.save()
    return beneficiary


@router.delete("/{insurance_id}/beneficiaries/{beneficiary_id}", response=MessageOut)
async def delete_beneficiary(
    request,
    insurance_id: uuid.UUID,
    beneficiary_id: uuid.UUID,
):
    """Delete a beneficiary."""
    beneficiary = get_object_or_404(
        InsuranceBeneficiary,
        id=beneficiary_id,
        insurance_id=insurance_id,
        owner=request.user,
    )
    beneficiary.delete()
    return MessageOut(message="Beneficiary deleted successfully")
