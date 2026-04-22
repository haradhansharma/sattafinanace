"""
Pagination utilities for Django Ninja API responses.
Provides a standard paginated response format matching frontend expectations.
"""

from typing import TypeVar, Generic, List

from ninja import Schema

T = TypeVar("T")


class PaginationSchema(Schema):
    """Query parameters for pagination."""

    page: int = 1
    per_page: int = 20


class PaginatedResponse(Schema, Generic[T]):
    """
    Standard paginated response wrapper.
    Usage: PaginatedResponse[SomeSchema]
    """

    items: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int


def paginate_queryset(queryset, page: int, per_page: int):
    """
    Paginate a Django queryset and return (items, total, total_pages).
    """
    total = queryset.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    items = queryset[start:end]
    return items, total, total_pages
