"""
Expense app API endpoints for FinLife Personal Finance SaaS.

All endpoints:
  - Require BearerAuth (JWT) via common.permissions.BearerAuth
  - Filter by request.user for tenant isolation
  - Use paginate_queryset from common.pagination for list endpoints
  - Return camelCase schemas matching frontend interfaces
"""

from typing import Optional

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from ninja import Query, Router

from common.pagination import PaginatedResponse, PaginationSchema, paginate_queryset
from common.permissions import BearerAuth

from .models import Expense, ExpenseCategory
from .schemas import (
    CategoryBreakdownOut,
    ExpenseCategoryCreate,
    ExpenseCategoryOut,
    ExpenseCategoryUpdate,
    ExpenseCreate,
    ExpenseOut,
    ExpenseUpdate,
    MessageOut,
)

router = Router(tags=["Expense"], auth=BearerAuth())

# ==================== Expense Category Endpoints ====================


@router.get(
    "/categories/",
    response=PaginatedResponse[ExpenseCategoryOut],
    summary="List expense categories",
)
async def list_expense_categories(
    request,
    pagination: PaginationSchema = Query(...),
    type: Optional[str] = Query(
        None, description="Filter by type: needs|wants|savings|investments"
    ),
):
    """
    List all expense categories for the authenticated user (paginated).
    Frontend: GET /api/expense/categories/
    """
    qs = ExpenseCategory.objects.filter(owner=request.user)
    if type:
        qs = qs.filter(type=type)
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
    "/categories/",
    response={201: ExpenseCategoryOut, 400: MessageOut},
    summary="Create expense category",
)
async def create_expense_category(request, payload: ExpenseCategoryCreate):
    """
    Create a new expense category.
    Frontend: POST /api/expense/categories/
    """
    try:
        category = ExpenseCategory.objects.create(
            owner=request.user,
            name=payload.name,
            icon=payload.icon or "",
            color=payload.color or "",
            type=payload.type,
            budget_limit=payload.budgetLimit,
        )
    except Exception as e:
        return 400, {"message": str(e)}
    return 201, category


@router.get(
    "/categories/{category_id}/",
    response={200: ExpenseCategoryOut, 404: MessageOut},
    summary="Get expense category",
)
async def get_expense_category(request, category_id: str):
    """
    Get a specific expense category by ID.
    Frontend: GET /api/expense/categories/{id}/
    """
    category = get_object_or_404(ExpenseCategory, id=category_id, owner=request.user)
    return category


@router.put(
    "/categories/{category_id}/",
    response={200: ExpenseCategoryOut, 404: MessageOut},
    summary="Update expense category",
)
async def update_expense_category(
    request, category_id: str, payload: ExpenseCategoryUpdate
):
    """
    Update an expense category.
    Frontend: PUT /api/expense/categories/{id}/
    """
    category = get_object_or_404(ExpenseCategory, id=category_id, owner=request.user)

    if payload.name is not None:
        category.name = payload.name
    if payload.icon is not None:
        category.icon = payload.icon
    if payload.color is not None:
        category.color = payload.color
    if payload.type is not None:
        category.type = payload.type
    if payload.budgetLimit is not None:
        category.budget_limit = payload.budgetLimit

    category.save()
    category.refresh_from_db()
    return category


@router.delete(
    "/categories/{category_id}/",
    response={200: MessageOut, 404: MessageOut},
    summary="Delete expense category",
)
async def delete_expense_category(request, category_id: str):
    """
    Delete an expense category.
    Frontend: DELETE /api/expense/categories/{id}/
    """
    category = get_object_or_404(ExpenseCategory, id=category_id, owner=request.user)
    category.delete()
    return {"message": "Expense category deleted successfully"}


# ==================== Expense Endpoints ====================


@router.get(
    "/",
    response=PaginatedResponse[ExpenseOut],
    summary="List expenses",
)
async def list_expenses(
    request,
    pagination: PaginationSchema = Query(...),
    categoryId: Optional[str] = Query(None, description="Filter by category ID"),
    dateFrom: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    dateTo: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    isRecurring: Optional[bool] = Query(None, description="Filter by recurring status"),
):
    """
    List expenses for the authenticated user (paginated, filterable).
    Frontend: GET /api/expense/
    """
    qs = Expense.objects.filter(owner=request.user).select_related("category")

    if categoryId:
        qs = qs.filter(category_id=categoryId)
    if dateFrom:
        qs = qs.filter(date__gte=dateFrom)
    if dateTo:
        qs = qs.filter(date__lte=dateTo)
    if isRecurring is not None:
        qs = qs.filter(is_recurring=isRecurring)

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
    "/",
    response={201: ExpenseOut, 400: MessageOut},
    summary="Create expense",
)
async def create_expense(request, payload: ExpenseCreate):
    """
    Create a new expense.
    Frontend: POST /api/expense/
    """
    try:
        category = get_object_or_404(
            ExpenseCategory, id=payload.categoryId, owner=request.user
        )
        expense = Expense.objects.create(
            owner=request.user,
            amount=payload.amount,
            date=payload.date,
            bank_account_id=payload.bankAccountId,
            card_id=payload.cardId,
            category=category,
            transaction_id=payload.transactionId,
            description=payload.description or "",
            is_recurring=payload.isRecurring,
            recurring_cycle=payload.recurringCycle,
            tags=payload.tags or [],
            currency=payload.currency,
        )
    except Exception as e:
        return 400, {"message": str(e)}
    return 201, expense


@router.get(
    "/{expense_id}/",
    response={200: ExpenseOut, 404: MessageOut},
    summary="Get expense",
)
async def get_expense(request, expense_id: str):
    """
    Get a specific expense by ID.
    Frontend: GET /api/expense/{id}/
    """
    expense = get_object_or_404(Expense, id=expense_id, owner=request.user)
    return expense


@router.put(
    "/{expense_id}/",
    response={200: ExpenseOut, 404: MessageOut},
    summary="Update expense",
)
async def update_expense(request, expense_id: str, payload: ExpenseUpdate):
    """
    Update an existing expense.
    Frontend: PUT /api/expense/{id}/
    """
    expense = get_object_or_404(Expense, id=expense_id, owner=request.user)

    if payload.amount is not None:
        expense.amount = payload.amount
    if payload.date is not None:
        expense.date = payload.date
    if payload.bankAccountId is not None:
        expense.bank_account_id = payload.bankAccountId
    if payload.cardId is not None:
        expense.card_id = payload.cardId
    if payload.categoryId is not None:
        expense.category = get_object_or_404(
            ExpenseCategory, id=payload.categoryId, owner=request.user
        )
    if payload.transactionId is not None:
        expense.transaction_id = payload.transactionId
    if payload.description is not None:
        expense.description = payload.description
    if payload.isRecurring is not None:
        expense.is_recurring = payload.isRecurring
    if payload.recurringCycle is not None:
        expense.recurring_cycle = payload.recurringCycle
    if payload.tags is not None:
        expense.tags = payload.tags
    if payload.currency is not None:
        expense.currency = payload.currency

    expense.save()
    expense.refresh_from_db()
    return expense


@router.delete(
    "/{expense_id}/",
    response={200: MessageOut, 404: MessageOut},
    summary="Delete expense",
)
async def delete_expense(request, expense_id: str):
    """
    Delete an expense.
    Frontend: DELETE /api/expense/{id}/
    """
    expense = get_object_or_404(Expense, id=expense_id, owner=request.user)
    expense.delete()
    return {"message": "Expense deleted successfully"}


# ==================== Category Breakdown ====================


@router.get(
    "/category-breakdown/",
    response=list[CategoryBreakdownOut],
    summary="Expense category breakdown",
)
async def category_breakdown(
    request,
    dateFrom: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    dateTo: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
):
    """
    Get expense breakdown by category with totals and percentages.
    Frontend: GET /api/expense/category-breakdown/
    """
    qs = Expense.objects.filter(owner=request.user).select_related("category")

    if dateFrom:
        qs = qs.filter(date__gte=dateFrom)
    if dateTo:
        qs = qs.filter(date__lte=dateTo)

    # Aggregate totals per category
    aggregates = (
        qs.values("category_id").annotate(total=Sum("amount")).order_by("-total")
    )

    grand_total = sum(a["total"] or 0 for a in aggregates)
    results = []

    # Batch-load all categories to avoid N+1 queries
    cat_ids = [a["category_id"] for a in aggregates if a["category_id"]]
    categories_map = {
        cat.id: cat for cat in ExpenseCategory.objects.filter(id__in=cat_ids)
    }

    for agg in aggregates:
        cat = categories_map.get(agg["category_id"])
        if not cat:
            continue
        total = agg["total"] or 0
        percentage = round((total / grand_total) * 100, 1) if grand_total > 0 else 0.0
        results.append(
            CategoryBreakdownOut(
                category=cat,
                total=total,
                percentage=percentage,
            )
        )

    return results
