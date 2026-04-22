"""
Calendar API — Django Ninja endpoints.

All endpoints are authenticated via BearerAuth and scoped to request.user.
List endpoints use paginate_queryset for standard pagination.
"""

import uuid

from django.http import HttpRequest
from ninja import Router

from common.permissions import BearerAuth
from common.pagination import paginate_queryset, PaginatedResponse

from .models import CalendarEvent
from .schemas import (
    CalendarEventOut,
    CalendarEventCreate,
    CalendarEventUpdate,
    MessageOut,
    to_snake_case,
    _parse_date,
)

router = Router(auth=BearerAuth())

_DATE_FIELDS = ("event_date", "end_date", "due_date", "next_occurrence_date")


def _apply_event_attrs(event: CalendarEvent, data: dict) -> None:
    """Apply a snake_case data dict to a CalendarEvent, parsing dates."""
    for field in _DATE_FIELDS:
        val = data.get(field)
        if val is not None:
            data[field] = _parse_date(val)
    for key, value in data.items():
        setattr(event, key, value)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get(
    "/", response=PaginatedResponse[CalendarEventOut], summary="List calendar events"
)
async def list_events(
    request: HttpRequest,
    page: int = 1,
    per_page: int = 20,
    year: int = None,
    month: int = None,
    category: str = None,
    status: str = None,
):
    qs = CalendarEvent.objects.filter(owner=request.user)
    if year and month:
        qs = qs.filter(event_date__year=year, event_date__month=month)
    elif year:
        qs = qs.filter(event_date__year=year)
    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)

    items, total, total_pages = paginate_queryset(qs, page, per_page)
    results = [CalendarEventOut.from_model(e) for e in items]
    return {
        "items": results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.get(
    "/month/{year}/{month}",
    response=list[CalendarEventOut],
    summary="List events by year and month",
)
async def list_events_by_month(request: HttpRequest, year: int, month: int):
    qs = CalendarEvent.objects.filter(
        owner=request.user,
        event_date__year=year,
        event_date__month=month,
    )
    return [CalendarEventOut.from_model(e) for e in qs]


@router.get(
    "/date/{event_date}", response=list[CalendarEventOut], summary="List events by date"
)
async def list_events_by_date(request: HttpRequest, event_date: str):
    d = _parse_date(event_date)
    qs = CalendarEvent.objects.filter(owner=request.user, event_date=d)
    return [CalendarEventOut.from_model(e) for e in qs]


@router.post("/", response={201: CalendarEventOut}, summary="Create a calendar event")
async def create_event(request: HttpRequest, payload: CalendarEventCreate):
    data = to_snake_case(payload.model_dump())
    for field in _DATE_FIELDS:
        if data.get(field):
            data[field] = _parse_date(data[field])
    if data.get("tags") is None:
        data["tags"] = []
    if data.get("description") is None:
        data["description"] = ""
    data["status"] = data.get("status", "upcoming")
    event = CalendarEvent(owner=request.user, **data)
    event.full_clean()
    event.save()
    event.refresh_from_db()
    return CalendarEventOut.from_model(event)


@router.get("/{event_id}", response=CalendarEventOut, summary="Get event by ID")
async def get_event(request: HttpRequest, event_id: uuid.UUID):
    event = CalendarEvent.objects.get(id=event_id, owner=request.user)
    return CalendarEventOut.from_model(event)


@router.put("/{event_id}", response=CalendarEventOut, summary="Update a calendar event")
async def update_event(
    request: HttpRequest, event_id: uuid.UUID, payload: CalendarEventUpdate
):
    event = CalendarEvent.objects.get(id=event_id, owner=request.user)
    data = to_snake_case(payload.model_dump(exclude_unset=True))
    _apply_event_attrs(event, data)
    event.full_clean()
    event.save()
    event.refresh_from_db()
    return CalendarEventOut.from_model(event)


@router.delete("/{event_id}", response=MessageOut, summary="Delete a calendar event")
async def delete_event(request: HttpRequest, event_id: uuid.UUID):
    event = CalendarEvent.objects.get(id=event_id, owner=request.user)
    event_id_str = str(event.id)
    event.delete()
    return MessageOut(message=f"Calendar event {event_id_str} deleted successfully")


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------


@router.post(
    "/{event_id}/complete", response=CalendarEventOut, summary="Mark event as completed"
)
async def complete_event(request: HttpRequest, event_id: uuid.UUID):
    event = CalendarEvent.objects.get(id=event_id, owner=request.user)
    event.status = "completed"
    event.save()
    event.refresh_from_db()
    return CalendarEventOut.from_model(event)


@router.post(
    "/{event_id}/cancel", response=CalendarEventOut, summary="Cancel a calendar event"
)
async def cancel_event(request: HttpRequest, event_id: uuid.UUID):
    event = CalendarEvent.objects.get(id=event_id, owner=request.user)
    event.status = "cancelled"
    event.save()
    event.refresh_from_db()
    return CalendarEventOut.from_model(event)
