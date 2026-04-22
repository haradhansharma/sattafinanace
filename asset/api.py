"""
Asset API — Django Ninja endpoints.

All endpoints are authenticated via BearerAuth and scoped to request.user.
List endpoints use paginate_queryset for standard pagination.
"""

import uuid

from django.http import HttpRequest
from ninja import Router

from common.permissions import BearerAuth
from common.pagination import paginate_queryset, PaginatedResponse

from .models import Asset, AssetValuation
from .schemas import (
    AssetOut,
    AssetCreate,
    AssetUpdate,
    AddValuationIn,
    UpdateStatusIn,
    MessageOut,
    AssetValuationOut,
    AssetValuationIn,
    to_snake_case,
    _parse_date,
)

router = Router(auth=BearerAuth())

_DATE_FIELDS = ("purchase_date", "registration_date", "warranty_expiry_date")


def _apply_asset_attrs(asset: Asset, data: dict) -> None:
    """Apply a snake_case data dict to an Asset instance, parsing dates."""
    for field in _DATE_FIELDS:
        val = data.get(field)
        if val is not None:
            data[field] = _parse_date(val)
    for key, value in data.items():
        setattr(asset, key, value)


def _hydrate_valuations(obj: Asset, valuations) -> AssetOut:
    """Attach prefetched valuations to the Asset instance before serialising."""
    obj._prefetched_valuations = valuations
    return AssetOut.from_model(obj)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("/", response=PaginatedResponse[AssetOut], summary="List assets")
async def list_assets(
    request: HttpRequest,
    page: int = 1,
    per_page: int = 20,
    category: str = None,
    status: str = None,
    current_condition: str = None,
):
    qs = Asset.objects.filter(owner=request.user)
    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)
    if current_condition:
        qs = qs.filter(current_condition=current_condition)

    items, total, total_pages = paginate_queryset(qs, page, per_page)

    # Batch-prefetch valuations for the page
    asset_ids = [a.id for a in items]
    valuations_map: dict = {}
    if asset_ids:
        for v in AssetValuation.objects.filter(asset_id__in=asset_ids):
            valuations_map.setdefault(v.asset_id, []).append(v)

    results = [_hydrate_valuations(a, valuations_map.get(a.id, [])) for a in items]
    return {
        "items": results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.post("/", response={201: AssetOut}, summary="Create an asset")
async def create_asset(request: HttpRequest, payload: AssetCreate):
    data = to_snake_case(payload.model_dump())
    for field in _DATE_FIELDS:
        if data.get(field):
            data[field] = _parse_date(data[field])
    if data.get("current_value") is None:
        data["current_value"] = data.get("purchase_price", 0)
    if data.get("tags") is None:
        data["tags"] = []
    if data.get("description") is None:
        data["description"] = ""
    asset = Asset(owner=request.user, **data)
    asset.full_clean()
    asset.save()
    asset.refresh_from_db()
    return AssetOut.from_model(asset)


@router.get("/{asset_id}", response=AssetOut, summary="Get asset by ID")
async def get_asset(request: HttpRequest, asset_id: uuid.UUID):
    asset = Asset.objects.get(id=asset_id, owner=request.user)
    return AssetOut.from_model(asset)


@router.put("/{asset_id}", response=AssetOut, summary="Update an asset")
async def update_asset(request: HttpRequest, asset_id: uuid.UUID, payload: AssetUpdate):
    asset = Asset.objects.get(id=asset_id, owner=request.user)
    data = to_snake_case(payload.model_dump(exclude_unset=True))
    _apply_asset_attrs(asset, data)
    asset.full_clean()
    asset.save()
    asset.refresh_from_db()
    return AssetOut.from_model(asset)


@router.delete("/{asset_id}", response=MessageOut, summary="Delete an asset")
async def delete_asset(request: HttpRequest, asset_id: uuid.UUID):
    asset = Asset.objects.get(id=asset_id, owner=request.user)
    asset_id_str = str(asset.id)
    asset.delete()
    return MessageOut(message=f"Asset {asset_id_str} deleted successfully")


# ---------------------------------------------------------------------------
# Valuations (embedded sub-resource)
# ---------------------------------------------------------------------------


@router.get(
    "/{asset_id}/valuations",
    response=list[AssetValuationOut],
    summary="List asset valuations",
)
async def list_valuations(request: HttpRequest, asset_id: uuid.UUID):
    Asset.objects.get(id=asset_id, owner=request.user)  # ownership check
    valuations = AssetValuation.objects.filter(asset_id=asset_id)
    return [
        AssetValuationOut(
            id=str(v.id),
            date=v.date.isoformat(),
            value=v.value,
            note=v.note or None,
        )
        for v in valuations
    ]


@router.post(
    "/{asset_id}/valuations",
    response=AssetOut,
    summary="Add a valuation (updates current value)",
)
async def add_valuation(
    request: HttpRequest, asset_id: uuid.UUID, payload: AddValuationIn
):
    asset = Asset.objects.get(id=asset_id, owner=request.user)
    data = to_snake_case(payload.model_dump())
    valuation = AssetValuation(
        asset=asset,
        date=_parse_date(data["date"]),
        value=data["value"],
        note=data.get("note", "") or "",
    )
    valuation.full_clean()
    valuation.save()

    # Update denormalised current value
    asset.current_value = valuation.value
    asset.save()
    asset.refresh_from_db()
    return AssetOut.from_model(asset)


@router.delete(
    "/{asset_id}/valuations/{valuation_id}",
    response=MessageOut,
    summary="Delete a valuation record",
)
async def delete_valuation(
    request: HttpRequest, asset_id: uuid.UUID, valuation_id: uuid.UUID
):
    asset = Asset.objects.get(id=asset_id, owner=request.user)
    valuation = AssetValuation.objects.get(id=valuation_id, asset=asset)
    valuation.delete()
    return MessageOut(message=f"Valuation {valuation_id} deleted successfully")


# ---------------------------------------------------------------------------
# Status transition
# ---------------------------------------------------------------------------


@router.put("/{asset_id}/status", response=AssetOut, summary="Update asset status")
async def update_status(
    request: HttpRequest, asset_id: uuid.UUID, payload: UpdateStatusIn
):
    asset = Asset.objects.get(id=asset_id, owner=request.user)
    asset.status = payload.status
    asset.save()
    asset.refresh_from_db()
    return AssetOut.from_model(asset)
