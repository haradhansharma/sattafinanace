"""
Asset schemas — camelCase fields matching the frontend Asset interface exactly.

Conversion helpers:
  • to_snake_case  – camelCase dict → snake_case dict (for Django model kwargs)
"""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from ninja import Schema

# ---------------------------------------------------------------------------
# Camel ↔ Snake helpers
# ---------------------------------------------------------------------------

_first_cap_re = re.compile(r"(.)([A-Z][a-z]+)")
_all_cap_re = re.compile(r"([a-z0-9])([A-Z])")


def _to_snake(name: str) -> str:
    s1 = _first_cap_re.sub(r"\1_\2", name)
    return _all_cap_re.sub(r"\1_\2", s1).lower()


def to_snake_case(data: dict) -> dict:
    return {_to_snake(k): v for k, v in data.items()}


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------


def _fmt_date(d: Optional[date]) -> Optional[str]:
    if d is None:
        return None
    return d.isoformat() if isinstance(d, (date, datetime)) else str(d)


def _parse_date(d):
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return date.fromisoformat(d)


# ---------------------------------------------------------------------------
# AssetValuation
# ---------------------------------------------------------------------------


class AssetValuationOut(Schema):
    id: str
    date: str
    value: int
    note: Optional[str] = None


class AssetValuationIn(Schema):
    date: str
    value: int
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------------


class AssetOut(Schema):
    id: str
    createdAt: str
    updatedAt: str

    name: str
    category: str
    description: Optional[str] = None

    purchaseDate: str
    purchasePrice: int
    purchaseFrom: Optional[str] = None
    invoiceNumber: Optional[str] = None

    currentValue: int
    currentCondition: str

    # Embedded valuations
    valuations: List[AssetValuationOut]

    location: Optional[str] = None

    depreciationMethod: str
    usefulLifeYears: Optional[int] = None
    salvageValue: Optional[int] = None
    currentBookValue: Optional[int] = None

    # Real estate
    propertyType: Optional[str] = None
    propertyAddress: Optional[str] = None
    sizeSqft: Optional[float] = None
    floorNumber: Optional[str] = None
    registrationDate: Optional[str] = None
    registrationNumber: Optional[str] = None
    khatianNumber: Optional[str] = None

    # Vehicle
    vehicleType: Optional[str] = None
    vehicleBrand: Optional[str] = None
    vehicleModel: Optional[str] = None
    vehicleYear: Optional[int] = None
    vehicleRegistrationNo: Optional[str] = None
    engineNo: Optional[str] = None
    chassisNo: Optional[str] = None
    mileageKm: Optional[int] = None

    # Electronics
    brand: Optional[str] = None
    model: Optional[str] = None
    serialNumber: Optional[str] = None
    warrantyExpiryDate: Optional[str] = None

    # Jewelry
    itemType: Optional[str] = None
    material: Optional[str] = None
    weightGrams: Optional[float] = None
    purity: Optional[str] = None

    # Ownership
    status: str
    ownershipPercentage: int
    loanAgainstAsset: bool
    insurancePolicyId: Optional[str] = None
    coOwners: Optional[str] = None
    bankAccountId: Optional[str] = None
    currency: str

    # Metadata
    notes: Optional[str] = None
    tags: list

    @classmethod
    def from_model(cls, obj: "Asset") -> "AssetOut":
        from .models import AssetValuation  # avoid circular at module-level

        valuations = [
            AssetValuationOut(
                id=str(v.id),
                date=_fmt_date(v.date),
                value=v.value,
                note=v.note or None,
            )
            for v in getattr(obj, "_prefetched_valuations", obj.valuation_set.all())
        ]
        return cls(
            id=str(obj.id),
            createdAt=obj.created_at.isoformat(),
            updatedAt=obj.updated_at.isoformat(),
            name=obj.name,
            category=obj.category,
            description=obj.description or None,
            purchaseDate=_fmt_date(obj.purchase_date),
            purchasePrice=obj.purchase_price,
            purchaseFrom=obj.purchase_from or None,
            invoiceNumber=obj.invoice_number or None,
            currentValue=obj.current_value,
            currentCondition=obj.current_condition,
            valuations=valuations,
            location=obj.location or None,
            depreciationMethod=obj.depreciation_method,
            usefulLifeYears=obj.useful_life_years,
            salvageValue=obj.salvage_value,
            currentBookValue=obj.current_book_value,
            propertyType=obj.property_type,
            propertyAddress=obj.property_address or None,
            sizeSqft=float(obj.size_sqft) if obj.size_sqft is not None else None,
            floorNumber=obj.floor_number or None,
            registrationDate=_fmt_date(obj.registration_date),
            registrationNumber=obj.registration_number or None,
            khatianNumber=obj.khatian_number or None,
            vehicleType=obj.vehicle_type,
            vehicleBrand=obj.vehicle_brand or None,
            vehicleModel=obj.vehicle_model or None,
            vehicleYear=obj.vehicle_year,
            vehicleRegistrationNo=obj.vehicle_registration_no or None,
            engineNo=obj.engine_no or None,
            chassisNo=obj.chassis_no or None,
            mileageKm=obj.mileage_km,
            brand=obj.brand or None,
            model=obj.model or None,
            serialNumber=obj.serial_number or None,
            warrantyExpiryDate=_fmt_date(obj.warranty_expiry_date),
            itemType=obj.item_type,
            material=obj.material or None,
            weightGrams=(
                float(obj.weight_grams) if obj.weight_grams is not None else None
            ),
            purity=obj.purity or None,
            status=obj.status,
            ownershipPercentage=obj.ownership_percentage,
            loanAgainstAsset=obj.loan_against_asset,
            insurancePolicyId=(
                str(obj.insurance_policy_id) if obj.insurance_policy_id else None
            ),
            coOwners=obj.co_owners or None,
            bankAccountId=str(obj.bank_account_id) if obj.bank_account_id else None,
            currency=obj.currency,
            notes=obj.notes or None,
            tags=obj.tags or [],
        )


class AssetCreate(Schema):
    name: str
    category: str
    description: Optional[str] = None
    purchaseDate: str
    purchasePrice: int
    purchaseFrom: Optional[str] = None
    invoiceNumber: Optional[str] = None
    currentValue: Optional[int] = None
    currentCondition: str = "good"
    location: Optional[str] = None
    depreciationMethod: str = "none"
    usefulLifeYears: Optional[int] = None
    salvageValue: Optional[int] = None
    propertyType: Optional[str] = None
    propertyAddress: Optional[str] = None
    sizeSqft: Optional[float] = None
    floorNumber: Optional[str] = None
    registrationDate: Optional[str] = None
    registrationNumber: Optional[str] = None
    khatianNumber: Optional[str] = None
    vehicleType: Optional[str] = None
    vehicleBrand: Optional[str] = None
    vehicleModel: Optional[str] = None
    vehicleYear: Optional[int] = None
    vehicleRegistrationNo: Optional[str] = None
    engineNo: Optional[str] = None
    chassisNo: Optional[str] = None
    mileageKm: Optional[int] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serialNumber: Optional[str] = None
    warrantyExpiryDate: Optional[str] = None
    itemType: Optional[str] = None
    material: Optional[str] = None
    weightGrams: Optional[float] = None
    purity: Optional[str] = None
    status: str = "owned"
    ownershipPercentage: int = 100
    loanAgainstAsset: bool = False
    insurancePolicyId: Optional[str] = None
    coOwners: Optional[str] = None
    bankAccountId: Optional[str] = None
    currency: str = "BDT"
    notes: Optional[str] = None
    tags: Optional[list] = None


class AssetUpdate(Schema):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    purchaseDate: Optional[str] = None
    purchasePrice: Optional[int] = None
    purchaseFrom: Optional[str] = None
    invoiceNumber: Optional[str] = None
    currentValue: Optional[int] = None
    currentCondition: Optional[str] = None
    location: Optional[str] = None
    depreciationMethod: Optional[str] = None
    usefulLifeYears: Optional[int] = None
    salvageValue: Optional[int] = None
    currentBookValue: Optional[int] = None
    propertyType: Optional[str] = None
    propertyAddress: Optional[str] = None
    sizeSqft: Optional[float] = None
    floorNumber: Optional[str] = None
    registrationDate: Optional[str] = None
    registrationNumber: Optional[str] = None
    khatianNumber: Optional[str] = None
    vehicleType: Optional[str] = None
    vehicleBrand: Optional[str] = None
    vehicleModel: Optional[str] = None
    vehicleYear: Optional[int] = None
    vehicleRegistrationNo: Optional[str] = None
    engineNo: Optional[str] = None
    chassisNo: Optional[str] = None
    mileageKm: Optional[int] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serialNumber: Optional[str] = None
    warrantyExpiryDate: Optional[str] = None
    itemType: Optional[str] = None
    material: Optional[str] = None
    weightGrams: Optional[float] = None
    purity: Optional[str] = None
    status: Optional[str] = None
    ownershipPercentage: Optional[int] = None
    loanAgainstAsset: Optional[bool] = None
    insurancePolicyId: Optional[str] = None
    coOwners: Optional[str] = None
    bankAccountId: Optional[str] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list] = None


class AddValuationIn(Schema):
    date: str
    value: int
    note: Optional[str] = None


class UpdateStatusIn(Schema):
    status: str


class MessageOut(Schema):
    message: str
