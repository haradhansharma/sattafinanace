import uuid

from django.db import models

from common.models import TenantMixin


class Investment(TenantMixin):
    """
    Investment model matching frontend Investment type.
    Tracks FDR, DPS, Sanchaypatra, Stock, Mutual Fund, Gold, Bond, and other investments.
    """

    CATEGORY_CHOICES = [
        ("fdr", "FDR"),
        ("dps", "DPS"),
        ("sanchaypatra", "Sanchaypatra"),
        ("stock", "Stock"),
        ("mutual_fund", "Mutual Fund"),
        ("gold", "Gold"),
        ("bond", "Bond"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("matured", "Matured"),
        ("sold", "Sold"),
        ("redeemed", "Redeemed"),
        ("closed", "Closed"),
    ]

    COMPOUNDING_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("annually", "Annually"),
        ("at_maturity", "At Maturity"),
    ]

    STOCK_EXCHANGE_CHOICES = [
        ("DSE", "DSE"),
        ("CSE", "CSE"),
        ("NASDAQ", "NASDAQ"),
        ("NYSE", "NYSE"),
        ("other", "Other"),
    ]

    PURITY_CHOICES = [
        ("18k", "18K"),
        ("21k", "21K"),
        ("22k", "22K"),
        ("24k", "24K"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    institution = models.CharField(max_length=255)
    account_number = models.CharField(max_length=255, blank=True, default="")
    purchase_date = models.DateField()
    maturity_date = models.DateField(blank=True, null=True)

    # Core financials
    invested_amount = models.BigIntegerField(default=0)
    current_value = models.BigIntegerField(default=0)
    total_returns = models.BigIntegerField(default=0)

    # Stock / mutual fund / unit-based fields
    quantity = models.DecimalField(
        max_digits=15, decimal_places=4, blank=True, null=True
    )
    avg_buy_price = models.BigIntegerField(default=0)
    current_unit_price = models.BigIntegerField(default=0)

    # FDR / DPS / Sanchaypatra fields
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    compounding = models.CharField(
        max_length=20, choices=COMPOUNDING_CHOICES, blank=True, default=""
    )
    tax_on_interest = models.BooleanField(default=False)
    monthly_deposit_amount = models.BigIntegerField(default=0)
    total_deposited_so_far = models.BigIntegerField(default=0)
    deposit_count = models.IntegerField(default=0)

    # Stock-specific fields
    stock_symbol = models.CharField(max_length=50, blank=True, default="")
    stock_exchange = models.CharField(
        max_length=10, choices=STOCK_EXCHANGE_CHOICES, blank=True, default=""
    )
    dividend_yield = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )

    # Gold-specific fields
    purity = models.CharField(
        max_length=5, choices=PURITY_CHOICES, blank=True, default=""
    )
    weight_grams = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )

    # Status and flags
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    auto_renew = models.BooleanField(default=False)

    # References and metadata
    bank_account_id = models.UUIDField(blank=True, null=True)
    currency = models.CharField(max_length=10, default="BDT")
    notes = models.TextField(blank=True, default="")
    tags = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "investments"
        verbose_name = "Investment"
        verbose_name_plural = "Investments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.category})"


class InvestmentTransaction(TenantMixin):
    """
    Investment transaction model — buy, sell, dividend, interest, deposit, etc.
    FK → Investment, scoped to owner via TenantMixin.
    """

    TYPE_CHOICES = [
        ("buy", "Buy"),
        ("sell", "Sell"),
        ("dividend", "Dividend"),
        ("interest", "Interest"),
        ("deposit", "Deposit"),
        ("withdrawal", "Withdrawal"),
        ("bonus", "Bonus"),
        ("maturity", "Maturity"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    investment = models.ForeignKey(
        Investment,
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.BigIntegerField(default=0)
    units = models.DecimalField(max_digits=15, decimal_places=4, blank=True, null=True)
    unit_price = models.BigIntegerField(default=0)
    date = models.DateField()
    note = models.TextField(blank=True, default="")
    bank_account_id = models.UUIDField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "investment_transactions"
        verbose_name = "Investment Transaction"
        verbose_name_plural = "Investment Transactions"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.type} - {self.amount} ({self.investment.name})"
