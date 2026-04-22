"""
Savings Goal schemas for FinLife Personal Finance SaaS.

All schemas use camelCase field names matching the frontend TypeScript interfaces.
"""

from datetime import date
from typing import List, Optional

from ninja import Schema


# ==================== Message ====================


class MessageOut(Schema):
    """Generic message response."""

    message: str


# ==================== Milestone Schemas ====================


class SavingsGoalMilestoneOut(Schema):
    """Milestone output matching frontend SavingsGoalMilestone interface."""

    id: str
    percent: int
    label: str
    achieved: bool
    achievedDate: Optional[str] = None

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_achievedDate(obj):
        return obj.achieved_date.isoformat() if obj.achieved_date else None


class SavingsGoalMilestoneCreate(Schema):
    """Create a milestone."""

    percent: int = 0
    label: str = ""
    achieved: bool = False
    achievedDate: Optional[date] = None


class SavingsGoalMilestoneUpdate(Schema):
    """Update a milestone — all fields optional."""

    percent: Optional[int] = None
    label: Optional[str] = None
    achieved: Optional[bool] = None
    achievedDate: Optional[date] = None


# ==================== Contribution Schemas ====================


class SavingsGoalContributionOut(Schema):
    """Contribution output matching frontend SavingsGoalContribution interface."""

    id: str
    goalId: str
    amount: int
    date: str
    note: Optional[str] = None
    bankAccountId: Optional[str] = None
    createdAt: str
    updatedAt: str

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_goalId(obj):
        return str(obj.goal_id)

    @staticmethod
    def resolve_date(obj):
        return obj.date.isoformat() if obj.date else ""

    @staticmethod
    def resolve_createdAt(obj):
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj):
        return obj.updated_at.isoformat()


class SavingsGoalContributionCreate(Schema):
    """Create a contribution."""

    amount: int
    date: date
    note: Optional[str] = None
    bankAccountId: Optional[str] = None


# ==================== SavingsGoal Schemas ====================


class SavingsGoalOut(Schema):
    """Full savings goal output matching frontend SavingsGoal interface."""

    id: str
    name: str
    description: Optional[str] = None
    category: str
    status: str
    targetAmount: int
    currentAmount: int
    currency: str
    startDate: str
    targetDate: Optional[str] = None
    completedDate: Optional[str] = None
    monthlyContributionAmount: int
    autoContributeEnabled: bool
    autoContributeDayOfMonth: Optional[int] = None
    totalContributed: int
    totalWithdrawn: int
    contributionCount: int
    motivationalQuote: Optional[str] = None
    coverColor: Optional[str] = None
    coverIcon: Optional[str] = None
    currentStreak: int
    longestStreak: int
    priority: str
    bankAccountId: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []
    # Embedded related objects
    contributions: List[SavingsGoalContributionOut] = []
    milestones: List[SavingsGoalMilestoneOut] = []
    createdAt: str
    updatedAt: str

    @staticmethod
    def resolve_id(obj):
        return str(obj.id)

    @staticmethod
    def resolve_startDate(obj):
        return obj.start_date.isoformat() if obj.start_date else ""

    @staticmethod
    def resolve_targetDate(obj):
        return obj.target_date.isoformat() if obj.target_date else None

    @staticmethod
    def resolve_completedDate(obj):
        return obj.completed_date.isoformat() if obj.completed_date else None

    @staticmethod
    def resolve_contributions(obj):
        return list(obj.contributions.all())

    @staticmethod
    def resolve_milestones(obj):
        return list(obj.milestones.all())

    @staticmethod
    def resolve_createdAt(obj):
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updatedAt(obj):
        return obj.updated_at.isoformat()


class SavingsGoalCreate(Schema):
    """Create a savings goal."""

    name: str
    description: Optional[str] = None
    category: str = "other"
    status: str = "active"
    targetAmount: int
    currentAmount: int = 0
    currency: str = "BDT"
    startDate: date
    targetDate: Optional[date] = None
    monthlyContributionAmount: int = 0
    autoContributeEnabled: bool = False
    autoContributeDayOfMonth: Optional[int] = None
    motivationalQuote: Optional[str] = None
    coverColor: Optional[str] = None
    coverIcon: Optional[str] = None
    priority: str = "medium"
    bankAccountId: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    milestones: Optional[List[SavingsGoalMilestoneCreate]] = None


class SavingsGoalUpdate(Schema):
    """Update a savings goal — all fields optional."""

    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    targetAmount: Optional[int] = None
    currentAmount: Optional[int] = None
    currency: Optional[str] = None
    startDate: Optional[date] = None
    targetDate: Optional[date] = None
    monthlyContributionAmount: Optional[int] = None
    autoContributeEnabled: Optional[bool] = None
    autoContributeDayOfMonth: Optional[int] = None
    motivationalQuote: Optional[str] = None
    coverColor: Optional[str] = None
    coverIcon: Optional[str] = None
    priority: Optional[str] = None
    bankAccountId: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class WithdrawAmountSchema(Schema):
    """Schema for withdrawal amount."""

    amount: int
