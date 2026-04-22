"""
Savings Goal API endpoints for FinLife Personal Finance SaaS.

All endpoints require BearerAuth (JWT) and filter by request.user.
List endpoints use paginate_queryset from common.pagination.
"""

import uuid
from datetime import date
from typing import Optional

from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from ninja import Router

from common.pagination import PaginatedResponse, PaginationSchema, paginate_queryset
from common.permissions import BearerAuth

from .models import SavingsGoal, SavingsGoalContribution, SavingsGoalMilestone
from .schemas import (
    MessageOut,
    SavingsGoalContributionCreate,
    SavingsGoalContributionOut,
    SavingsGoalCreate,
    SavingsGoalMilestoneCreate,
    SavingsGoalMilestoneOut,
    SavingsGoalMilestoneUpdate,
    SavingsGoalOut,
    SavingsGoalUpdate,
    WithdrawAmountSchema,
)

router = Router(tags=["Savings Goal"])


# ==================== Field Mapping ====================
# camelCase schema key → snake_case model field

GOAL_FIELDS = {
    "name": "name",
    "description": "description",
    "category": "category",
    "status": "status",
    "targetAmount": "target_amount",
    "currentAmount": "current_amount",
    "currency": "currency",
    "startDate": "start_date",
    "targetDate": "target_date",
    "monthlyContributionAmount": "monthly_contribution_amount",
    "autoContributeEnabled": "auto_contribute_enabled",
    "autoContributeDayOfMonth": "auto_contribute_day_of_month",
    "motivationalQuote": "motivational_quote",
    "coverColor": "cover_color",
    "coverIcon": "cover_icon",
    "priority": "priority",
    "bankAccountId": "bank_account_id",
    "notes": "notes",
    "tags": "tags",
}


# ==================== Helpers ====================


def _check_and_update_milestones(goal: SavingsGoal):
    """Auto-achieve milestones when current_amount hits their percent threshold."""
    if goal.target_amount <= 0:
        return
    milestones = goal.milestones.filter(achieved=False)
    today = date.today()
    for ms in milestones:
        threshold = goal.target_amount * ms.percent / 100
        if goal.current_amount >= threshold:
            ms.achieved = True
            ms.achieved_date = today
            ms.save(update_fields=["achieved", "achieved_date", "updated_at"])


# ==================== SavingsGoal CRUD ====================


@router.get("/", auth=BearerAuth(), response=PaginatedResponse[SavingsGoalOut])
async def list_savings_goals(
    request,
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    pagination: PaginationSchema = PaginationSchema(),
):
    """List all savings goals for the authenticated user (paginated, filterable)."""
    qs = SavingsGoal.objects.filter(owner=request.user)
    if status:
        qs = qs.filter(status=status)
    if category:
        qs = qs.filter(category=category)
    if priority:
        qs = qs.filter(priority=priority)

    qs = qs.prefetch_related("contributions", "milestones")

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


@router.post("/", auth=BearerAuth(), response={201: SavingsGoalOut})
async def create_savings_goal(request, data: SavingsGoalCreate):
    """Create a new savings goal."""
    payload = data.model_dump()
    milestones_data = payload.pop("milestones", None) or []

    # Map camelCase → snake_case
    create_fields = {}
    for schema_key, model_field in GOAL_FIELDS.items():
        if schema_key in payload and payload[schema_key] is not None:
            create_fields[model_field] = payload[schema_key]

    if "tags" not in create_fields:
        create_fields["tags"] = []

    with db_transaction.atomic():
        goal = SavingsGoal.objects.create(owner=request.user, **create_fields)

        # Create milestones
        for ms_data in milestones_data:
            SavingsGoalMilestone.objects.create(
                owner=request.user,
                goal=goal,
                percent=ms_data.get("percent", 0),
                label=ms_data.get("label", ""),
                achieved=ms_data.get("achieved", False),
                achieved_date=ms_data.get("achievedDate"),
            )

    return 201, goal


@router.get("/{goal_id}/", auth=BearerAuth(), response=SavingsGoalOut)
async def get_savings_goal(request, goal_id: uuid.UUID):
    """Get a single savings goal by ID with embedded contributions and milestones."""
    goal = get_object_or_404(
        SavingsGoal.objects.prefetch_related("contributions", "milestones"),
        id=goal_id,
        owner=request.user,
    )
    return goal


@router.put("/{goal_id}/", auth=BearerAuth(), response=SavingsGoalOut)
async def update_savings_goal(request, goal_id: uuid.UUID, data: SavingsGoalUpdate):
    """Update a savings goal."""
    goal = get_object_or_404(SavingsGoal, id=goal_id, owner=request.user)
    payload = data.model_dump(exclude_unset=True)

    for schema_key, model_field in GOAL_FIELDS.items():
        if schema_key in payload:
            setattr(goal, model_field, payload[schema_key])

    goal.save()
    return goal


@router.delete("/{goal_id}/", auth=BearerAuth(), response=MessageOut)
async def delete_savings_goal(request, goal_id: uuid.UUID):
    """Delete a savings goal and all its contributions and milestones."""
    goal = get_object_or_404(SavingsGoal, id=goal_id, owner=request.user)
    goal.delete()
    return {"message": "Savings goal deleted successfully"}


# ==================== Contribution ====================


@router.post(
    "/{goal_id}/contribute/", auth=BearerAuth(), response=SavingsGoalContributionOut
)
async def contribute_to_goal(
    request, goal_id: uuid.UUID, data: SavingsGoalContributionCreate
):
    """Record a contribution to a savings goal and update totals."""
    with db_transaction.atomic():
        goal = get_object_or_404(SavingsGoal, id=goal_id, owner=request.user)

        contribution = SavingsGoalContribution.objects.create(
            owner=request.user,
            goal=goal,
            amount=data.amount,
            date=data.date,
            note=data.note or "",
            bank_account_id=data.bankAccountId or "",
        )

        # Update goal aggregates
        goal.current_amount += data.amount
        goal.total_contributed += data.amount
        goal.contribution_count += 1
        goal.current_streak += 1
        if goal.current_streak > goal.longest_streak:
            goal.longest_streak = goal.current_streak

        # Auto-complete if target reached
        if goal.current_amount >= goal.target_amount and goal.target_amount > 0:
            goal.status = "completed"
            goal.completed_date = date.today()

        _check_and_update_milestones(goal)
        goal.save()
        goal.refresh_from_db()
    return contribution


@router.get(
    "/{goal_id}/contributions/",
    auth=BearerAuth(),
    response=PaginatedResponse[SavingsGoalContributionOut],
)
async def list_goal_contributions(
    request,
    goal_id: uuid.UUID,
    pagination: PaginationSchema = PaginationSchema(),
):
    """List all contributions for a specific savings goal."""
    get_object_or_404(SavingsGoal, id=goal_id, owner=request.user)

    qs = SavingsGoalContribution.objects.filter(
        owner=request.user, goal_id=goal_id
    ).order_by("-date", "-created_at")

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


# ==================== Withdraw ====================


@router.post("/{goal_id}/withdraw/", auth=BearerAuth(), response=SavingsGoalOut)
async def withdraw_from_goal(request, goal_id: uuid.UUID, data: WithdrawAmountSchema):
    """Withdraw an amount from a savings goal."""
    with db_transaction.atomic():
        goal = get_object_or_404(SavingsGoal, id=goal_id, owner=request.user)

        if data.amount > goal.current_amount:
            from ninja.errors import HttpError

            raise HttpError(400, "Withdrawal amount exceeds current savings")

        goal.current_amount -= data.amount
        goal.total_withdrawn += data.amount

        # Revert completed status if we dip below target
        if goal.status == "completed" and goal.current_amount < goal.target_amount:
            goal.status = "active"
            goal.completed_date = None

        goal.save()
        goal.refresh_from_db()
    return goal


# ==================== Pause / Resume ====================


@router.post("/{goal_id}/pause/", auth=BearerAuth(), response=SavingsGoalOut)
async def pause_goal(request, goal_id: uuid.UUID):
    """Pause a savings goal and reset current streak."""
    goal = get_object_or_404(SavingsGoal, id=goal_id, owner=request.user)
    goal.status = "paused"
    goal.current_streak = 0
    goal.save()
    goal.refresh_from_db()
    return goal


@router.post("/{goal_id}/resume/", auth=BearerAuth(), response=SavingsGoalOut)
async def resume_goal(request, goal_id: uuid.UUID):
    """Resume a paused savings goal."""
    goal = get_object_or_404(SavingsGoal, id=goal_id, owner=request.user)
    goal.status = "active"
    goal.save()
    goal.refresh_from_db()
    return goal


# ==================== Milestone CRUD ====================


@router.post(
    "/{goal_id}/milestones/", auth=BearerAuth(), response={201: SavingsGoalMilestoneOut}
)
async def create_goal_milestone(
    request, goal_id: uuid.UUID, data: SavingsGoalMilestoneCreate
):
    """Create a milestone for a savings goal."""
    goal = get_object_or_404(SavingsGoal, id=goal_id, owner=request.user)
    milestone = SavingsGoalMilestone.objects.create(
        owner=request.user,
        goal=goal,
        percent=data.percent,
        label=data.label,
        achieved=data.achieved,
        achieved_date=data.achievedDate,
    )
    return 201, milestone


@router.put(
    "/{goal_id}/milestones/{milestone_id}/",
    auth=BearerAuth(),
    response=SavingsGoalMilestoneOut,
)
async def update_goal_milestone(
    request,
    goal_id: uuid.UUID,
    milestone_id: uuid.UUID,
    data: SavingsGoalMilestoneUpdate,
):
    """Update a milestone."""
    milestone = get_object_or_404(
        SavingsGoalMilestone, id=milestone_id, goal_id=goal_id, owner=request.user
    )
    payload = data.model_dump(exclude_unset=True)

    if "percent" in payload:
        milestone.percent = payload["percent"]
    if "label" in payload:
        milestone.label = payload["label"]
    if "achieved" in payload:
        milestone.achieved = payload["achieved"]
    if "achievedDate" in payload:
        milestone.achieved_date = payload["achievedDate"]

    milestone.save()
    milestone.refresh_from_db()
    return milestone


@router.delete(
    "/{goal_id}/milestones/{milestone_id}/", auth=BearerAuth(), response=MessageOut
)
async def delete_goal_milestone(request, goal_id: uuid.UUID, milestone_id: uuid.UUID):
    """Delete a milestone."""
    milestone = get_object_or_404(
        SavingsGoalMilestone, id=milestone_id, goal_id=goal_id, owner=request.user
    )
    milestone.delete()
    return {"message": "Milestone deleted successfully"}
