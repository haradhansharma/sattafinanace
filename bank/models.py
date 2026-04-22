"""
Bank Account and Transaction models for FinLife.

All models inherit from TenantMixin to enforce tenant isolation.
TenantMixin adds `owner = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE)`.
"""

import uuid

from django.db import models

from common.models import TenantMixin


# ──────────────────────────────────────────────────────────────────────────────
# Choice constants — must match frontend TypeScript union types EXACTLY
# ──────────────────────────────────────────────────────────────────────────────

CURRENCY_CHOICES = [
    ("BDT", "Bangladeshi Taka"),
    ("USD", "US Dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound"),
    ("INR", "Indian Rupee"),
    ("SGD", "Singapore Dollar"),
    ("SAR", "Saudi Riyal"),
]

ACCOUNT_TYPE_CHOICES = [
    ("savings", "Savings"),
    ("checking", "Checking"),
    ("current", "Current"),
    ("fixed_deposit", "Fixed Deposit"),
    ("salary", "Salary"),
]

TRANSACTION_TYPE_CHOICES = [
    ("income", "Income"),
    ("expense", "Expense"),
    ("transfer", "Transfer"),
]

DIRECTION_CHOICES = [
    ("credit", "Credit"),
    ("debit", "Debit"),
]


# ──────────────────────────────────────────────────────────────────────────────
# BankAccount
# Frontend: id, bankName, accountNumber, accountName, type, openingBalance,
#           icon?, color?, currency?, isActive, createdAt, updatedAt
# ──────────────────────────────────────────────────────────────────────────────


class BankAccount(TenantMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=100)
    account_name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    opening_balance = models.BigIntegerField(default=0)
    icon = models.CharField(max_length=100, blank=True, default="")
    color = models.CharField(max_length=20, blank=True, default="")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="BDT")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bank_accounts"
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.bank_name} — {self.account_name} ({self.account_number})"

    @property
    def masked_account_number(self) -> str:
        """Return last 4 digits of account number masked."""
        if len(self.account_number) >= 4:
            return f"****{self.account_number[-4:]}"
        return self.account_number

    @property
    def current_balance(self) -> int:
        """Compute current balance: opening + credits - debits."""
        credits = (
            self.transactions.filter(direction="credit").aggregate(
                total=models.Sum("amount")
            )["total"]
            or 0
        )
        debits = (
            self.transactions.filter(direction="debit").aggregate(
                total=models.Sum("amount")
            )["total"]
            or 0
        )
        return self.opening_balance + credits - debits


# ──────────────────────────────────────────────────────────────────────────────
# Transaction
# Frontend: id, type, amount, direction, bankAccountId, toBankAccountId?,
#           categoryId, date, description, referenceId?, tags?, currency?,
#           createdAt, updatedAt
# ──────────────────────────────────────────────────────────────────────────────


class Transaction(TenantMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    to_bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_transfers",
    )

    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.BigIntegerField(default=0)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    category_id = models.UUIDField()
    date = models.DateField()
    description = models.TextField(blank=True, default="")
    reference_id = models.CharField(max_length=100, blank=True, default="")
    tags = models.JSONField(default=list, blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="BDT")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transactions"
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ("-date", "-created_at")

    def __str__(self) -> str:
        return f"{self.get_type_display()} — {self.amount} ({self.date})"
