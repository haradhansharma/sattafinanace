"""
Mortgage models for FinLife SaaS.

All models inherit from TenantMixin (common.models) which provides:
  - owner: FK → settings.AUTH_USER_MODEL (auto-added)
  - Tenant isolation: every query MUST filter by owner

Embedded sub-objects (MortgageProperty, MortgageEscrow, HeldMortgageCollateral)
are stored as JSONField to match the frontend embedded-object pattern exactly.
"""

import uuid

from django.db import models

from common.models import TenantMixin


# ==================== Property type choices (shared) ====================


class PropertyType(models.TextChoices):
    APARTMENT = "apartment", "Apartment"
    HOUSE = "house", "House"
    LAND = "land", "Land"
    COMMERCIAL = "commercial", "Commercial"
    CONDO = "condo", "Condo"


class InterestType(models.TextChoices):
    FIXED = "fixed", "Fixed"
    VARIABLE = "variable", "Variable"


# ==================== Mortgage ====================


class MortgageStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"
    DEFAULTED = "defaulted", "Defaulted"
    IN_REVIEW = "in_review", "In Review"


class Mortgage(TenantMixin):
    """
    A mortgage taken by the user (borrower perspective).
    Property and Escrow are stored as JSONField (embedded objects).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # --- Embedded: MortgageProperty (JSONField) ---
    # Stores: { name, propertyType, address, sizeSqft?, purchasePrice, currentMarketValue?, purchaseDate }
    property = models.JSONField(default=dict, blank=True)

    lender_name = models.CharField(max_length=255)
    loan_amount = models.BigIntegerField(default=0)
    down_payment = models.BigIntegerField(default=0)
    down_payment_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    current_balance = models.BigIntegerField(default=0)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    interest_type = models.CharField(
        max_length=20, choices=InterestType.choices, default=InterestType.FIXED
    )
    term_months = models.IntegerField(default=0)
    emi_amount = models.BigIntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    next_payment_date = models.DateField(null=True, blank=True)
    paid_amount = models.BigIntegerField(default=0)
    paid_installments = models.IntegerField(default=0)
    total_installments = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20, choices=MortgageStatus.choices, default=MortgageStatus.ACTIVE
    )

    # --- Embedded: MortgageEscrow (JSONField) ---
    # Stores: { propertyTaxAnnual, insuranceAnnual, monthlyEscrow }
    escrow = models.JSONField(default=dict, blank=True)

    bank_account_id = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=10, default="BDT")
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Mortgage"
        verbose_name_plural = "Mortgages"

    def __str__(self):
        return f"Mortgage — {self.lender_name}"


# ==================== Held Mortgage (lender perspective) ====================


class Relationship(models.TextChoices):
    FAMILY = "family", "Family"
    FRIEND = "friend", "Friend"
    BUSINESS = "business", "Business"
    COLLEAGUE = "colleague", "Colleague"
    OTHER = "other", "Other"


class HeldMortgageStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"
    DEFAULTED = "defaulted", "Defaulted"
    FORECLOSED = "foreclosed", "Foreclosed"
    IN_REVIEW = "in_review", "In Review"


class HeldMortgage(TenantMixin):
    """
    A mortgage held by the user (lender perspective).
    Collateral is stored as JSONField (embedded object).
    Payments are a separate FK-related model.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    borrower_name = models.CharField(max_length=255)
    borrower_phone = models.CharField(max_length=50, blank=True, default="")
    borrower_email = models.EmailField(blank=True, default="")
    borrower_address = models.TextField(blank=True, default="")
    relationship = models.CharField(
        max_length=20, choices=Relationship.choices, default=Relationship.OTHER
    )

    # --- Embedded: HeldMortgageCollateral (JSONField) ---
    # Stores: { name, propertyType, address, sizeSqft?, appraisedValue, currentValue, documents? }
    collateral = models.JSONField(default=dict, blank=True)

    loan_amount = models.BigIntegerField(default=0)
    current_balance = models.BigIntegerField(default=0)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    interest_type = models.CharField(
        max_length=20, choices=InterestType.choices, default=InterestType.FIXED
    )
    term_months = models.IntegerField(default=0)
    expected_monthly_payment = models.BigIntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    next_payment_due_date = models.DateField(null=True, blank=True)
    total_received_amount = models.BigIntegerField(default=0)
    total_interest_earned = models.BigIntegerField(default=0)
    received_installments = models.IntegerField(default=0)
    total_installments = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=HeldMortgageStatus.choices,
        default=HeldMortgageStatus.ACTIVE,
    )

    late_payment_penalty_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    grace_period_days = models.IntegerField(default=0)

    bank_account_id = models.CharField(max_length=255, null=True, blank=True)
    currency = models.CharField(max_length=10, default="BDT")
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Held Mortgage"
        verbose_name_plural = "Held Mortgages"

    def __str__(self):
        return f"Held Mortgage — {self.borrower_name}"


# ==================== Held Mortgage Payment ====================


class HeldMortgagePayment(TenantMixin):
    """
    An individual payment received against a held mortgage.
    FK to HeldMortgage via held_mortgage field.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    held_mortgage = models.ForeignKey(
        HeldMortgage,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    amount = models.BigIntegerField(default=0)
    principal_component = models.BigIntegerField(default=0)
    interest_component = models.BigIntegerField(default=0)
    payment_date = models.DateField(null=True, blank=True)
    payment_number = models.IntegerField(default=0)
    note = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["payment_number"]
        verbose_name = "Held Mortgage Payment"
        verbose_name_plural = "Held Mortgage Payments"

    def __str__(self):
        return f"Payment #{self.payment_number} from {self.held_mortgage.borrower_name}"
