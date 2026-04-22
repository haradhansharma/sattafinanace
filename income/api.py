"""
Income API — full CRUD for IncomeSource, IncomeCategory, and Income.

All endpoints require BearerAuth (JWT).
All querysets are filtered by `request.user` (tenant isolation).
List endpoints use `paginate_queryset` from `common.pagination`.

Routes (prefixed with /api/income):
  ── Categories ─────────────────────────────────────────────
  GET    /categories/                     List categories
  POST   /categories/                     Create category
  PUT    /categories/{category_id}/       Update category
  DELETE /categories/{category_id}/       Delete category

  ── Sources ────────────────────────────────────────────────
  GET    /sources/                        List sources
  POST   /sources/                        Create source
  PUT    /sources/{source_id}/            Update source
  DELETE /sources/{source_id}/            Delete source

  ── Incomes ────────────────────────────────────────────────
  GET    /                                List incomes (paginated, filterable)
  POST   /                                Create income
  GET    /{income_id}/                    Retrieve income
  PUT    /{income_id}/                    Update income
  DELETE /{income_id}/                    Delete income
"""

from typing import List, Optional

from django.shortcuts import get_object_or_404
from ninja import Router

from common.pagination import (
    PaginatedResponse,
    PaginationSchema,
    paginate_queryset,
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
    IncomeUpdate,
    MessageOut,
)

router = Router(tags=["Income"])
auth = BearerAuth()


# ══════════════════════════════════════════════════════════════════════════════
# Income Category Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/categories/", auth=auth, response=List[IncomeCategoryOut])
async def list_income_categories(request):
    """List all income categories for the authenticated user."""
    qs = IncomeCategory.objects.filter(owner=request.user)
    return [
        IncomeCategoryOut(
            id=str(c.id),
            name=c.name,
            icon=c.icon,
            color=c.color,
            type=c.type,
            createdAt=c.created_at.isoformat(),
            updatedAt=c.updated_at.isoformat(),
        )
        for c in qs
    ]


@router.post("/categories/", auth=auth, response=IncomeCategoryOut)
async def create_income_category(request, payload: IncomeCategoryCreate):
    """Create a new income category."""
    cat = IncomeCategory.objects.create(
        name=payload.name,
        icon=payload.icon,
        color=payload.color,
        type=payload.type,
        owner=request.user,
    )
    return IncomeCategoryOut(
        id=str(cat.id),
        name=cat.name,
        icon=cat.icon,
        color=cat.color,
        type=cat.type,
        createdAt=cat.created_at.isoformat(),
        updatedAt=cat.updated_at.isoformat(),
    )


@router.put("/categories/{category_id}/", auth=auth, response=IncomeCategoryOut)
async def update_income_category(
    request, category_id: str, payload: IncomeCategoryUpdate
):
    """Update an income category."""
    cat = get_object_or_404(IncomeCategory, id=category_id, owner=request.user)

    if payload.name is not None:
        cat.name = payload.name
    if payload.icon is not None:
        cat.icon = payload.icon
    if payload.color is not None:
        cat.color = payload.color
    if payload.type is not None:
        cat.type = payload.type
    cat.save()

    return IncomeCategoryOut(
        id=str(cat.id),
        name=cat.name,
        icon=cat.icon,
        color=cat.color,
        type=cat.type,
        createdAt=cat.created_at.isoformat(),
        updatedAt=cat.updated_at.isoformat(),
    )


@router.delete("/categories/{category_id}/", auth=auth, response=MessageOut)
async def delete_income_category(request, category_id: str):
    """Delete an income category."""
    cat = get_object_or_404(IncomeCategory, id=category_id, owner=request.user)
    cat.delete()
    return {"message": "Income category deleted successfully"}


# ══════════════════════════════════════════════════════════════════════════════
# Income Source Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/sources/", auth=auth, response=List[IncomeSourceOut])
async def list_income_sources(request):
    """List all income sources for the authenticated user."""
    qs = IncomeSource.objects.filter(owner=request.user)
    return [
        IncomeSourceOut(
            id=str(s.id),
            name=s.name,
            type=s.type,
            isActive=s.is_active,
            monthlyAmount=s.monthly_amount,
            createdAt=s.created_at.isoformat(),
            updatedAt=s.updated_at.isoformat(),
        )
        for s in qs
    ]


@router.post("/sources/", auth=auth, response=IncomeSourceOut)
async def create_income_source(request, payload: IncomeSourceCreate):
    """Create a new income source."""
    source = IncomeSource.objects.create(
        name=payload.name,
        type=payload.type,
        is_active=payload.isActive,
        monthly_amount=payload.monthlyAmount,
        owner=request.user,
    )
    return IncomeSourceOut(
        id=str(source.id),
        name=source.name,
        type=source.type,
        isActive=source.is_active,
        monthlyAmount=source.monthly_amount,
        createdAt=source.created_at.isoformat(),
        updatedAt=source.updated_at.isoformat(),
    )


@router.put("/sources/{source_id}/", auth=auth, response=IncomeSourceOut)
async def update_income_source(request, source_id: str, payload: IncomeSourceUpdate):
    """Update an income source."""
    source = get_object_or_404(IncomeSource, id=source_id, owner=request.user)

    if payload.name is not None:
        source.name = payload.name
    if payload.type is not None:
        source.type = payload.type
    if payload.isActive is not None:
        source.is_active = payload.isActive
    if payload.monthlyAmount is not None:
        source.monthly_amount = payload.monthlyAmount
    source.save()

    return IncomeSourceOut(
        id=str(source.id),
        name=source.name,
        type=source.type,
        isActive=source.is_active,
        monthlyAmount=source.monthly_amount,
        createdAt=source.created_at.isoformat(),
        updatedAt=source.updated_at.isoformat(),
    )


@router.delete("/sources/{source_id}/", auth=auth, response=MessageOut)
async def delete_income_source(request, source_id: str):
    """Delete an income source."""
    source = get_object_or_404(IncomeSource, id=source_id, owner=request.user)
    source.delete()
    return {"message": "Income source deleted successfully"}


# ══════════════════════════════════════════════════════════════════════════════
# Income Endpoints
# ══════════════════════════════════════════════════════════════════════════════


def _build_income_out(income: Income) -> dict:
    """Helper to build IncomeOut dict from a model instance."""
    return {
        "id": str(income.id),
        "sourceId": str(income.source_id),
        "amount": income.amount,
        "date": income.date.isoformat(),
        "bankAccountId": str(income.bank_account_id),
        "categoryId": str(income.category_id),
        "transactionId": str(income.transaction_id) if income.transaction_id else None,
        "description": income.description,
        "isRecurring": income.is_recurring,
        "recurringCycle": income.recurring_cycle,
        "currency": income.currency,
        "createdAt": income.created_at.isoformat(),
        "updatedAt": income.updated_at.isoformat(),
    }


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

    items, total, total_pages = paginate_queryset(qs, page, per_page)
    return {
        "items": [_build_income_out(i) for i in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.post("/", auth=auth, response=IncomeOut)
async def create_income(request, payload: IncomeCreate):
    """Create a new income record."""
    source = get_object_or_404(IncomeSource, id=payload.sourceId, owner=request.user)
    category = get_object_or_404(
        IncomeCategory, id=payload.categoryId, owner=request.user
    )

    income = Income.objects.create(
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
    return _build_income_out(income)


@router.get("/{income_id}/", auth=auth, response=IncomeOut)
async def get_income(request, income_id: str):
    """Get a specific income record by ID."""
    income = get_object_or_404(Income, id=income_id, owner=request.user)
    return _build_income_out(income)


@router.put("/{income_id}/", auth=auth, response=IncomeOut)
async def update_income(request, income_id: str, payload: IncomeUpdate):
    """Update an existing income record."""
    income = get_object_or_404(Income, id=income_id, owner=request.user)

    if payload.sourceId is not None:
        income.source = get_object_or_404(
            IncomeSource, id=payload.sourceId, owner=request.user
        )
    if payload.amount is not None:
        income.amount = payload.amount
    if payload.date is not None:
        income.date = payload.date
    if payload.bankAccountId is not None:
        income.bank_account_id = payload.bankAccountId
    if payload.categoryId is not None:
        income.category = get_object_or_404(
            IncomeCategory, id=payload.categoryId, owner=request.user
        )
    if payload.transactionId is not None:
        income.transaction_id = payload.transactionId
    if payload.description is not None:
        income.description = payload.description
    if payload.isRecurring is not None:
        income.is_recurring = payload.isRecurring
    if payload.recurringCycle is not None:
        income.recurring_cycle = payload.recurringCycle
    if payload.currency is not None:
        income.currency = payload.currency

    income.save()
    return _build_income_out(income)


@router.delete("/{income_id}/", auth=auth, response=MessageOut)
async def delete_income(request, income_id: str):
    """Delete an income record."""
    income = get_object_or_404(Income, id=income_id, owner=request.user)
    income.delete()
    return {"message": "Income deleted successfully"}
