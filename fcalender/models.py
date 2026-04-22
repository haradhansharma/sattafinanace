"""
Calendar event tracking for FinLife Personal Finance SaaS.

CalendarEvent — financial events (EMI due, dividend dates, tax deadlines, etc.)
Inherits TenantMixin for automatic owner scoping.
"""

import uuid

from django.db import models

from common.models import TenantMixin


class CalendarEvent(TenantMixin):
    """Financial calendar event with recurrence, reminders, and cross-entity linking."""

    # --- Choices ---
    CATEGORY_CHOICES = [
        ("emi_payment", "EMI Payment"),
        ("insurance_premium", "Insurance Premium"),
        ("bill_payment", "Bill Payment"),
        ("investment_maturity", "Investment Maturity"),
        ("investment_deposit", "Investment Deposit"),
        ("dividend", "Dividend"),
        ("tax_deadline", "Tax Deadline"),
        ("salary", "Salary"),
        ("rental_income", "Rental Income"),
        ("rental_payment", "Rental Payment"),
        ("lending_payment", "Lending Payment"),
        ("subscription", "Subscription"),
        ("maintenance", "Maintenance"),
        ("document_renewal", "Document Renewal"),
        ("milestone", "Milestone"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("completed", "Completed"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]
    RECURRENCE_CHOICES = [
        ("none", "None"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("biweekly", "Biweekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("semiannually", "Semiannually"),
        ("annually", "Annually"),
        ("custom", "Custom"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]
    LINKED_ENTITY_TYPE_CHOICES = [
        ("loan", "Loan"),
        ("mortgage", "Mortgage"),
        ("insurance", "Insurance"),
        ("investment", "Investment"),
        ("lending", "Lending"),
        ("invoice", "Invoice"),
        ("document", "Document"),
        ("card", "Card"),
        ("bill", "Bill"),
        ("other", "Other"),
    ]

    # --- Core ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")

    # --- Financial ---
    amount = models.BigIntegerField(null=True, blank=True)
    currency = models.CharField(max_length=10, blank=True, default="BDT")

    # --- Dates ---
    event_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    # --- Recurrence ---
    recurrence = models.CharField(
        max_length=20, choices=RECURRENCE_CHOICES, default="none"
    )
    custom_recurrence_days = models.IntegerField(null=True, blank=True)
    recurrence_day_of_month = models.IntegerField(null=True, blank=True)
    next_occurrence_date = models.DateField(null=True, blank=True)

    # --- Reminders ---
    reminder_days_before = models.IntegerField(default=0)
    reminder_enabled = models.BooleanField(default=True)
    second_reminder_days_before = models.IntegerField(null=True, blank=True)

    # --- Display ---
    color = models.CharField(max_length=7, blank=True, default="")

    # --- Linking ---
    linked_entity_id = models.UUIDField(null=True, blank=True)
    linked_entity_type = models.CharField(
        max_length=50, choices=LINKED_ENTITY_TYPE_CHOICES, null=True, blank=True
    )
    linked_bill_id = models.UUIDField(null=True, blank=True)

    # --- Priority & Metadata ---
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    notes = models.TextField(blank=True, default="")
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["event_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.title} — {self.event_date}"
