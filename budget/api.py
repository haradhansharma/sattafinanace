"""
Budget API endpoints (Django Ninja).

All endpoints require BearerAuth and filter by request.user.
Computed fields (allocatedAmount, spentAmount, remainingBalance, etc.) are
calculated here from actual Expense data and day-of-month projections.
"""

import calendar
from datetime import date
from typing import Optional

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from ninja import Router

from common.pagination import PaginatedResponse, PaginationSchema, paginate_queryset
from common.permissions import BearerAuth

from .models import Budget, BudgetCategory
from .schemas import (
    BudgetCategoryCreate,
    BudgetCategoryOut,
    BudgetCategoryUpdate,
    BudgetCreate,
    BudgetOut,
    BudgetUpdate,
    MessageOut,
)

router = Router(tags=["Budget"], auth=BearerAuth())


# ==================== Computation helpers ====================


def _month_range(month_str: str) -> tuple[date, date]:
    """Return (first_day, last_day) for a ``YYYY-MM`` string."""
    year, month = int(month_str[:4]), int(month_str[5:7])
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    return first, last


async def _category_spent(user, category_id: str, month_str: str) -> int:
    """Sum of Expense amounts for a given ExpenseCategory in a month (async)."""
    try:
        from apps.expense.models import Expense

        first, last = _month_range(month_str)
        result = await Expense.objects.filter(
            owner=user,
            category_id=category_id,
            date__gte=first,
            date__lte=last,
        ).aaggregate(total=Sum("amount"))
        return result["total"] or 0
    except Exception:
        return 0


def _today_info() -> tuple[int, int]:
    """Return (day_of_month, days_in_current_month)."""
    today = date.today()
    return today.day, calendar.monthrange(today.year, today.month)[1]


async def _build_category_out(cat: BudgetCategory) -> dict:
    """Build a BudgetCategoryOut dict with all computed fields (async)."""
    budget_amount = cat.budget_amount or 0
    month_str = cat.budget.month
    spent = await _category_spent(cat.owner, str(cat.category_id), month_str)

    remaining = budget_amount - spent
    is_over = spent > budget_amount if budget_amount > 0 else False

    today_dom, days_in_month = _today_info()
    days_left = max(days_in_month - today_dom, 1)

    # Linear forecast based on average daily spend so far
    if today_dom > 1:
        daily_avg = spent // today_dom
        forecasted = daily_avg * days_in_month
    else:
        forecasted = 0

    available = max(remaining, 0)
    over_amount = spent - budget_amount if is_over else 0

    daily_safe = max((budget_amount - spent) // days_left, 0) if not is_over else 0
    required_daily_reduction = over_amount // days_left if is_over else 0
    required_extra_income = over_amount if is_over else 0

    return {
        "id": str(cat.id),
        "name": cat.name,
        "categoryId": str(cat.category_id),
        "budgetAmount": budget_amount,
        "allocatedAmount": budget_amount,
        "availableBalance": available,
        "remainingBalance": remaining,
        "spentAmount": spent,
        "isOverBudget": is_over,
        "overAmount": over_amount,
        "forecastedSpend": forecasted,
        "dailySafeSpend": daily_safe,
        "requiredDailyReduction": required_daily_reduction,
        "requiredExtraIncome": required_extra_income,
    }


async def _build_budget_out(budget: Budget) -> dict:
    """Build a BudgetOut dict with all computed fields + embedded categories (async)."""
    cats = list(budget.categories.select_related("owner").all())
    categories_out = [await _build_category_out(c) for c in cats]

    total_budget = budget.total_budget_amount or 0
    allocated = sum(c["budgetAmount"] for c in categories_out)
    total_spent = sum(c["spentAmount"] for c in categories_out)
    remaining = total_budget - total_spent
    is_over = total_spent > total_budget if total_budget > 0 else False

    today_dom, days_in_month = _today_info()
    days_left = max(days_in_month - today_dom, 1)

    if today_dom > 1:
        daily_avg = total_spent // today_dom
        forecasted = daily_avg * days_in_month
    else:
        forecasted = 0

    forecast_gap = forecasted - total_budget if forecasted > total_budget else 0
    available = max(remaining, 0)
    over_amount = total_spent - total_budget if is_over else 0

    daily_safe = max((total_budget - total_spent) // days_left, 0) if not is_over else 0
    required_daily_reduction = over_amount // days_left if is_over else 0
    required_extra_income = over_amount if is_over else 0

    return {
        "id": str(budget.id),
        "createdAt": budget.created_at.isoformat(),
        "updatedAt": budget.updated_at.isoformat(),
        "name": budget.name,
        "month": budget.month,
        "currency": budget.currency,
        "totalBudgetAmount": total_budget,
        "allocatedAmount": allocated,
        "availableBalance": available,
        "remainingBalance": remaining,
        "isOverBudget": is_over,
        "overAmount": over_amount,
        "forecastedSpend": forecasted,
        "forecastGap": forecast_gap,
        "dailySafeSpend": daily_safe,
        "requiredDailyReduction": required_daily_reduction,
        "requiredExtraIncome": required_extra_income,
        "categories": categories_out,
    }


# ==================== Budget CRUD ====================


@router.get("/", response=PaginatedResponse[BudgetOut])
async def list_budgets(
    request,
    month: Optional[str] = None,
    pagination: PaginationSchema = PaginationSchema(),
):
    """List all budgets for the authenticated user, optionally filtered by month."""
    qs = Budget.objects.filter(owner=request.user)
    if month:
        qs = qs.filter(month=month)
    qs = qs.order_by("-month", "-created_at")

    items, total, total_pages = paginate_queryset(
        qs, pagination.page, pagination.per_page
    )
    items_out = [await _build_budget_out(b) for b in items]
    return PaginatedResponse(
        items=items_out,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=total_pages,
    )


@router.post("/", response={201: BudgetOut})
async def create_budget(request, payload: BudgetCreate):
    """Create a new budget with optional inline categories."""
    budget = Budget.objects.create(
        owner=request.user,
        name=payload.name,
        month=payload.month,
        currency=payload.currency,
        total_budget_amount=payload.totalBudgetAmount,
    )
    for cat_data in payload.categories:
        BudgetCategory.objects.create(
            owner=request.user,
            budget=budget,
            name=cat_data.name,
            category_id=cat_data.categoryId,
            budget_amount=cat_data.budgetAmount,
        )
    return 201, await _build_budget_out(budget)


@router.get("/current/", response=BudgetOut)
async def get_current_budget(request):
    """Get the budget for the current month (YYYY-MM)."""
    current_month = date.today().strftime("%Y-%m")
    budget = get_object_or_404(Budget, owner=request.user, month=current_month)
    return await _build_budget_out(budget)


@router.get("/{budget_id}/", response=BudgetOut)
async def get_budget(request, budget_id: str):
    """Get a specific budget by ID."""
    budget = get_object_or_404(Budget, id=budget_id, owner=request.user)
    return await _build_budget_out(budget)


@router.put("/{budget_id}/", response=BudgetOut)
async def update_budget(request, budget_id: str, payload: BudgetUpdate):
    """Update a budget and optionally replace its categories."""
    budget = get_object_or_404(Budget, id=budget_id, owner=request.user)

    if payload.name is not None:
        budget.name = payload.name
    if payload.totalBudgetAmount is not None:
        budget.total_budget_amount = payload.totalBudgetAmount
    if payload.currency is not None:
        budget.currency = payload.currency

    if payload.categories is not None:
        # Replace all categories atomically
        budget.categories.all().delete()
        for cat_data in payload.categories:
            BudgetCategory.objects.create(
                owner=request.user,
                budget=budget,
                name=cat_data.name,
                category_id=cat_data.categoryId,
                budget_amount=cat_data.budgetAmount,
            )

    budget.save()
    return await _build_budget_out(budget)


@router.delete("/{budget_id}/", response=MessageOut)
async def delete_budget(request, budget_id: str):
    """Delete a budget and all its categories."""
    budget = get_object_or_404(Budget, id=budget_id, owner=request.user)
    budget.delete()
    return MessageOut(message="Budget deleted successfully")


# ==================== Budget Category CRUD ====================


@router.post("/{budget_id}/categories/", response={201: BudgetCategoryOut})
async def add_category(request, budget_id: str, payload: BudgetCategoryCreate):
    """Add a category to an existing budget."""
    budget = get_object_or_404(Budget, id=budget_id, owner=request.user)
    cat = BudgetCategory.objects.create(
        owner=request.user,
        budget=budget,
        name=payload.name,
        category_id=payload.categoryId,
        budget_amount=payload.budgetAmount,
    )
    return 201, await _build_category_out(cat)


@router.put("/{budget_id}/categories/{category_id}/", response=BudgetCategoryOut)
async def update_category(
    request, budget_id: str, category_id: str, payload: BudgetCategoryUpdate
):
    """Update a specific budget category."""
    cat = get_object_or_404(
        BudgetCategory, id=category_id, budget_id=budget_id, owner=request.user
    )
    if payload.name is not None:
        cat.name = payload.name
    if payload.categoryId is not None:
        cat.category_id = payload.categoryId
    if payload.budgetAmount is not None:
        cat.budget_amount = payload.budgetAmount
    cat.save()
    return await _build_category_out(cat)


@router.delete("/{budget_id}/categories/{category_id}/", response=MessageOut)
async def delete_category(request, budget_id: str, category_id: str):
    """Delete a specific budget category."""
    cat = get_object_or_404(
        BudgetCategory, id=category_id, budget_id=budget_id, owner=request.user
    )
    cat.delete()
    return MessageOut(message="Budget category deleted successfully")
