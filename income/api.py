# """
# Income API — full CRUD for IncomeSource, IncomeCategory, and Income.

# All endpoints require BearerAuth (JWT).
# All querysets are filtered by `request.user` (tenant isolation).
# List endpoints use `paginate_queryset` from `common.pagination`.

# Routes (prefixed with /api/income):
#   ── Categories ─────────────────────────────────────────────
#   GET    /categories/                     List categories
#   POST   /categories/                     Create category
#   PUT    /categories/{category_id}/       Update category
#   DELETE /categories/{category_id}/       Delete category

#   ── Sources ────────────────────────────────────────────────
#   GET    /sources/                        List sources
#   POST   /sources/                        Create source
#   PUT    /sources/{source_id}/            Update source
#   DELETE /sources/{source_id}/            Delete source

#   ── Incomes ────────────────────────────────────────────────
#   GET    /                                List incomes (paginated, filterable)
#   POST   /                                Create income
#   GET    /{income_id}/                    Retrieve income
#   DELETE /{income_id}/                    Delete income
# """

# from typing import List, Optional

# from django.core.exceptions import ValidationError as DjangoValidationError
# from django.shortcuts import aget_object_or_404
# from ninja import Router

# from common.pagination import (
#     PaginatedResponse,
#     PaginationSchema,
#     apaginate_queryset,
# )
# from common.permissions import BearerAuth

# from .models import Income, IncomeCategory, IncomeSource
# from .schemas import (
#     IncomeCategoryCreate,
#     IncomeCategoryOut,
#     IncomeCategoryUpdate,
#     IncomeCreate,
#     IncomeOut,
#     IncomeSourceCreate,
#     IncomeSourceOut,
#     IncomeSourceUpdate,
#     MessageOut,
# )

# router = Router(tags=["Income"])
# auth = BearerAuth()


# # ══════════════════════════════════════════════════════════════════════════════
# # Income Category Endpoints
# # ══════════════════════════════════════════════════════════════════════════════


# @router.get("/categories/", auth=auth, response=List[IncomeCategoryOut])
# async def list_income_categories(request):
#     """List all income categories for the authenticated user."""
#     # .alist() evaluates the queryset asynchronously and returns a list
#     return [cat async for cat in IncomeCategory.objects.filter(owner=request.user)]


# @router.post("/categories/", auth=auth, response=IncomeCategoryOut)
# async def create_income_category(request, payload: IncomeCategoryCreate):
#     """Create a new income category."""
#     return await IncomeCategory.objects.acreate(
#         name=payload.name,
#         icon=payload.icon,
#         color=payload.color,
#         type=payload.type,
#         owner=request.user,
#     )


# @router.put("/categories/{category_id}/", auth=auth, response=IncomeCategoryOut)
# async def update_income_category(
#     request, category_id: str, payload: IncomeCategoryUpdate
# ):
#     """Update an income category."""
#     cat = await aget_object_or_404(IncomeCategory, id=category_id, owner=request.user)

#     if payload.name is not None:
#         cat.name = payload.name
#     if payload.icon is not None:
#         cat.icon = payload.icon
#     if payload.color is not None:
#         cat.color = payload.color
#     if payload.type is not None:
#         cat.type = payload.type
#     await cat.asave()

#     return cat


# @router.delete("/categories/{category_id}/", auth=auth, response=MessageOut)
# async def delete_income_category(request, category_id: str):
#     """Delete an income category."""
#     cat = await aget_object_or_404(IncomeCategory, id=category_id, owner=request.user)
#     await cat.adelete()
#     return {"message": "Income category deleted successfully"}


# # ══════════════════════════════════════════════════════════════════════════════
# # Income Source Endpoints
# # ══════════════════════════════════════════════════════════════════════════════


# @router.get("/sources/", auth=auth, response=List[IncomeSourceOut])
# async def list_income_sources(request):
#     """List all income sources for the authenticated user."""
#     # return await IncomeSource.objects.filter(owner=request.user)
#     return [source async for source in IncomeSource.objects.filter(owner=request.user)]


# @router.post("/sources/", auth=auth, response=IncomeSourceOut)
# async def create_income_source(request, payload: IncomeSourceCreate):
#     """Create a new income source."""
#     return await IncomeSource.objects.acreate(
#         name=payload.name,
#         type=payload.type,
#         is_active=payload.isActive,
#         monthly_amount=payload.monthlyAmount,
#         currency=payload.currency,
#         owner=request.user,
#     )


# @router.put("/sources/{source_id}/", auth=auth, response=IncomeSourceOut)
# async def update_income_source(request, source_id: str, payload: IncomeSourceUpdate):
#     """Update an income source."""
#     source = await aget_object_or_404(IncomeSource, id=source_id, owner=request.user)

#     if payload.name is not None:
#         source.name = payload.name
#     if payload.type is not None:
#         source.type = payload.type
#     if payload.isActive is not None:
#         source.is_active = payload.isActive
#     if payload.monthlyAmount is not None:
#         source.monthly_amount = payload.monthlyAmount
#     if payload.currency is not None:
#         source.currency = payload.currency
#     await source.asave()

#     return source


# @router.delete("/sources/{source_id}/", auth=auth, response=MessageOut)
# async def delete_income_source(request, source_id: str):
#     """Delete an income source. Protected: cannot delete if linked income records exist."""
#     source = await aget_object_or_404(IncomeSource, id=source_id, owner=request.user)
#     has_incomes = await Income.objects.filter(source=source).aexists()
#     if has_incomes:
#         raise DjangoValidationError(
#             "Cannot delete this income source because it has linked income records. "
#             "Deactivate it instead."
#         )
#     await source.adelete()
#     return {"message": "Income source deleted successfully"}


# # ══════════════════════════════════════════════════════════════════════════════
# # Income Endpoints
# # ══════════════════════════════════════════════════════════════════════════════


# @router.get("/", auth=auth, response=PaginatedResponse[IncomeOut])
# async def list_incomes(
#     request,
#     page: int = PaginationSchema.__fields__["page"].default,
#     per_page: int = PaginationSchema.__fields__["per_page"].default,
#     sourceId: Optional[str] = None,
#     categoryId: Optional[str] = None,
#     dateFrom: Optional[str] = None,
#     dateTo: Optional[str] = None,
# ):
#     """List incomes for the authenticated user, filterable by source, category, and date range."""
#     qs = Income.objects.filter(owner=request.user).select_related("source", "category")

#     if sourceId:
#         qs = qs.filter(source_id=sourceId)
#     if categoryId:
#         qs = qs.filter(category_id=categoryId)
#     if dateFrom:
#         qs = qs.filter(date__gte=dateFrom)
#     if dateTo:
#         qs = qs.filter(date__lte=dateTo)

#     items, total, total_pages = await apaginate_queryset(qs, page, per_page)
#     return {
#         "items": [item async for item in items],
#         "total": total,
#         "page": page,
#         "per_page": per_page,
#         "total_pages": total_pages,
#     }


# @router.post("/", auth=auth, response=IncomeOut)
# async def create_income(request, payload: IncomeCreate):
#     """Create a new income record."""
#     source = await aget_object_or_404(
#         IncomeSource, id=payload.sourceId, owner=request.user
#     )
#     category = await aget_object_or_404(
#         IncomeCategory, id=payload.categoryId, owner=request.user
#     )

#     return await Income.objects.acreate(
#         source=source,
#         amount=payload.amount,
#         date=payload.date,
#         bank_account_id=payload.bankAccountId,
#         category=category,
#         transaction_id=payload.transactionId,
#         description=payload.description,
#         is_recurring=payload.isRecurring,
#         recurring_cycle=payload.recurringCycle,
#         currency=payload.currency,
#         owner=request.user,
#     )


# @router.get("/{income_id}/", auth=auth, response=IncomeOut)
# async def get_income(request, income_id: str):
#     """Get a specific income record by ID."""
#     return await aget_object_or_404(Income, id=income_id, owner=request.user)


# @router.delete("/{income_id}/", auth=auth, response=MessageOut)
# async def delete_income(request, income_id: str):
#     """Delete an income record."""
#     income = await aget_object_or_404(Income, id=income_id, owner=request.user)
#     await income.adelete()
#     return {"message": "Income deleted successfully"}

"""
Income API — full CRUD for IncomeSource, IncomeCategory, and Income.

All endpoints require BearerAuth (JWT).
All querysets are filtered by `request.user` (tenant isolation).
List endpoints use `apaginate_queryset` from `common.pagination`.

Routes (prefixed with /api/income):
  ── Categories ─────────────────────────────────────────────
  GET    /categories/                     List categories (paginated, filterable)
  POST   /categories/                     Create category
  PUT    /categories/{category_id}/       Update category
  DELETE /categories/{category_id}/       Delete category

  ── Sources ────────────────────────────────────────────────
  GET    /sources/                        List sources (paginated, filterable)
  POST   /sources/                        Create source
  PUT    /sources/{source_id}/            Update source
  DELETE /sources/{source_id}/            Delete source

  ── Incomes ────────────────────────────────────────────────
  GET    /                                List incomes (paginated, filterable)
  POST   /                                Create income
  GET    /{income_id}/                    Retrieve income
  DELETE /{income_id}/                    Delete income
"""

from typing import Optional

from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import aget_object_or_404
from ninja import Router

from common.pagination import (
    PaginatedResponse,
    PaginationSchema,
    apaginate_queryset,
)
from common.permissions import BearerAuth

from .models import Income, IncomeCategory, IncomeSource
from .schemas import (
    IncomeCategoryCreate,
    IncomeCategoryOut,
    IncomeCategoryUpdate,
    IncomeCreate,
    IncomeOut,
    IncomeSourceCreate,
    IncomeSourceOut,
    IncomeSourceUpdate,
    MessageOut,
)

router = Router(tags=["Income"])
auth = BearerAuth()


# ══════════════════════════════════════════════════════════════════════════════
# Income Category Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/categories/", auth=auth, response=PaginatedResponse[IncomeCategoryOut])
async def list_income_categories(
    request,
    page: int = PaginationSchema.__fields__["page"].default,
    per_page: int = PaginationSchema.__fields__["per_page"].default,
    type: Optional[str] = None,
):
    """List all income categories for the authenticated user (paginated)."""
    qs = IncomeCategory.objects.filter(owner=request.user)
    if type:
        qs = qs.filter(type=type)
    items, total, total_pages = await apaginate_queryset(qs, page, per_page)
    return {
        "items": [item async for item in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.post("/categories/", auth=auth, response=IncomeCategoryOut)
async def create_income_category(request, payload: IncomeCategoryCreate):
    """Create a new income category."""
    return await IncomeCategory.objects.acreate(
        name=payload.name,
        icon=payload.icon,
        color=payload.color,
        type=payload.type,
        owner=request.user,
    )


@router.put("/categories/{category_id}/", auth=auth, response=IncomeCategoryOut)
async def update_income_category(
    request, category_id: str, payload: IncomeCategoryUpdate
):
    """Update an income category."""
    cat = await aget_object_or_404(IncomeCategory, id=category_id, owner=request.user)

    if payload.name is not None:
        cat.name = payload.name
    if payload.icon is not None:
        cat.icon = payload.icon
    if payload.color is not None:
        cat.color = payload.color
    if payload.type is not None:
        cat.type = payload.type
    await cat.asave()

    return cat


@router.delete("/categories/{category_id}/", auth=auth, response=MessageOut)
async def delete_income_category(request, category_id: str):
    """Delete an income category."""
    cat = await aget_object_or_404(IncomeCategory, id=category_id, owner=request.user)
    await cat.adelete()
    return {"message": "Income category deleted successfully"}


# ══════════════════════════════════════════════════════════════════════════════
# Income Source Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/sources/", auth=auth, response=PaginatedResponse[IncomeSourceOut])
async def list_income_sources(
    request,
    page: int = PaginationSchema.__fields__["page"].default,
    per_page: int = PaginationSchema.__fields__["per_page"].default,
    type: Optional[str] = None,
    isActive: Optional[bool] = None,
):
    """List all income sources for the authenticated user (paginated)."""
    qs = IncomeSource.objects.filter(owner=request.user)
    if type:
        qs = qs.filter(type=type)
    if isActive is not None:
        qs = qs.filter(is_active=isActive)
    items, total, total_pages = await apaginate_queryset(qs, page, per_page)
    return {
        "items": [item async for item in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.post("/sources/", auth=auth, response=IncomeSourceOut)
async def create_income_source(request, payload: IncomeSourceCreate):
    """Create a new income source."""
    return await IncomeSource.objects.acreate(
        name=payload.name,
        type=payload.type,
        is_active=payload.isActive,
        monthly_amount=payload.monthlyAmount,
        currency=payload.currency,
        owner=request.user,
    )


@router.put("/sources/{source_id}/", auth=auth, response=IncomeSourceOut)
async def update_income_source(request, source_id: str, payload: IncomeSourceUpdate):
    """Update an income source."""
    source = await aget_object_or_404(IncomeSource, id=source_id, owner=request.user)

    if payload.name is not None:
        source.name = payload.name
    if payload.type is not None:
        source.type = payload.type
    if payload.isActive is not None:
        source.is_active = payload.isActive
    if payload.monthlyAmount is not None:
        source.monthly_amount = payload.monthlyAmount
    if payload.currency is not None:
        source.currency = payload.currency
    await source.asave()

    return source


@router.delete("/sources/{source_id}/", auth=auth, response=MessageOut)
async def delete_income_source(request, source_id: str):
    """Delete an income source. Protected: cannot delete if linked income records exist."""
    source = await aget_object_or_404(IncomeSource, id=source_id, owner=request.user)
    has_incomes = await Income.objects.filter(source=source).aexists()
    if has_incomes:
        raise DjangoValidationError(
            "Cannot delete this income source because it has linked income records. "
            "Deactivate it instead."
        )
    await source.adelete()
    return {"message": "Income source deleted successfully"}


# ══════════════════════════════════════════════════════════════════════════════
# Income Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/", auth=auth, response=PaginatedResponse[IncomeOut])
async def list_incomes(
    request,
    page: int = PaginationSchema.__fields__["page"].default,
    per_page: int = PaginationSchema.__fields__["per_page"].default,
    sourceId: Optional[str] = None,
    categoryId: Optional[str] = None,
    dateFrom: Optional[str] = None,
    dateTo: Optional[str] = None,
):
    """List incomes for the authenticated user, filterable by source, category, and date range."""
    qs = Income.objects.filter(owner=request.user).select_related("source", "category")

    if sourceId:
        qs = qs.filter(source_id=sourceId)
    if categoryId:
        qs = qs.filter(category_id=categoryId)
    if dateFrom:
        qs = qs.filter(date__gte=dateFrom)
    if dateTo:
        qs = qs.filter(date__lte=dateTo)

    items, total, total_pages = await apaginate_queryset(qs, page, per_page)
    return {
        "items": [item async for item in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.post("/", auth=auth, response=IncomeOut)
async def create_income(request, payload: IncomeCreate):
    """Create a new income record."""
    source = await aget_object_or_404(
        IncomeSource, id=payload.sourceId, owner=request.user
    )
    category = await aget_object_or_404(
        IncomeCategory, id=payload.categoryId, owner=request.user
    )

    return await Income.objects.acreate(
        source=source,
        amount=payload.amount,
        date=payload.date,
        bank_account_id=payload.bankAccountId,
        category=category,
        transaction_id=payload.transactionId,
        description=payload.description,
        is_recurring=payload.isRecurring,
        recurring_cycle=payload.recurringCycle,
        currency=payload.currency,
        owner=request.user,
    )


@router.get("/{income_id}/", auth=auth, response=IncomeOut)
async def get_income(request, income_id: str):
    """Get a specific income record by ID."""
    return await aget_object_or_404(Income, id=income_id, owner=request.user)


@router.delete("/{income_id}/", auth=auth, response=MessageOut)
async def delete_income(request, income_id: str):
    """Delete an income record."""
    income = await aget_object_or_404(Income, id=income_id, owner=request.user)
    await income.adelete()
    return {"message": "Income deleted successfully"}
