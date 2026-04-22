"""
Asset tracking for FinLife Personal Finance SaaS.

Asset — full asset lifecycle with category-specific fields
        (real estate, vehicle, electronics, jewelry, etc.).
AssetValuation — lightweight FK child of Asset (no TenantMixin, no timestamps).
"""

import uuid

from django.db import models

from common.models import TenantMixin


class Asset(TenantMixin):
    """Track owned assets with depreciation, category-specific metadata, and valuations."""

    # --- Choices ---
    CATEGORY_CHOICES = [
        ("real_estate", "Real Estate"),
        ("vehicle", "Vehicle"),
        ("electronics", "Electronics"),
        ("furniture", "Furniture"),
        ("jewelry", "Jewelry"),
        ("art", "Art"),
        ("equipment", "Equipment"),
        ("other", "Other"),
    ]
    CONDITION_CHOICES = [
        ("excellent", "Excellent"),
        ("good", "Good"),
        ("fair", "Fair"),
        ("poor", "Poor"),
        ("damaged", "Damaged"),
    ]
    DEPRECIATION_CHOICES = [
        ("none", "None"),
        ("straight_line", "Straight Line"),
        ("declining_balance", "Declining Balance"),
    ]
    PROPERTY_TYPE_CHOICES = [
        ("apartment", "Apartment"),
        ("house", "House"),
        ("land", "Land"),
        ("commercial", "Commercial"),
        ("condo", "Condo"),
        ("plot", "Plot"),
    ]
    VEHICLE_TYPE_CHOICES = [
        ("car", "Car"),
        ("motorcycle", "Motorcycle"),
        ("bus", "Bus"),
        ("truck", "Truck"),
        ("bicycle", "Bicycle"),
        ("rickshaw_van", "Rickshaw Van"),
        ("other", "Other"),
    ]
    JEWELRY_ITEM_TYPE_CHOICES = [
        ("necklace", "Necklace"),
        ("ring", "Ring"),
        ("earring", "Earring"),
        ("bangle", "Bangle"),
        ("bracelet", "Bracelet"),
        ("chain", "Chain"),
        ("pendant", "Pendant"),
        ("watch", "Watch"),
        ("set", "Set"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("owned", "Owned"),
        ("rented", "Rented"),
        ("leased", "Leased"),
        ("sold", "Sold"),
        ("gifted", "Gifted"),
        ("damaged", "Damaged"),
        ("disposed", "Disposed"),
    ]

    # --- Core ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, default="")

    # --- Purchase ---
    purchase_date = models.DateField()
    purchase_price = models.BigIntegerField()
    purchase_from = models.CharField(max_length=255, blank=True, default="")
    invoice_number = models.CharField(max_length=255, blank=True, default="")

    # --- Current state ---
    current_value = models.BigIntegerField()
    current_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    location = models.TextField(blank=True, default="")

    # --- Depreciation ---
    depreciation_method = models.CharField(
        max_length=20, choices=DEPRECIATION_CHOICES, default="none"
    )
    useful_life_years = models.IntegerField(null=True, blank=True)
    salvage_value = models.BigIntegerField(null=True, blank=True)
    current_book_value = models.BigIntegerField(null=True, blank=True)

    # --- Real estate ---
    property_type = models.CharField(
        max_length=30, choices=PROPERTY_TYPE_CHOICES, null=True, blank=True
    )
    property_address = models.TextField(blank=True, default="")
    size_sqft = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    floor_number = models.CharField(max_length=50, blank=True, default="")
    registration_date = models.DateField(null=True, blank=True)
    registration_number = models.CharField(max_length=255, blank=True, default="")
    khatian_number = models.CharField(max_length=255, blank=True, default="")

    # --- Vehicle ---
    vehicle_type = models.CharField(
        max_length=30, choices=VEHICLE_TYPE_CHOICES, null=True, blank=True
    )
    vehicle_brand = models.CharField(max_length=100, blank=True, default="")
    vehicle_model = models.CharField(max_length=100, blank=True, default="")
    vehicle_year = models.IntegerField(null=True, blank=True)
    vehicle_registration_no = models.CharField(max_length=255, blank=True, default="")
    engine_no = models.CharField(max_length=255, blank=True, default="")
    chassis_no = models.CharField(max_length=255, blank=True, default="")
    mileage_km = models.IntegerField(null=True, blank=True)

    # --- Electronics ---
    brand = models.CharField(max_length=100, blank=True, default="")
    model = models.CharField(max_length=100, blank=True, default="")
    serial_number = models.CharField(max_length=255, blank=True, default="")
    warranty_expiry_date = models.DateField(null=True, blank=True)

    # --- Jewelry ---
    item_type = models.CharField(
        max_length=30, choices=JEWELRY_ITEM_TYPE_CHOICES, null=True, blank=True
    )
    material = models.CharField(max_length=100, blank=True, default="")
    weight_grams = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    purity = models.CharField(max_length=50, blank=True, default="")

    # --- Ownership ---
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="owned")
    ownership_percentage = models.IntegerField(default=100)
    loan_against_asset = models.BooleanField(default=False)
    insurance_policy_id = models.UUIDField(null=True, blank=True)
    co_owners = models.CharField(max_length=255, blank=True, default="")
    bank_account_id = models.UUIDField(null=True, blank=True)
    currency = models.CharField(max_length=10, default="BDT")

    # --- Metadata ---
    notes = models.TextField(blank=True, default="")
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} — {self.category}"


class AssetValuation(models.Model):
    """
    Periodic valuation record for an Asset.
    No TenantMixin, no created_at / updated_at — lives and dies with its Asset.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="valuation_set"
    )

    date = models.DateField()
    value = models.BigIntegerField()
    note = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"Valuation {self.value} on {self.date} for {self.asset.name}"
