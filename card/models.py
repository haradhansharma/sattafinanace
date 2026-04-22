"""
Card app models for FinLife Personal Finance SaaS.

All models inherit from TenantMixin which adds an `owner` FK,
ensuring every record is scoped to the authenticated user.
"""

import uuid

from django.db import models

from common.models import TenantMixin


class Card(TenantMixin):
    """
    Card (debit or credit) linked to a bank account.
    Frontend fields: id, createdAt, updatedAt, bankAccountId (FK→BankAccount),
                     name, type ('debit'|'credit'), cardNumber, holderName,
                     expiryDate, brand ('visa'|'mastercard'|'amex'|'discover'),
                     creditLimit?, currentBalance,
                     billingCycle ({start, end}), dueDate, isActive,
                     color?, currency?, secondaryCurrency?,
                     secondaryCreditLimit?, secondaryCurrentBalance?
    """

    CARD_TYPE_CHOICES = [
        ("debit", "Debit"),
        ("credit", "Credit"),
    ]
    BRAND_CHOICES = [
        ("visa", "Visa"),
        ("mastercard", "Mastercard"),
        ("amex", "Amex"),
        ("discover", "Discover"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bank_account_id = models.UUIDField()  # FK→BankAccount stored as UUID
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=CARD_TYPE_CHOICES)
    card_number = models.CharField(max_length=4)  # Last 4 digits only
    holder_name = models.CharField(max_length=255)
    expiry_date = models.CharField(max_length=7)  # "MM/YYYY"
    brand = models.CharField(max_length=20, choices=BRAND_CHOICES)
    credit_limit = models.BigIntegerField(null=True, blank=True)
    current_balance = models.BigIntegerField(default=0)
    billing_cycle = models.JSONField(default=dict)  # {"start": int, "end": int}
    due_date = models.IntegerField(default=1)  # Day of month
    is_active = models.BooleanField(default=True)
    color = models.CharField(max_length=7, null=True, blank=True)
    currency = models.CharField(max_length=10, default="BDT")
    secondary_currency = models.CharField(max_length=10, null=True, blank=True)
    secondary_credit_limit = models.BigIntegerField(null=True, blank=True)
    secondary_current_balance = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Card"
        verbose_name_plural = "Cards"

    def __str__(self):
        return f"{self.name} (****{self.card_number})"
