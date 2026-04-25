# """
# Expense app API endpoints for FinLife Personal Finance SaaS.

# All endpoints:
#   - Require BearerAuth (JWT) via common.permissions.BearerAuth
#   - Filter by request.user for tenant isolation
#   - Use paginate_queryset from common.pagination for list endpoints
#   - Return camelCase schemas matching frontend interfaces
# """

# from typing import Optional

# from django.db.models import Sum
# from django.shortcuts import aget_object_or_404
# from ninja import Query, Router

# from common.pagination import PaginatedResponse, PaginationSchema, apaginate_queryset
# from common.permissions import BearerAuth

# from .models import Expense, ExpenseCategory
# from .schemas import (
#     CategoryBreakdownOut,
#     ExpenseCategoryCreate,
#     ExpenseCategoryOut,
#     ExpenseCategoryUpdate,
#     ExpenseCreate,
#     ExpenseOut,
#     ExpenseUpdate,
#     MessageOut,
# )

# router = Router(tags=["Expense"], auth=BearerAuth())


# # ==================== Helper Functions ====================


# def _build_expense_out(expense: Expense) -> dict:
#     """Helper to build ExpenseOut dict from a model instance (same pattern as income)."""
#     return {
#         "id": str(expense.id),
#         "amount": expense.amount,
#         "date": expense.date.isoformat(),
#         "bankAccountId": (
#             str(expense.bank_account_id) if expense.bank_account_id else None
#         ),
#         "cardId": str(expense.card_id) if expense.card_id else None,
#         "categoryId": str(expense.category_id),
#         "transactionId": (
#             str(expense.transaction_id) if expense.transaction_id else None
#         ),
#         "description": expense.description,
#         "isRecurring": expense.is_recurring,
#         "recurringCycle": expense.recurring_cycle,
#         "tags": expense.tags or [],
#         "currency": expense.currency,
#         "createdAt": expense.created_at.isoformat(),
#         "updatedAt": expense.updated_at.isoformat(),
#     }


# # ==================== Expense Category Endpoints ====================


# @router.get(
#     "/categories/",
#     response=PaginatedResponse[ExpenseCategoryOut],
#     summary="List expense categories",
# )
# async def list_expense_categories(
#     request,
#     pagination: PaginationSchema = Query(...),
#     type: Optional[str] = Query(
#         None, description="Filter by type: needs|wants|savings|investments"
#     ),
# ):
#     """
#     List all expense categories for the authenticated user (paginated).
#     Frontend: GET /api/expense/categories/
#     """
#     qs = ExpenseCategory.objects.filter(owner=request.user)
#     if type:
#         qs = qs.filter(type=type)
#     items, total, total_pages = await apaginate_queryset(
#         qs, pagination.page, pagination.per_page
#     )
#     print([item async for item in items])  # Debug: print the items being returned
#     return {
#         "items": [item async for item in items],
#         "total": total,
#         "page": pagination.page,
#         "per_page": pagination.per_page,
#         "total_pages": total_pages,
#     }


# @router.post(
#     "/categories/",
#     response={201: ExpenseCategoryOut, 400: MessageOut},
#     summary="Create expense category",
# )
# async def create_expense_category(request, payload: ExpenseCategoryCreate):
#     """
#     Create a new expense category.
#     Frontend: POST /api/expense/categories/
#     """
#     try:
#         category = await ExpenseCategory.objects.acreate(
#             owner=request.user,
#             name=payload.name,
#             icon=payload.icon or "",
#             color=payload.color or "",
#             type=payload.type,
#             budget_limit=payload.budgetLimit,
#             currency=payload.currency,
#         )
#     except Exception as e:
#         return 400, {"message": str(e)}
#     return 201, category


# @router.get(
#     "/categories/{category_id}/",
#     response={200: ExpenseCategoryOut, 404: MessageOut},
#     summary="Get expense category",
# )
# async def get_expense_category(request, category_id: str):
#     """
#     Get a specific expense category by ID.
#     Frontend: GET /api/expense/categories/{id}/
#     """
#     category = await aget_object_or_404(
#         ExpenseCategory, id=category_id, owner=request.user
#     )
#     return category


# @router.put(
#     "/categories/{category_id}/",
#     response={200: ExpenseCategoryOut, 404: MessageOut},
#     summary="Update expense category",
# )
# async def update_expense_category(
#     request, category_id: str, payload: ExpenseCategoryUpdate
# ):
#     """
#     Update an expense category.
#     Frontend: PUT /api/expense/categories/{id}/
#     """
#     category = await aget_object_or_404(
#         ExpenseCategory, id=category_id, owner=request.user
#     )

#     if payload.name is not None:
#         category.name = payload.name
#     if payload.icon is not None:
#         category.icon = payload.icon
#     if payload.color is not None:
#         category.color = payload.color
#     if payload.type is not None:
#         category.type = payload.type
#     if payload.budgetLimit is not None:
#         category.budget_limit = payload.budgetLimit
#     if payload.currency is not None:
#         category.currency = payload.currency

#     await category.asave()
#     await category.arefresh_from_db()
#     return category


# @router.delete(
#     "/categories/{category_id}/",
#     response={200: MessageOut, 404: MessageOut},
#     summary="Delete expense category",
# )
# async def delete_expense_category(request, category_id: str):
#     """
#     Delete an expense category.
#     Frontend: DELETE /api/expense/categories/{id}/
#     """
#     category = await aget_object_or_404(
#         ExpenseCategory, id=category_id, owner=request.user
#     )
#     await category.adelete()
#     return {"message": "Expense category deleted successfully"}


# # ==================== Expense Endpoints ====================


# @router.get(
#     "/",
#     response=PaginatedResponse[ExpenseOut],
#     summary="List expenses",
# )
# async def list_expenses(
#     request,
#     pagination: PaginationSchema = Query(...),
#     categoryId: Optional[str] = Query(None, description="Filter by category ID"),
#     dateFrom: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
#     dateTo: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
#     isRecurring: Optional[bool] = Query(None, description="Filter by recurring status"),
# ):
#     """
#     List expenses for the authenticated user (paginated, filterable).
#     Frontend: GET /api/expense/
#     """
#     qs = Expense.objects.filter(owner=request.user).select_related("category")

#     if categoryId:
#         qs = qs.filter(category_id=categoryId)
#     if dateFrom:
#         qs = qs.filter(date__gte=dateFrom)
#     if dateTo:
#         qs = qs.filter(date__lte=dateTo)
#     if isRecurring is not None:
#         qs = qs.filter(is_recurring=isRecurring)

#     items, total, total_pages = await apaginate_queryset(
#         qs, pagination.page, pagination.per_page
#     )
#     return {
#         "items": [_build_expense_out(item) async for item in items],
#         "total": total,
#         "page": pagination.page,
#         "per_page": pagination.per_page,
#         "total_pages": total_pages,
#     }


# @router.post(
#     "/",
#     response={201: ExpenseOut, 400: MessageOut},
#     summary="Create expense",
# )
# async def create_expense(request, payload: ExpenseCreate):
#     """
#     Create a new expense.
#     Frontend: POST /api/expense/
#     """
#     try:
#         category = await aget_object_or_404(
#             ExpenseCategory, id=payload.categoryId, owner=request.user
#         )
#         expense = await Expense.objects.acreate(
#             owner=request.user,
#             amount=payload.amount,
#             date=payload.date,
#             bank_account_id=payload.bankAccountId,
#             card_id=payload.cardId,
#             category=category,
#             transaction_id=payload.transactionId,
#             description=payload.description or "",
#             is_recurring=payload.isRecurring,
#             recurring_cycle=payload.recurringCycle,
#             tags=payload.tags or [],
#             currency=payload.currency,
#         )
#     except Exception as e:
#         return 400, {"message": str(e)}
#     return 201, _build_expense_out(expense)


# @router.get(
#     "/{expense_id}/",
#     response={200: ExpenseOut, 404: MessageOut},
#     summary="Get expense",
# )
# async def get_expense(request, expense_id: str):
#     """
#     Get a specific expense by ID.
#     Frontend: GET /api/expense/{id}/
#     """
#     expense = await aget_object_or_404(Expense, id=expense_id, owner=request.user)
#     return _build_expense_out(expense)


# @router.put(
#     "/{expense_id}/",
#     response={200: ExpenseOut, 404: MessageOut},
#     summary="Update expense",
# )
# async def update_expense(request, expense_id: str, payload: ExpenseUpdate):
#     """
#     Update an existing expense.
#     Frontend: PUT /api/expense/{id}/
#     """
#     expense = await aget_object_or_404(Expense, id=expense_id, owner=request.user)

#     if payload.amount is not None:
#         expense.amount = payload.amount
#     if payload.date is not None:
#         expense.date = payload.date
#     if payload.bankAccountId is not None:
#         expense.bank_account_id = payload.bankAccountId
#     if payload.cardId is not None:
#         expense.card_id = payload.cardId
#     if payload.categoryId is not None:
#         expense.category = await aget_object_or_404(
#             ExpenseCategory, id=payload.categoryId, owner=request.user
#         )
#     if payload.transactionId is not None:
#         expense.transaction_id = payload.transactionId
#     if payload.description is not None:
#         expense.description = payload.description
#     if payload.isRecurring is not None:
#         expense.is_recurring = payload.isRecurring
#     if payload.recurringCycle is not None:
#         expense.recurring_cycle = payload.recurringCycle
#     if payload.tags is not None:
#         expense.tags = payload.tags
#     if payload.currency is not None:
#         expense.currency = payload.currency

#     await expense.asave()
#     await expense.arefresh_from_db()
#     return _build_expense_out(expense)


# @router.delete(
#     "/{expense_id}/",
#     response={200: MessageOut, 404: MessageOut},
#     summary="Delete expense",
# )
# async def delete_expense(request, expense_id: str):
#     """
#     Delete an expense.
#     Frontend: DELETE /api/expense/{id}/
#     """
#     expense = await aget_object_or_404(Expense, id=expense_id, owner=request.user)
#     await expense.adelete()
#     return {"message": "Expense deleted successfully"}


# # ==================== Category Breakdown ====================


# @router.get(
#     "/category-breakdown/",
#     response=list[CategoryBreakdownOut],
#     summary="Expense category breakdown",
# )
# async def category_breakdown(
#     request,
#     dateFrom: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
#     dateTo: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
# ):
#     """
#     Get expense breakdown by category with totals and percentages.
#     Frontend: GET /api/expense/category-breakdown/
#     """
#     qs = Expense.objects.filter(owner=request.user).select_related("category")

#     if dateFrom:
#         qs = qs.filter(date__gte=dateFrom)
#     if dateTo:
#         qs = qs.filter(date__lte=dateTo)

#     # Aggregate totals per category
#     aggregates = (
#         qs.values("category_id").annotate(total=Sum("amount")).order_by("-total")
#     )

#     # Materialize aggregates to avoid async double-consumption
#     aggregates_list = [a async for a in aggregates]
#     grand_total = sum(a["total"] or 0 for a in aggregates_list)
#     results = []

#     # Batch-load all categories to avoid N+1 queries
#     cat_ids = [a["category_id"] for a in aggregates_list if a["category_id"]]
#     categories_map = {
#         cat.id: cat async for cat in ExpenseCategory.objects.filter(id__in=cat_ids)
#     }

#     async for agg in aggregates_list:
#         cat = categories_map.get(agg["category_id"])
#         if not cat:
#             continue
#         total = agg["total"] or 0
#         percentage = round((total / grand_total) * 100, 1) if grand_total > 0 else 0.0
#         results.append(
#             CategoryBreakdownOut(
#                 category=cat,
#                 total=total,
#                 percentage=percentage,
#             )
#         )

#     return results

"""
Expense API — full CRUD for ExpenseCategory and Expense.

All endpoints require BearerAuth (JWT).
All querysets are filtered by `request.user` (tenant isolation).
List endpoints use `apaginate_queryset` from `common.pagination`.

Routes (prefixed with /api/expense):
  ── Categories ─────────────────────────────────────────────
  GET    /categories/                     List categories (paginated, filterable)
  POST   /categories/                     Create category
  PUT    /categories/{category_id}/       Update category
  DELETE /categories/{category_id}/       Delete category

  ── Expenses ───────────────────────────────────────────────
  GET    /                                List expenses (paginated, filterable)
  POST   /                                Create expense
  GET    /{expense_id}/                   Retrieve expense
  PUT    /{expense_id}/                   Update expense
  DELETE /{expense_id}/                   Delete expense
"""

from typing import Optional

from django.shortcuts import aget_object_or_404
from ninja import Router

from common.pagination import (
    PaginatedResponse,
    PaginationSchema,
    apaginate_queryset,
)
from common.permissions import BearerAuth

from .models import Expense, ExpenseCategory
from .schemas import (
    ExpenseCategoryCreate,
    ExpenseCategoryOut,
    ExpenseCategoryUpdate,
    ExpenseCreate,
    ExpenseOut,
    ExpenseUpdate,
    MessageOut,
)

router = Router(tags=["Expense"])
auth = BearerAuth()


# ══════════════════════════════════════════════════════════════════════════════
# Expense Category Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/categories/", auth=auth, response=PaginatedResponse[ExpenseCategoryOut])
async def list_expense_categories(
    request,
    page: int = PaginationSchema.__fields__["page"].default,
    per_page: int = PaginationSchema.__fields__["per_page"].default,
    type: Optional[str] = None,
):
    """List all expense categories for the authenticated user (paginated)."""
    qs = ExpenseCategory.objects.filter(owner=request.user)
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


@router.post("/categories/", auth=auth, response=ExpenseCategoryOut)
async def create_expense_category(request, payload: ExpenseCategoryCreate):
    """Create a new expense category."""
    return await ExpenseCategory.objects.acreate(
        name=payload.name,
        icon=payload.icon,
        color=payload.color,
        type=payload.type,
        budget_limit=payload.budgetLimit,
        currency=payload.currency,
        owner=request.user,
    )


@router.put("/categories/{category_id}/", auth=auth, response=ExpenseCategoryOut)
async def update_expense_category(
    request, category_id: str, payload: ExpenseCategoryUpdate
):
    """Update an expense category."""
    cat = await aget_object_or_404(ExpenseCategory, id=category_id, owner=request.user)

    if payload.name is not None:
        cat.name = payload.name
    if payload.icon is not None:
        cat.icon = payload.icon
    if payload.color is not None:
        cat.color = payload.color
    if payload.type is not None:
        cat.type = payload.type
    if payload.budgetLimit is not None:
        cat.budget_limit = payload.budgetLimit
    if payload.currency is not None:
        cat.currency = payload.currency
    await cat.asave()

    return cat


@router.delete("/categories/{category_id}/", auth=auth, response=MessageOut)
async def delete_expense_category(request, category_id: str):
    """Delete an expense category."""
    cat = await aget_object_or_404(ExpenseCategory, id=category_id, owner=request.user)
    await cat.adelete()
    return {"message": "Expense category deleted successfully"}


# ══════════════════════════════════════════════════════════════════════════════
# Expense Endpoints
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/", auth=auth, response=PaginatedResponse[ExpenseOut])
async def list_expenses(
    request,
    page: int = PaginationSchema.__fields__["page"].default,
    per_page: int = PaginationSchema.__fields__["per_page"].default,
    categoryId: Optional[str] = None,
    dateFrom: Optional[str] = None,
    dateTo: Optional[str] = None,
    isRecurring: Optional[bool] = None,
):
    """List expenses for the authenticated user, filterable by category, date range, and recurring status."""
    qs = Expense.objects.filter(owner=request.user).select_related("category")

    if categoryId:
        qs = qs.filter(category_id=categoryId)
    if dateFrom:
        qs = qs.filter(date__gte=dateFrom)
    if dateTo:
        qs = qs.filter(date__lte=dateTo)
    if isRecurring is not None:
        qs = qs.filter(is_recurring=isRecurring)

    items, total, total_pages = await apaginate_queryset(qs, page, per_page)
    return {
        "items": [item async for item in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.post("/", auth=auth, response=ExpenseOut)
async def create_expense(request, payload: ExpenseCreate):
    """Create a new expense record."""
    category = await aget_object_or_404(
        ExpenseCategory, id=payload.categoryId, owner=request.user
    )

    return await Expense.objects.acreate(
        amount=payload.amount,
        date=payload.date,
        bank_account_id=payload.bankAccountId,
        card_id=payload.cardId,
        category=category,
        transaction_id=payload.transactionId,
        description=payload.description,
        is_recurring=payload.isRecurring,
        recurring_cycle=payload.recurringCycle,
        tags=payload.tags,
        currency=payload.currency,
        owner=request.user,
    )


@router.get("/{expense_id}/", auth=auth, response=ExpenseOut)
async def get_expense(request, expense_id: str):
    """Get a specific expense record by ID."""
    return await aget_object_or_404(Expense, id=expense_id, owner=request.user)


@router.put("/{expense_id}/", auth=auth, response=ExpenseOut)
async def update_expense(request, expense_id: str, payload: ExpenseUpdate):
    """Update an existing expense record."""
    expense = await aget_object_or_404(Expense, id=expense_id, owner=request.user)

    if payload.amount is not None:
        expense.amount = payload.amount
    if payload.date is not None:
        expense.date = payload.date
    if payload.bankAccountId is not None:
        expense.bank_account_id = payload.bankAccountId
    if payload.cardId is not None:
        expense.card_id = payload.cardId
    if payload.categoryId is not None:
        expense.category = await aget_object_or_404(
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

    await expense.asave()
    return expense


@router.delete("/{expense_id}/", auth=auth, response=MessageOut)
async def delete_expense(request, expense_id: str):
    """Delete an expense record."""
    expense = await aget_object_or_404(Expense, id=expense_id, owner=request.user)
    await expense.adelete()
    return {"message": "Expense deleted successfully"}
