"""
Budget schemas (Django Ninja) — camelCase matching the frontend exactly.

Computed fields are default-0 on schemas and populated in the API layer via
helper functions that aggregate real Expense data.
"""

from typing import List, Optional

from ninja import Schema


# ==================== Budget Category Schemas ====================


class BudgetCategoryOut(Schema):
    """Full output for a single budget category including all computed fields."""

    id: str
    name: str
    categoryId: str
    budgetAmount: int

    # ── Computed fields (NOT stored in DB) ──
    allocatedAmount: int = 0
    availableBalance: int = 0
    remainingBalance: int = 0
    spentAmount: int = 0
    isOverBudget: bool = False
    overAmount: int = 0
    forecastedSpend: int = 0
    dailySafeSpend: int = 0
    requiredDailyReduction: int = 0
    requiredExtraIncome: int = 0


class BudgetCategoryCreate(Schema):
    """Payload for creating a budget category."""

    name: str
    categoryId: str
    budgetAmount: int = 0


class BudgetCategoryUpdate(Schema):
    """Payload for patching a budget category (all optional)."""

    name: Optional[str] = None
    categoryId: Optional[str] = None
    budgetAmount: Optional[int] = None


# ==================== Budget Schemas ====================


class BudgetOut(Schema):
    """Full output for a single budget including all computed fields + embedded categories."""

    id: str
    createdAt: str
    updatedAt: str
    name: str
    month: str
    currency: str = "BDT"
    totalBudgetAmount: int

    # ── Computed fields (NOT stored in DB) ──
    allocatedAmount: int = 0
    availableBalance: int = 0
    remainingBalance: int = 0
    isOverBudget: bool = False
    overAmount: int = 0
    forecastedSpend: int = 0
    forecastGap: int = 0
    dailySafeSpend: int = 0
    requiredDailyReduction: int = 0
    requiredExtraIncome: int = 0

    categories: List[BudgetCategoryOut] = []


class BudgetCreate(Schema):
    """Payload for creating a budget with optional inline categories."""

    name: str
    month: str
    currency: str = "BDT"
    totalBudgetAmount: int = 0
    categories: List[BudgetCategoryCreate] = []


class BudgetUpdate(Schema):
    """Payload for patching a budget (all optional)."""

    name: Optional[str] = None
    totalBudgetAmount: Optional[int] = None
    currency: Optional[str] = None
    categories: Optional[List[BudgetCategoryCreate]] = None


# ==================== Shared ====================


class MessageOut(Schema):
    message: str
