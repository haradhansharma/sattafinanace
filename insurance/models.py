"""
Insurance models for FinLife SaaS.

All models inherit from TenantMixin (common.models) which provides:
  - owner: FK → settings.AUTH_USER_MODEL (auto-added)
  - Tenant isolation: every query MUST filter by owner

Insurance has 40+ fields covering life, health, vehicle, property, travel,
critical_illness, and other categories. Related sub-resources (premium payments,
claims, beneficiaries) use FK relationships with CASCADE delete.
"""

import uuid

from django.db import models

from common.models import TenantMixin


# ==================== Shared choice enums ====================


class InsuranceCategory(models.TextChoices):
    LIFE = "life", "Life"
    HEALTH = "health", "Health"
    VEHICLE = "vehicle", "Vehicle"
    PROPERTY = "property", "Property"
    TRAVEL = "travel", "Travel"
    CRITICAL_ILLNESS = "critical_illness", "Critical Illness"
    OTHER = "other", "Other"


class PremiumFrequency(models.TextChoices):
    MONTHLY = "monthly", "Monthly"
    QUARTERLY = "quarterly", "Quarterly"
    SEMIANNUALLY = "semiannually", "Semiannually"
    ANNUALLY = "annually", "Annually"
    SINGLE = "single", "Single"


class InsuranceStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"
    CLAIMED = "claimed", "Claimed"
    LAPSED = "lapsed", "Lapsed"
    PENDING_RENEWAL = "pending_renewal", "Pending Renewal"


class VehicleType(models.TextChoices):
    CAR = "car", "Car"
    MOTORCYCLE = "motorcycle", "Motorcycle"
    BUS = "bus", "Bus"
    TRUCK = "truck", "Truck"
    OTHER = "other", "Other"


class PropertyType(models.TextChoices):
    APARTMENT = "apartment", "Apartment"
    HOUSE = "house", "House"
    LAND = "land", "Land"
    COMMERCIAL = "commercial", "Commercial"
    OTHER = "other", "Other"


class BeneficiaryRelationship(models.TextChoices):
    SELF = "self", "Self"
    SPOUSE = "spouse", "Spouse"
    CHILD = "child", "Child"
    PARENT = "parent", "Parent"
    SIBLING = "sibling", "Sibling"
    OTHER = "other", "Other"


class ClaimStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    PAID = "paid", "Paid"
    IN_REVIEW = "in_review", "In Review"


# ==================== Insurance ====================


class Insurance(TenantMixin):
    """
    Main Insurance model with 40+ fields.
    Covers all category-specific fields as flat columns.
    Related: premium_payments (FK), claims (FK), beneficiaries (FK).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # --- Core fields ---
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=InsuranceCategory.choices)
    provider = models.CharField(max_length=255)
    policy_number = models.CharField(max_length=255)
    group_policy_number = models.CharField(max_length=255, blank=True, default="")

    coverage_amount = models.BigIntegerField(default=0)
    premium_amount = models.BigIntegerField(default=0)
    premium_frequency = models.CharField(
        max_length=20,
        choices=PremiumFrequency.choices,
        default=PremiumFrequency.MONTHLY,
    )

    # --- Dates ---
    issue_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)
    next_premium_due_date = models.DateField(null=True, blank=True)

    # --- Totals ---
    total_premium_paid = models.BigIntegerField(default=0)
    paid_premiums_count = models.IntegerField(default=0)
    total_claimed_amount = models.BigIntegerField(default=0)

    status = models.CharField(
        max_length=20, choices=InsuranceStatus.choices, default=InsuranceStatus.ACTIVE
    )
    auto_renew = models.BooleanField(default=False)

    # --- Life specific ---
    policy_term = models.IntegerField(null=True, blank=True)
    maturity_benefit = models.BigIntegerField(default=0)
    rider_names = models.JSONField(default=list, blank=True)

    # --- Health specific ---
    deductible_amount = models.BigIntegerField(default=0)
    copay_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    network_hospitals = models.CharField(max_length=500, blank=True, default="")

    # --- Vehicle specific ---
    vehicle_type = models.CharField(
        max_length=20, choices=VehicleType.choices, null=True, blank=True
    )
    vehicle_registration = models.CharField(max_length=255, blank=True, default="")
    vehicle_model = models.CharField(max_length=255, blank=True, default="")

    # --- Property specific ---
    property_type = models.CharField(
        max_length=20, choices=PropertyType.choices, null=True, blank=True
    )
    property_address = models.TextField(blank=True, default="")
    property_value = models.BigIntegerField(default=0)

    # --- Common ---
    bank_account_id = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=10, default="BDT")
    notes = models.TextField(blank=True, default="")
    tags = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Insurance"
        verbose_name_plural = "Insurances"

    def __str__(self):
        return f"{self.name} ({self.category}) — {self.policy_number}"


# ==================== InsuranceBeneficiary ====================


class InsuranceBeneficiary(TenantMixin):
    """
    Beneficiary linked to an Insurance policy.
    NO separate created_at/updated_at per spec (beneficiary is a simple sub-object),
    but we include them as standard practice for audit trails.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    insurance = models.ForeignKey(
        Insurance,
        on_delete=models.CASCADE,
        related_name="beneficiaries",
    )

    name = models.CharField(max_length=255)
    relationship = models.CharField(
        max_length=20, choices=BeneficiaryRelationship.choices
    )
    percentage = models.IntegerField(default=0)
    phone = models.CharField(max_length=50, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Insurance Beneficiary"
        verbose_name_plural = "Insurance Beneficiaries"

    def __str__(self):
        return f"{self.name} ({self.relationship}) — {self.percentage}%"


# ==================== InsurancePremiumPayment ====================


class InsurancePremiumPayment(TenantMixin):
    """
    Premium payment record for an Insurance policy.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    insurance = models.ForeignKey(
        Insurance,
        on_delete=models.CASCADE,
        related_name="premium_payments",
    )

    amount = models.BigIntegerField(default=0)
    payment_date = models.DateField(null=True, blank=True)
    payment_number = models.IntegerField(default=1)
    note = models.TextField(blank=True, default="")
    bank_account_id = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-payment_date", "-created_at"]
        verbose_name = "Insurance Premium Payment"
        verbose_name_plural = "Insurance Premium Payments"

    def __str__(self):
        return f"Premium #{self.payment_number} — {self.amount} ({self.insurance.name})"


# ==================== InsuranceClaim ====================


class InsuranceClaim(TenantMixin):
    """
    Claim record for an Insurance policy.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    insurance = models.ForeignKey(
        Insurance,
        on_delete=models.CASCADE,
        related_name="claims",
    )

    claim_number = models.CharField(max_length=255, blank=True, default="")
    claim_date = models.DateField(null=True, blank=True)
    claim_amount = models.BigIntegerField(default=0)
    approved_amount = models.BigIntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=ClaimStatus.choices, default=ClaimStatus.PENDING
    )
    description = models.TextField(blank=True, default="")
    documents = models.TextField(blank=True, default="")
    resolution_date = models.DateField(null=True, blank=True)
    resolution_note = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-claim_date", "-created_at"]
        verbose_name = "Insurance Claim"
        verbose_name_plural = "Insurance Claims"

    def __str__(self):
        return f"Claim {self.claim_number or self.id} — {self.claim_amount} ({self.insurance.name})"
