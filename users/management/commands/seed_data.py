"""
Django management command to populate FinLife with realistic demo data.

Usage:
    python manage.py seed_data                  # Creates demo user + all data
    python manage.py seed_data --email=custom@example.com  # Custom email
    python manage.py seed_data --clear          # Clears existing data first
    python manage.py seed_data --skip-user      # Use existing user (must set --email)

Creates a single demo user with:
    - 3 bank accounts with transactions
    - 8 expense categories + 30+ expenses
    - 6 income categories + 12+ incomes
    - 3 income sources
    - 2 credit/debit cards
    - 2 loans with payments
    - 1 budget with categories
    - 4 investments (FDR, DPS, Stock, Gold)
    - 2 insurance policies (life + health)
    - 3 savings goals with contributions
    - 2 assets (real estate + vehicle)
    - 2 lending records
    - 3 invoices with items
    - 5 bills with payment history
    - 8 calendar events
    - 5 document vault items
"""

import calendar
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()


def _d(days_ago: int = 0) -> date:
    """Helper: date N days ago."""
    return date.today() - timedelta(days=days_ago)


def _rand_id() -> str:
    """Return a random UUID string for non-FK UUID references."""
    return str(uuid.uuid4())


class Command(BaseCommand):
    help = "Populate FinLife with realistic demo data for a single user."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            default="rahim@example.com",
            help="Demo user email (default: rahim@example.com)",
        )
        parser.add_argument(
            "--name",
            default="Abdur Rahim",
            help="Demo user name (default: Abdur Rahim)",
        )
        parser.add_argument(
            "--password",
            default="demo1234",
            help="Demo user password (default: demo1234)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing data for the user before seeding",
        )
        parser.add_argument(
            "--skip-user",
            action="store_true",
            help="Skip user creation (user must already exist)",
        )

    def handle(self, *args, **options):
        self.email = options["email"]
        self.name = options["name"]
        self.password = options["password"]
        self.clear = options["clear"]
        self.skip_user = options["skip_user"]
        self.v = options["verbosity"]

        self._ids = {}  # Store created object IDs for cross-references
        self.today = date.today()
        self.month_str = self.today.strftime("%Y-%m")

        # ---------- User ----------
        if self.skip_user:
            try:
                self.user = User.objects.get(email=self.email)
                self._log(f"Using existing user: {self.user.email}")
            except User.DoesNotExist:
                self._err(
                    f"User {self.email} not found. Create it first or remove --skip-user."
                )
                return
        else:
            if User.objects.filter(email=self.email).exists():
                User.objects.filter(email=self.email).delete()
            self.user = User.objects.create_user(
                email=self.email,
                password=self.password,
                name=self.name,
                currency="BDT",
            )
            self._ok(f"Created user: {self.user.email} / {self.password}")

        if self.clear:
            self._clear_user_data()

        self._log(f"Seeding data for: {self.user.name} ({self.user.email})")
        self._log(f"Month: {self.month_str}")
        self._log("")

        # ---------- Seed in dependency order ----------
        self._seed_bank_accounts()
        self._seed_expense_categories()
        self._seed_income_categories()
        self._seed_income_sources()
        self._seed_cards()
        self._seed_expenses()
        self._seed_incomes()
        self._seed_transactions()
        self._seed_budgets()
        self._seed_loans()
        self._seed_investments()
        self._seed_insurance()
        self._seed_savings_goals()
        self._seed_assets()
        self._seed_lending()
        self._seed_invoices()
        self._seed_bills()
        self._seed_calendar_events()
        self._seed_documents()

        self._log("")
        self._ok("=" * 50)
        self._ok("Seed data created successfully!")
        self._ok(f"Login: {self.email} / {self.password}")
        self._ok("=" * 50)

    # ====================================================================
    # HELPERS
    # ====================================================================

    def _log(self, msg):
        if self.v >= 1:
            self.stdout.write(msg)

    def _ok(self, msg):
        self.stdout.write(self.style.SUCCESS(msg))

    def _err(self, msg):
        self.stderr.write(self.style.ERROR(msg))

    def _clear_user_data(self):
        """Delete all tenant-scoped data for the user (reverse FK order)."""
        from bank.models import BankAccount, Transaction
        from income.models import Income, IncomeCategory, IncomeSource
        from expense.models import Expense, ExpenseCategory
        from card.models import Card
        from loan.models import Loan, LoanPayment
        from budget.models import Budget, BudgetCategory
        from investment.models import Investment, InvestmentTransaction
        from insurance.models import (
            Insurance,
            InsuranceBeneficiary,
            InsuranceClaim,
            InsurancePremiumPayment,
        )
        from savings_goal.models import (
            SavingsGoal,
            SavingsGoalContribution,
            SavingsGoalMilestone,
        )
        from asset.models import Asset, AssetValuation
        from lending.models import Lending, LendingPayment
        from invoice.models import Invoice, InvoiceItem
        from bill.models import Bill, BillPaymentHistory
        from fcalender.models import CalendarEvent
        from document.models import DocumentVaultItem, DocumentVersion

        # Delete in safe order (children first)
        counts = 0
        for qs in [
            DocumentVersion.objects.filter(owner=self.user),
            DocumentVaultItem.objects.filter(owner=self.user),
            CalendarEvent.objects.filter(owner=self.user),
            BillPaymentHistory.objects.filter(bill__owner=self.user),
            Bill.objects.filter(owner=self.user),
            InvoiceItem.objects.filter(invoice__owner=self.user),
            Invoice.objects.filter(owner=self.user),
            LendingPayment.objects.filter(owner=self.user),
            Lending.objects.filter(owner=self.user),
            AssetValuation.objects.filter(asset__owner=self.user),
            Asset.objects.filter(owner=self.user),
            SavingsGoalMilestone.objects.filter(owner=self.user),
            SavingsGoalContribution.objects.filter(owner=self.user),
            SavingsGoal.objects.filter(owner=self.user),
            InsuranceBeneficiary.objects.filter(owner=self.user),
            InsuranceClaim.objects.filter(owner=self.user),
            InsurancePremiumPayment.objects.filter(owner=self.user),
            Insurance.objects.filter(owner=self.user),
            InvestmentTransaction.objects.filter(owner=self.user),
            Investment.objects.filter(owner=self.user),
            BudgetCategory.objects.filter(owner=self.user),
            Budget.objects.filter(owner=self.user),
            LoanPayment.objects.filter(owner=self.user),
            Loan.objects.filter(owner=self.user),
            Card.objects.filter(owner=self.user),
            Transaction.objects.filter(owner=self.user),
            Expense.objects.filter(owner=self.user),
            ExpenseCategory.objects.filter(owner=self.user),
            Income.objects.filter(owner=self.user),
            IncomeCategory.objects.filter(owner=self.user),
            IncomeSource.objects.filter(owner=self.user),
            BankAccount.objects.filter(owner=self.user),
        ]:
            c = qs.delete()[0]
            counts += c

        self._ok(f"Cleared {counts} existing records for user.")

    # ====================================================================
    # BANK ACCOUNTS
    # ====================================================================

    def _seed_bank_accounts(self):
        from bank.models import BankAccount

        accounts = [
            {
                "bank_name": "Dutch-Bangla Bank",
                "account_number": "1234567890",
                "account_name": "Abdur Rahim - Savings",
                "type": "savings",
                "opening_balance": 150000,
                "icon": "🏦",
                "color": "#3B82F6",
                "currency": "BDT",
                "is_active": True,
            },
            {
                "bank_name": "City Bank",
                "account_number": "9876543210",
                "account_name": "Abdur Rahim - Salary",
                "type": "salary",
                "opening_balance": 85000,
                "icon": "💼",
                "color": "#10B981",
                "currency": "BDT",
                "is_active": True,
            },
            {
                "bank_name": "IBBL",
                "account_number": "5555666677",
                "account_name": "Abdur Rahim - FDR",
                "type": "fixed_deposit",
                "opening_balance": 500000,
                "icon": "🏛️",
                "color": "#8B5CF6",
                "currency": "BDT",
                "is_active": True,
            },
        ]

        self.bank_accounts = []
        for acc_data in accounts:
            acc = BankAccount.objects.create(owner=self.user, **acc_data)
            self.bank_accounts.append(acc)
            self._log(f"  Bank Account: {acc.account_name} ({acc.bank_name})")

        self._ids["bank_primary"] = str(self.bank_accounts[0].id)
        self._ids["bank_salary"] = str(self.bank_accounts[1].id)
        self._ids["bank_fdr"] = str(self.bank_accounts[2].id)
        self._ok(f"Created {len(self.bank_accounts)} bank accounts")

    # ====================================================================
    # EXPENSE CATEGORIES
    # ====================================================================

    def _seed_expense_categories(self):
        from expense.models import ExpenseCategory

        categories = [
            ("Groceries", "🛒", "#EF4444", "needs", 25000),
            ("Transport", "🚗", "#F59E0B", "needs", 10000),
            ("Dining Out", "🍕", "#EC4899", "wants", 8000),
            ("Shopping", "🛍️", "#8B5CF6", "wants", 12000),
            ("Rent", "🏠", "#3B82F6", "needs", 20000),
            ("Utilities", "💡", "#06B6D4", "needs", 5000),
            ("Entertainment", "🎬", "#F97316", "wants", 5000),
            ("Healthcare", "🏥", "#10B981", "needs", 8000),
        ]

        self.expense_categories = []
        for name, icon, color, etype, budget_limit in categories:
            cat = ExpenseCategory.objects.create(
                owner=self.user,
                name=name,
                icon=icon,
                color=color,
                type=etype,
                budget_limit=budget_limit,
            )
            self.expense_categories.append(cat)
            self._log(f"  Expense Category: {name}")

        self._ids["cat_groceries"] = str(self.expense_categories[0].id)
        self._ids["cat_transport"] = str(self.expense_categories[1].id)
        self._ids["cat_dining"] = str(self.expense_categories[2].id)
        self._ids["cat_shopping"] = str(self.expense_categories[3].id)
        self._ids["cat_rent"] = str(self.expense_categories[4].id)
        self._ids["cat_utilities"] = str(self.expense_categories[5].id)
        self._ids["cat_entertainment"] = str(self.expense_categories[6].id)
        self._ids["cat_healthcare"] = str(self.expense_categories[7].id)
        self._ok(f"Created {len(self.expense_categories)} expense categories")

    # ====================================================================
    # INCOME CATEGORIES
    # ====================================================================

    def _seed_income_categories(self):
        from income.models import IncomeCategory

        categories = [
            ("Salary", "💰", "#10B981", "salary"),
            ("Freelance", "💻", "#3B82F6", "freelance"),
            ("Business", "🏢", "#8B5CF6", "business"),
            ("Investment Return", "📈", "#F59E0B", "investment"),
            ("Rental Income", "🏠", "#EC4899", "rental"),
            ("Bonus", "🎁", "#F97316", "other"),
        ]

        self.income_categories = []
        for name, icon, color, itype in categories:
            cat = IncomeCategory.objects.create(
                owner=self.user,
                name=name,
                icon=icon,
                color=color,
                type=itype,
            )
            self.income_categories.append(cat)
            self._log(f"  Income Category: {name}")

        self._ids["cat_salary"] = str(self.income_categories[0].id)
        self._ids["cat_freelance"] = str(self.income_categories[1].id)
        self._ids["cat_investment_return"] = str(self.income_categories[3].id)
        self._ids["cat_rental"] = str(self.income_categories[4].id)
        self._ok(f"Created {len(self.income_categories)} income categories")

    # ====================================================================
    # INCOME SOURCES
    # ====================================================================

    def _seed_income_sources(self):
        from income.models import IncomeSource

        sources = [
            ("TechCorp BD", "salary", True, 120000),
            ("Upwork Freelance", "freelance", True, 45000),
            ("Shop Rent - Gulshan", "rental", True, 30000),
        ]

        self.income_sources = []
        for name, stype, is_active, monthly in sources:
            src = IncomeSource.objects.create(
                owner=self.user,
                name=name,
                type=stype,
                is_active=is_active,
                monthly_amount=monthly,
            )
            self.income_sources.append(src)
            self._log(f"  Income Source: {name} ({monthly:,} BDT/mo)")

        self._ok(f"Created {len(self.income_sources)} income sources")

    # ====================================================================
    # CARDS
    # ====================================================================

    def _seed_cards(self):
        from card.models import Card

        cards = [
            {
                "bank_account_id": self._ids["bank_primary"],
                "name": "DBBL Visa Platinum",
                "type": "credit",
                "card_number": "4532",
                "holder_name": "Abdur Rahim",
                "expiry_date": "12/2027",
                "brand": "visa",
                "credit_limit": 200000,
                "current_balance": 35000,
                "billing_cycle": {"start": 5, "end": 4},
                "due_date": 15,
                "color": "#3B82F6",
                "currency": "BDT",
            },
            {
                "bank_account_id": self._ids["bank_salary"],
                "name": "City Bank Debit",
                "type": "debit",
                "card_number": "8901",
                "holder_name": "Abdur Rahim",
                "expiry_date": "08/2026",
                "brand": "mastercard",
                "credit_limit": None,
                "current_balance": 0,
                "billing_cycle": {},
                "due_date": 1,
                "color": "#10B981",
                "currency": "BDT",
            },
        ]

        self.cards = []
        for c_data in cards:
            card = Card.objects.create(owner=self.user, **c_data)
            self.cards.append(card)
            self._log(f"  Card: {card.name} (****{card.card_number})")

        self._ids["card_visa"] = str(self.cards[0].id)
        self._ids["card_debit"] = str(self.cards[1].id)
        self._ok(f"Created {len(self.cards)} cards")

    # ====================================================================
    # EXPENSES
    # ====================================================================

    def _seed_expenses(self):
        from expense.models import Expense

        expenses_data = [
            # Groceries (cat 0)
            (
                "Chaldal Weekly Groceries",
                4500,
                1,
                self._ids["cat_groceries"],
                False,
                None,
                ["groceries"],
            ),
            (
                "Navana Supermarket",
                3200,
                3,
                self._ids["cat_groceries"],
                False,
                None,
                ["groceries"],
            ),
            (
                "Agora Fresh Vegetables",
                1800,
                5,
                self._ids["cat_groceries"],
                False,
                None,
                [],
            ),
            (
                "Unimart Monthly Stock",
                6200,
                8,
                self._ids["cat_groceries"],
                False,
                None,
                ["monthly"],
            ),
            (
                "Meat & Fish - Karwan Bazar",
                3500,
                10,
                self._ids["cat_groceries"],
                False,
                None,
                [],
            ),
            (
                "Chaldal Groceries",
                4100,
                14,
                self._ids["cat_groceries"],
                False,
                None,
                [],
            ),
            (
                "Swiss Bakery",
                900,
                16,
                self._ids["cat_groceries"],
                False,
                None,
                ["bakery"],
            ),
            # Transport (cat 1)
            (
                "Uber Rides - Week",
                2500,
                2,
                self._ids["cat_transport"],
                True,
                "weekly",
                ["uber"],
            ),
            (
                "Pathao Bike Rides",
                1200,
                4,
                self._ids["cat_transport"],
                True,
                "weekly",
                ["pathao"],
            ),
            ("CNG Auto Rickshaw", 800, 7, self._ids["cat_transport"], False, None, []),
            (
                "Fuel - Motorcycle",
                1500,
                11,
                self._ids["cat_transport"],
                True,
                "monthly",
                ["fuel"],
            ),
            (
                "Uber - Airport Transfer",
                1200,
                15,
                self._ids["cat_transport"],
                False,
                None,
                ["uber"],
            ),
            # Dining Out (cat 2)
            (
                "Star Kabab Dinner",
                2800,
                2,
                self._ids["cat_dining"],
                False,
                None,
                ["dinner"],
            ),
            (
                "Pizza Hut - Family",
                3500,
                6,
                self._ids["cat_dining"],
                False,
                None,
                ["pizza"],
            ),
            (
                "Coffee & Snacks - North End",
                650,
                9,
                self._ids["cat_dining"],
                False,
                None,
                ["coffee"],
            ),
            (
                "Fakruddin Biriyani",
                1200,
                13,
                self._ids["cat_dining"],
                False,
                None,
                ["biriyani"],
            ),
            (
                "Gloria Jean's Coffee",
                450,
                17,
                self._ids["cat_dining"],
                False,
                None,
                ["coffee"],
            ),
            # Shopping (cat 3)
            (
                "Bashundhara City Clothes",
                8500,
                4,
                self._ids["cat_shopping"],
                False,
                None,
                ["clothes"],
            ),
            (
                "Daraz Online Order",
                3200,
                9,
                self._ids["cat_shopping"],
                False,
                None,
                ["electronics"],
            ),
            (
                "Muktupolon Book Store",
                1500,
                12,
                self._ids["cat_shopping"],
                False,
                None,
                ["books"],
            ),
            # Rent (cat 4)
            (
                "Monthly Rent - Gulshan Apt",
                20000,
                1,
                self._ids["cat_rent"],
                True,
                "monthly",
                ["rent"],
            ),
            # Utilities (cat 5)
            (
                "DESCO Electricity Bill",
                4500,
                5,
                self._ids["cat_utilities"],
                True,
                "monthly",
                ["electricity"],
            ),
            (
                "WASA Water Bill",
                1200,
                7,
                self._ids["cat_utilities"],
                True,
                "monthly",
                ["water"],
            ),
            (
                "Internet - Link3",
                1500,
                10,
                self._ids["cat_utilities"],
                True,
                "monthly",
                ["internet"],
            ),
            (
                "Gas Bill - Titas",
                1800,
                12,
                self._ids["cat_utilities"],
                True,
                "monthly",
                ["gas"],
            ),
            # Entertainment (cat 6)
            (
                "Netflix Subscription",
                800,
                1,
                self._ids["cat_entertainment"],
                True,
                "monthly",
                ["streaming"],
            ),
            (
                "Movie Tickets - Blockbuster",
                1500,
                8,
                self._ids["cat_entertainment"],
                False,
                None,
                ["movie"],
            ),
            (
                "Steam Games",
                2500,
                14,
                self._ids["cat_entertainment"],
                False,
                None,
                ["gaming"],
            ),
            # Healthcare (cat 7)
            (
                "Lab Tests - Ibn Sina",
                3500,
                6,
                self._ids["cat_healthcare"],
                False,
                None,
                ["medical"],
            ),
            (
                "Pharmacy - Medicine",
                1800,
                11,
                self._ids["cat_healthcare"],
                False,
                None,
                ["medicine"],
            ),
        ]

        self.expenses = []
        for desc, amount, day_ago, cat_id, is_recurring, cycle, tags in expenses_data:
            use_card = amount < 5000 and day_ago % 3 == 0
            exp = Expense.objects.create(
                owner=self.user,
                amount=amount,
                date=_d(day_ago),
                bank_account_id=self._ids["bank_primary"],
                card_id=self._ids["card_visa"] if use_card else None,
                category_id=cat_id,
                description=desc,
                is_recurring=is_recurring,
                recurring_cycle=cycle,
                tags=tags,
                currency="BDT",
            )
            self.expenses.append(exp)

        self._ok(f"Created {len(self.expenses)} expenses")

    # ====================================================================
    # INCOMES
    # ====================================================================

    def _seed_incomes(self):
        from income.models import Income

        incomes_data = [
            # Salary (source 0, cat 0) - past 3 months
            ("Monthly Salary - TechCorp BD", 120000, 15, 0, 0, True, "monthly"),
            ("Monthly Salary - TechCorp BD", 120000, 45, 0, 0, True, "monthly"),
            ("Monthly Salary - TechCorp BD", 120000, 75, 0, 0, True, "monthly"),
            # Freelance (source 1, cat 1)
            ("Upwork Project - Web App", 35000, 10, 1, 1, False, None),
            ("Upwork Project - Mobile App", 50000, 25, 1, 1, False, None),
            ("Upwork - Ongoing Support", 15000, 8, 1, 1, True, "monthly"),
            ("Upwork - Ongoing Support", 15000, 38, 1, 1, True, "monthly"),
            # Rental (source 2, cat 4)
            ("Shop Rent - Gulshan", 30000, 1, 2, 4, True, "monthly"),
            ("Shop Rent - Gulshan", 30000, 31, 2, 4, True, "monthly"),
            # Investment returns (source N/A, cat 3)
            ("FDR Interest - Dutch Bangla", 8750, 20, None, 3, True, "quarterly"),
            ("DPS Interest - City Bank", 3200, 15, None, 3, True, "monthly"),
            # Bonus
            ("Eid Bonus - TechCorp", 50000, 60, 0, 5, False, None),
        ]

        self.incomes = []
        for (
            desc,
            amount,
            day_ago,
            src_idx,
            cat_idx,
            is_recurring,
            cycle,
        ) in incomes_data:
            inc = Income.objects.create(
                owner=self.user,
                amount=amount,
                date=_d(day_ago),
                bank_account_id=(
                    self._ids["bank_salary"]
                    if src_idx == 0
                    else self._ids["bank_primary"]
                ),
                source=(
                    self.income_sources[src_idx]
                    if src_idx is not None
                    else self.income_sources[0]
                ),
                category=self.income_categories[cat_idx],
                description=desc,
                is_recurring=is_recurring,
                recurring_cycle=cycle,
                currency="BDT",
            )
            self.incomes.append(inc)

        self._ok(f"Created {len(self.incomes)} incomes")

    # ====================================================================
    # TRANSACTIONS (Bank)
    # ====================================================================

    def _seed_transactions(self):
        from bank.models import Transaction

        transactions = [
            # Salary credits to salary account
            (
                self.bank_accounts[1],
                None,
                "income",
                120000,
                "credit",
                self._ids["cat_salary"],
                15,
                "Salary - TechCorp BD",
            ),
            (
                self.bank_accounts[1],
                None,
                "income",
                30000,
                "credit",
                self._ids["cat_rental"],
                1,
                "Shop Rent Received",
            ),
            (
                self.bank_accounts[1],
                None,
                "income",
                35000,
                "credit",
                self._ids["cat_freelance"],
                10,
                "Upwork Withdrawal",
            ),
            # Expense debits from primary
            (
                self.bank_accounts[0],
                None,
                "expense",
                20000,
                "debit",
                self._ids["cat_rent"],
                1,
                "Rent Payment",
            ),
            (
                self.bank_accounts[0],
                None,
                "expense",
                4500,
                "debit",
                self._ids["cat_utilities"],
                5,
                "DESCO Bill",
            ),
            (
                self.bank_accounts[0],
                None,
                "expense",
                6200,
                "debit",
                self._ids["cat_groceries"],
                8,
                "Unimart Shopping",
            ),
            (
                self.bank_accounts[0],
                None,
                "expense",
                2800,
                "debit",
                self._ids["cat_dining"],
                2,
                "Star Kabab",
            ),
            (
                self.bank_accounts[0],
                None,
                "expense",
                800,
                "debit",
                self._ids["cat_entertainment"],
                1,
                "Netflix",
            ),
            # Transfer salary to primary
            (
                self.bank_accounts[1],
                self.bank_accounts[0],
                "transfer",
                50000,
                "debit",
                _rand_id(),
                16,
                "Transfer to Savings",
            ),
            (
                self.bank_accounts[0],
                self.bank_accounts[1],
                "transfer",
                50000,
                "credit",
                _rand_id(),
                16,
                "Transfer from Salary",
            ),
        ]

        count = 0
        for (
            account,
            to_account,
            ttype,
            amount,
            direction,
            cat_id,
            day_ago,
            desc,
        ) in transactions:
            Transaction.objects.create(
                owner=self.user,
                bank_account=account,
                to_bank_account=to_account,
                type=ttype,
                amount=amount,
                direction=direction,
                category_id=cat_id,
                date=_d(day_ago),
                description=desc,
                currency="BDT",
            )
            count += 1

        self._ok(f"Created {count} bank transactions")

    # ====================================================================
    # BUDGETS
    # ====================================================================

    def _seed_budgets(self):
        from budget.models import Budget, BudgetCategory

        budget = Budget.objects.create(
            owner=self.user,
            name=f"Monthly Budget - {self.month_str}",
            month=self.month_str,
            currency="BDT",
            total_budget_amount=93000,
        )

        budget_cats = [
            (self.expense_categories[0], "Groceries", 25000),
            (self.expense_categories[1], "Transport", 10000),
            (self.expense_categories[2], "Dining Out", 8000),
            (self.expense_categories[3], "Shopping", 12000),
            (self.expense_categories[4], "Rent", 20000),
            (self.expense_categories[5], "Utilities", 10000),
            (self.expense_categories[6], "Entertainment", 5000),
            (self.expense_categories[7], "Healthcare", 3000),
        ]

        for cat, name, amount in budget_cats:
            BudgetCategory.objects.create(
                owner=self.user,
                budget=budget,
                name=name,
                category_id=cat.id,
                budget_amount=amount,
            )

        self._ok(f"Created budget '{budget.name}' with {len(budget_cats)} categories")

    # ====================================================================
    # LOANS
    # ====================================================================

    def _seed_loans(self):
        from loan.models import Loan, LoanPayment

        loans_data = [
            {
                "name": "Personal Loan - City Bank",
                "type": "personal",
                "lender_name": "City Bank",
                "principal_amount": 500000,
                "current_balance": 380000,
                "interest_rate": Decimal("12.50"),
                "term_months": 36,
                "emi_amount": 16700,
                "start_date": _d(180),
                "next_payment_date": _d(-5),
                "paid_amount": 120000,
                "paid_installments": 7,
                "total_installments": 36,
                "status": "active",
                "bank_account_id": self._ids["bank_salary"],
            },
            {
                "name": "Car Loan - DBBL",
                "type": "auto",
                "lender_name": "Dutch-Bangla Bank",
                "principal_amount": 1500000,
                "current_balance": 1200000,
                "interest_rate": Decimal("9.00"),
                "term_months": 60,
                "emi_amount": 31200,
                "start_date": _d(365),
                "next_payment_date": _d(-8),
                "paid_amount": 300000,
                "paid_installments": 10,
                "total_installments": 60,
                "status": "active",
                "bank_account_id": self._ids["bank_primary"],
            },
        ]

        self.loans = []
        for loan_data in loans_data:
            loan = Loan.objects.create(owner=self.user, **loan_data)
            self.loans.append(loan)

            # Create some payments
            for i in range(3):
                LoanPayment.objects.create(
                    owner=self.user,
                    loan=loan,
                    amount=loan.emi_amount,
                    principal_component=int(loan.emi_amount * 0.7),
                    interest_component=int(loan.emi_amount * 0.3),
                    payment_date=_d(30 * (i + 1)),
                    payment_number=loan.paid_installments - 2 + i,
                    bank_account_id=loan.bank_account_id,
                )

        self._ok(f"Created {len(self.loans)} loans with payments")

    # ====================================================================
    # INVESTMENTS
    # ====================================================================

    def _seed_investments(self):
        from investment.models import Investment, InvestmentTransaction

        investments_data = [
            {
                "name": "Dutch Bangla FDR - 2 Year",
                "category": "fdr",
                "institution": "Dutch-Bangla Bank",
                "account_number": "FDR-2024-001",
                "purchase_date": _d(365),
                "maturity_date": _d(-365 + 730),
                "invested_amount": 500000,
                "current_value": 535000,
                "total_returns": 35000,
                "interest_rate": Decimal("7.00"),
                "compounding": "quarterly",
                "tax_on_interest": True,
                "status": "active",
                "auto_renew": True,
                "bank_account_id": self._ids["bank_fdr"],
                "currency": "BDT",
            },
            {
                "name": "City Bank DPS - 5 Year",
                "category": "dps",
                "institution": "City Bank",
                "account_number": "DPS-2023-015",
                "purchase_date": _d(730),
                "maturity_date": _d(-730 + 1825),
                "invested_amount": 144000,
                "current_value": 288000,
                "total_returns": 144000,
                "monthly_deposit_amount": 4000,
                "total_deposited_so_far": 96000,
                "deposit_count": 24,
                "interest_rate": Decimal("7.50"),
                "compounding": "monthly",
                "tax_on_interest": False,
                "status": "active",
                "bank_account_id": self._ids["bank_salary"],
                "currency": "BDT",
            },
            {
                "name": "Grameenphone Shares - DSE",
                "category": "stock",
                "institution": "LankaBangla Securities",
                "purchase_date": _d(200),
                "invested_amount": 200000,
                "current_value": 245000,
                "total_returns": 45000,
                "quantity": Decimal("5000"),
                "avg_buy_price": 40,
                "current_unit_price": 49,
                "stock_symbol": "GP",
                "stock_exchange": "DSE",
                "dividend_yield": Decimal("5.20"),
                "status": "active",
                "bank_account_id": self._ids["bank_primary"],
                "currency": "BDT",
                "tags": ["stock", "DSE", "dividend"],
            },
            {
                "name": "Gold Bar - 22 Carat",
                "category": "gold",
                "institution": "Aarong",
                "purchase_date": _d(150),
                "invested_amount": 300000,
                "current_value": 365000,
                "total_returns": 65000,
                "weight_grams": Decimal("50.00"),
                "purity": "22k",
                "status": "active",
                "currency": "BDT",
                "tags": ["gold", "physical"],
            },
        ]

        self.investments = []
        for inv_data in investments_data:
            inv = Investment.objects.create(owner=self.user, **inv_data)
            self.investments.append(inv)

            # Create a couple transactions per investment
            inv_type = "interest" if inv.category in ("fdr", "dps") else "buy"
            InvestmentTransaction.objects.create(
                owner=self.user,
                investment=inv,
                type=inv_type,
                amount=inv.total_returns // 2,
                date=_d(90),
                note=f"Quarterly {inv_type}",
            )

        self._ok(f"Created {len(self.investments)} investments with transactions")

    # ====================================================================
    # INSURANCE
    # ====================================================================

    def _seed_insurance(self):
        from insurance.models import (
            Insurance,
            InsuranceBeneficiary,
            InsurancePremiumPayment,
        )

        # Life Insurance
        life_ins = Insurance.objects.create(
            owner=self.user,
            name="Life Insurance - MetLife",
            category="life",
            provider="MetLife Bangladesh",
            policy_number="ML-2024-LI-78432",
            group_policy_number="GRP-TECHCORP-001",
            coverage_amount=5000000,
            premium_amount=2500,
            premium_frequency="monthly",
            issue_date=_d(365),
            start_date=_d(365),
            expiry_date=_d(-365 + 3650),
            maturity_date=_d(-365 + 3650),
            next_premium_due_date=_d(-1),
            total_premium_paid=30000,
            paid_premiums_count=12,
            status="active",
            auto_renew=True,
            policy_term=10,
            maturity_benefit=5000000,
            rider_names=["Accidental Death", "Critical Illness"],
            bank_account_id=self._ids["bank_primary"],
            currency="BDT",
        )

        InsuranceBeneficiary.objects.create(
            owner=self.user,
            insurance=life_ins,
            name="Fatima Rahim",
            relationship="spouse",
            percentage=60,
            phone="+8801712345678",
        )
        InsuranceBeneficiary.objects.create(
            owner=self.user,
            insurance=life_ins,
            name="Ibrahim Rahim",
            relationship="child",
            percentage=40,
            phone="",
        )

        # Premium payments
        for i in range(5):
            InsurancePremiumPayment.objects.create(
                owner=self.user,
                insurance=life_ins,
                amount=2500,
                payment_date=_d(30 * (i + 1)),
                payment_number=life_ins.paid_premiums_count - 4 + i,
                bank_account_id=self._ids["bank_primary"],
            )

        # Health Insurance
        health_ins = Insurance.objects.create(
            owner=self.user,
            name="Health Insurance - Pragati Life",
            category="health",
            provider="Pragati Life Insurance",
            policy_number="PL-2024-HI-45210",
            coverage_amount=1000000,
            premium_amount=1800,
            premium_frequency="monthly",
            issue_date=_d(200),
            start_date=_d(200),
            expiry_date=_d(-200 + 365),
            next_premium_due_date=_d(-2),
            total_premium_paid=18000,
            paid_premiums_count=10,
            status="active",
            deductible_amount=5000,
            copay_percent=Decimal("20.00"),
            network_hospitals="United, Square, Labaid, Ibn Sina",
            bank_account_id=self._ids["bank_primary"],
            currency="BDT",
        )

        self._ok(
            f"Created 2 insurance policies (life + health) with beneficiaries & payments"
        )

    # ====================================================================
    # SAVINGS GOALS
    # ====================================================================

    def _seed_savings_goals(self):
        from savings_goal.models import (
            SavingsGoal,
            SavingsGoalContribution,
            SavingsGoalMilestone,
        )

        goals_data = [
            {
                "name": "Emergency Fund",
                "description": "6 months of expenses as safety net",
                "category": "emergency_fund",
                "status": "active",
                "target_amount": 500000,
                "current_amount": 275000,
                "start_date": _d(180),
                "target_date": _d(-180 + 365),
                "monthly_contribution_amount": 25000,
                "auto_contribute_enabled": True,
                "auto_contribute_day_of_month": 5,
                "total_contributed": 275000,
                "contribution_count": 9,
                "motivational_quote": "The best time to save was yesterday. The next best time is now.",
                "cover_color": "#EF4444",
                "cover_icon": "🛡️",
                "current_streak": 5,
                "longest_streak": 8,
                "priority": "high",
            },
            {
                "name": "Japan Vacation 2027",
                "description": "Trip to Tokyo and Osaka with family",
                "category": "vacation",
                "status": "active",
                "target_amount": 400000,
                "current_amount": 85000,
                "start_date": _d(90),
                "target_date": date(2027, 3, 1),
                "monthly_contribution_amount": 15000,
                "total_contributed": 85000,
                "contribution_count": 5,
                "cover_color": "#3B82F6",
                "cover_icon": "✈️",
                "current_streak": 3,
                "longest_streak": 4,
                "priority": "medium",
            },
            {
                "name": "New MacBook Pro",
                "description": "M4 MacBook Pro for development work",
                "category": "gadget",
                "status": "active",
                "target_amount": 250000,
                "current_amount": 180000,
                "start_date": _d(60),
                "target_date": _d(-60 + 180),
                "monthly_contribution_amount": 30000,
                "total_contributed": 180000,
                "contribution_count": 6,
                "cover_color": "#8B5CF6",
                "cover_icon": "💻",
                "current_streak": 6,
                "longest_streak": 6,
                "priority": "high",
            },
        ]

        self.savings_goals = []
        for goal_data in goals_data:
            goal = SavingsGoal.objects.create(owner=self.user, **goal_data)
            self.savings_goals.append(goal)

            # Contributions
            for i in range(3):
                SavingsGoalContribution.objects.create(
                    owner=self.user,
                    goal=goal,
                    amount=goal.monthly_contribution_amount,
                    date=_d(30 * (i + 1)),
                    note=f"Monthly contribution #{i + 1}",
                    bank_account_id=self._ids["bank_primary"],
                )

            # Milestones
            for pct, label in [
                (25, "Quarter Way"),
                (50, "Halfway"),
                (75, "Almost There"),
                (100, "Goal Reached!"),
            ]:
                achieved = pct <= (goal.current_amount / goal.target_amount * 100)
                SavingsGoalMilestone.objects.create(
                    owner=self.user,
                    goal=goal,
                    percent=pct,
                    label=label,
                    achieved=achieved,
                    achieved_date=_d(30) if achieved else None,
                )

        self._ok(
            f"Created {len(self.savings_goals)} savings goals with contributions & milestones"
        )

    # ====================================================================
    # ASSETS
    # ====================================================================

    def _seed_assets(self):
        from asset.models import Asset, AssetValuation

        # Real Estate
        flat = Asset.objects.create(
            owner=self.user,
            name="Apartment - Gulshan Avenue",
            category="real_estate",
            description="3 bed, 2 bath apartment in Gulshan-2",
            purchase_date=date(2020, 6, 15),
            purchase_price=15000000,
            purchase_from="Bashundhara Group",
            current_value=22000000,
            current_condition="excellent",
            location="Gulshan-2, Dhaka",
            property_type="apartment",
            property_address="House 45, Road 135, Gulshan-2, Dhaka 1212",
            size_sqft=Decimal("1800.00"),
            floor_number="8th",
            registration_date=date(2020, 8, 1),
            registration_number="REG-2020-45678",
            khatian_number="KHAT-4567",
            depreciation_method="none",
            status="owned",
            ownership_percentage=100,
            currency="BDT",
            tags=["apartment", "gulshan", "dhaka"],
        )

        AssetValuation.objects.create(
            asset=flat,
            date=_d(30),
            value=22000000,
            note="Current market estimate based on recent area sales",
        )

        # Vehicle
        car = Asset.objects.create(
            owner=self.user,
            name="Toyota Corolla 2022",
            category="vehicle",
            description="Toyota Corolla X 1.6L, White",
            purchase_date=date(2022, 1, 10),
            purchase_price=3200000,
            current_value=2600000,
            current_condition="good",
            location="Dhaka",
            vehicle_type="car",
            vehicle_brand="Toyota",
            vehicle_model="Corolla X 1.6L",
            vehicle_year=2022,
            vehicle_registration_no="DHAKA-METRO-GA-45-1234",
            engine_no="1NZ-FE-876543",
            chassis_no="NZE141-567890",
            mileage_km=35000,
            depreciation_method="straight_line",
            useful_life_years=10,
            salvage_value=500000,
            current_book_value=2600000,
            status="owned",
            currency="BDT",
            tags=["car", "toyota"],
        )

        self._ok("Created 2 assets (apartment + car) with valuations")

    # ====================================================================
    # LENDING
    # ====================================================================

    def _seed_lending(self):
        from lending.models import Lending, LendingPayment

        lendings_data = [
            {
                "borrower_name": "Karim Uddin",
                "borrower_phone": "+8801898765432",
                "borrower_email": "karim@example.com",
                "relationship": "friend",
                "principal_amount": 50000,
                "current_balance": 30000,
                "interest_rate": Decimal("0.00"),
                "total_repayable_amount": 50000,
                "total_repaid_amount": 20000,
                "issued_date": _d(90),
                "due_date": _d(-90 + 180),
                "repayment_schedule": "monthly",
                "status": "active",
                "currency": "BDT",
            },
            {
                "borrower_name": "Jamal Ahmed",
                "borrower_phone": "+8801612345678",
                "borrower_email": "",
                "relationship": "colleague",
                "principal_amount": 100000,
                "current_balance": 65000,
                "interest_rate": Decimal("5.00"),
                "total_interest_amount": 5000,
                "total_repayable_amount": 105000,
                "total_repaid_amount": 40000,
                "issued_date": _d(150),
                "due_date": _d(-150 + 365),
                "repayment_schedule": "monthly",
                "status": "active",
                "currency": "BDT",
            },
        ]

        self.lendings = []
        for lend_data in lendings_data:
            lending = Lending.objects.create(owner=self.user, **lend_data)
            self.lendings.append(lending)

            # Some payments
            LendingPayment.objects.create(
                owner=self.user,
                lending=lending,
                amount=10000,
                payment_date=_d(60),
                payment_number=1,
                note="First repayment",
            )
            LendingPayment.objects.create(
                owner=self.user,
                lending=lending,
                amount=10000,
                payment_date=_d(30),
                payment_number=2,
                note="Second repayment",
            )

        self._ok(f"Created {len(self.lendings)} lending records with payments")

    # ====================================================================
    # INVOICES
    # ====================================================================

    def _seed_invoices(self):
        from invoice.models import Invoice, InvoiceItem

        invoices_data = [
            {
                "invoice_number": "INV-2026-001",
                "type": "sent",
                "client_name": "Digital Solutions Ltd",
                "client_email": "finance@digitalsolutions.com",
                "client_phone": "+88021234567",
                "client_address": "House 12, Road 7, Banani, Dhaka",
                "subtotal": 85000,
                "tax_rate": Decimal("5.00"),
                "tax_amount": 4250,
                "discount_amount": 0,
                "total_amount": 89250,
                "status": "paid",
                "issue_date": _d(45),
                "due_date": _d(15),
                "paid_date": _d(10),
                "bank_account_id": self._ids["bank_primary"],
            },
            {
                "invoice_number": "INV-2026-002",
                "type": "sent",
                "client_name": "StartUp Hub BD",
                "client_email": "accounts@startuphub.bd",
                "client_phone": "+88029876543",
                "client_address": "Floor 5, Tower B, Mohakhali, Dhaka",
                "subtotal": 150000,
                "tax_rate": Decimal("5.00"),
                "tax_amount": 7500,
                "discount_amount": 5000,
                "total_amount": 152500,
                "status": "sent",
                "issue_date": _d(10),
                "due_date": _d(-20),
                "bank_account_id": self._ids["bank_primary"],
            },
            {
                "invoice_number": "INV-2026-003",
                "type": "received",
                "client_name": "AWS Bangladesh",
                "client_email": "billing@aws.amazon.com",
                "client_phone": "",
                "client_address": "",
                "subtotal": 12500,
                "tax_rate": Decimal("15.00"),
                "tax_amount": 1875,
                "discount_amount": 0,
                "total_amount": 14375,
                "status": "paid",
                "issue_date": _d(20),
                "due_date": _d(5),
                "paid_date": _d(3),
                "bank_account_id": self._ids["bank_primary"],
            },
        ]

        self.invoices = []
        for inv_data in invoices_data:
            invoice = Invoice.objects.create(owner=self.user, **inv_data)
            self.invoices.append(invoice)

            # Create line items
            items = [
                ("Web Application Development", 40, 2000, 80000),
                ("UI/UX Design Consultation", 5, 1000, 5000),
            ]
            for desc, qty, unit_price, total in items:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=desc,
                    quantity=qty,
                    unit_price=unit_price,
                    total=total,
                )

        self._ok(f"Created {len(self.invoices)} invoices with line items")

    # ====================================================================
    # BILLS
    # ====================================================================

    def _seed_bills(self):
        from bill.models import Bill, BillPaymentHistory

        bills_data = [
            {
                "name": "Electricity - DESCO",
                "description": "Monthly electricity bill",
                "category": "utilities",
                "status": "paid",
                "amount": 4500,
                "payee_name": "Dhaka Electric Supply Company",
                "payee_account": "DESCO-Account-789012",
                "payee_website": "https://desco.org.bd",
                "due_date": _d(10),
                "due_date_day_of_month": 15,
                "recurrence": "monthly",
                "recurrence_day_of_month": 15,
                "total_paid_amount": 4500,
                "total_payments_count": 1,
                "last_paid_date": _d(10),
                "last_paid_amount": 4500,
            },
            {
                "name": "Internet - Link3",
                "description": "Fiber internet connection 50Mbps",
                "category": "utilities",
                "status": "paid",
                "amount": 1500,
                "payee_name": "Link3 Technologies",
                "payee_account": "LINK3-45678",
                "payee_website": "https://link3.net",
                "due_date": _d(5),
                "due_date_day_of_month": 10,
                "recurrence": "monthly",
                "recurrence_day_of_month": 10,
                "total_paid_amount": 1500,
                "total_payments_count": 1,
                "last_paid_date": _d(5),
                "last_paid_amount": 1500,
            },
            {
                "name": "Gas - Titas",
                "description": "Monthly gas bill",
                "category": "utilities",
                "status": "upcoming",
                "amount": 1800,
                "payee_name": "Titas Gas Transmission",
                "payee_account": "TITAS-11223",
                "payee_website": "",
                "due_date": _d(-5),
                "due_date_day_of_month": 20,
                "recurrence": "monthly",
                "recurrence_day_of_month": 20,
            },
            {
                "name": "Credit Card - DBBL Visa",
                "description": "Monthly credit card bill",
                "category": "credit_card",
                "status": "upcoming",
                "amount": 35000,
                "payee_name": "Dutch-Bangla Bank",
                "payee_account": "CC-DBBL-4532",
                "payee_website": "https://dbbl.com.bd",
                "due_date": _d(-3),
                "due_date_day_of_month": 15,
                "recurrence": "monthly",
                "recurrence_day_of_month": 15,
            },
            {
                "name": "Netflix Subscription",
                "description": "Standard plan streaming",
                "category": "subscriptions",
                "status": "paid",
                "amount": 800,
                "payee_name": "Netflix Inc",
                "payee_account": "",
                "payee_website": "https://netflix.com",
                "due_date": _d(1),
                "due_date_day_of_month": 5,
                "recurrence": "monthly",
                "recurrence_day_of_month": 5,
                "auto_pay_enabled": True,
                "auto_pay_method": "Credit Card DBBL Visa",
                "auto_pay_day_before": 1,
                "total_paid_amount": 800,
                "total_payments_count": 1,
                "last_paid_date": _d(1),
                "last_paid_amount": 800,
            },
        ]

        self.bills = []
        for bill_data in bills_data:
            bill = Bill.objects.create(owner=self.user, **bill_data)
            self.bills.append(bill)

            # Add payment history for paid bills
            if bill.status == "paid":
                BillPaymentHistory.objects.create(
                    bill=bill,
                    payment_date=bill.last_paid_date or _d(5),
                    amount=bill.last_paid_amount or bill.amount,
                    payment_method="Online Banking",
                    reference_number=f"TXN-{uuid.uuid4().hex[:8].upper()}",
                )

        self._ok(f"Created {len(self.bills)} bills with payment history")

    # ====================================================================
    # CALENDAR EVENTS
    # ====================================================================

    def _seed_calendar_events(self):
        from fcalender.models import CalendarEvent

        events_data = [
            {
                "title": "Loan EMI - City Bank",
                "description": "Monthly personal loan EMI payment",
                "category": "emi_payment",
                "status": "upcoming",
                "amount": 16700,
                "event_date": _d(-3),
                "due_date": _d(-3),
                "recurrence": "monthly",
                "recurrence_day_of_month": 25,
                "reminder_days_before": 3,
                "reminder_enabled": True,
                "color": "#EF4444",
                "priority": "high",
            },
            {
                "title": "Car Loan EMI - DBBL",
                "description": "Monthly car loan installment",
                "category": "emi_payment",
                "status": "upcoming",
                "amount": 31200,
                "event_date": _d(-8),
                "due_date": _d(-8),
                "recurrence": "monthly",
                "recurrence_day_of_month": 15,
                "reminder_days_before": 3,
                "reminder_enabled": True,
                "color": "#F59E0B",
                "priority": "high",
            },
            {
                "title": "Insurance Premium - MetLife",
                "description": "Monthly life insurance premium",
                "category": "insurance_premium",
                "status": "upcoming",
                "amount": 2500,
                "event_date": _d(-1),
                "due_date": _d(-1),
                "recurrence": "monthly",
                "recurrence_day_of_month": 28,
                "reminder_days_before": 2,
                "reminder_enabled": True,
                "color": "#3B82F6",
                "priority": "medium",
            },
            {
                "title": "Credit Card Payment Due",
                "description": "DBBL Visa Platinum payment",
                "category": "bill_payment",
                "status": "upcoming",
                "amount": 35000,
                "event_date": _d(-3),
                "due_date": _d(-3),
                "recurrence": "monthly",
                "recurrence_day_of_month": 15,
                "reminder_days_before": 5,
                "reminder_enabled": True,
                "second_reminder_days_before": 1,
                "color": "#8B5CF6",
                "priority": "high",
            },
            {
                "title": "Salary Credit",
                "description": "Monthly salary from TechCorp BD",
                "category": "salary",
                "status": "completed",
                "amount": 120000,
                "event_date": _d(15),
                "recurrence": "monthly",
                "recurrence_day_of_month": 28,
                "color": "#10B981",
                "priority": "low",
            },
            {
                "title": "Tax Filing Deadline",
                "description": "Income tax return submission",
                "category": "tax_deadline",
                "status": "upcoming",
                "event_date": date(2026, 11, 30),
                "due_date": date(2026, 11, 30),
                "reminder_days_before": 30,
                "reminder_days_before": 30,
                "reminder_enabled": True,
                "color": "#EF4444",
                "priority": "high",
            },
            {
                "title": "DPS Installment",
                "description": "City Bank monthly DPS deposit",
                "category": "investment_deposit",
                "status": "completed",
                "amount": 4000,
                "event_date": _d(2),
                "recurrence": "monthly",
                "recurrence_day_of_month": 10,
                "reminder_days_before": 1,
                "reminder_enabled": True,
                "color": "#06B6D4",
                "priority": "medium",
            },
            {
                "title": "Rental Income Received",
                "description": "Monthly shop rent from Gulshan tenant",
                "category": "rental_income",
                "status": "completed",
                "amount": 30000,
                "event_date": _d(1),
                "recurrence": "monthly",
                "recurrence_day_of_month": 1,
                "color": "#10B981",
                "priority": "low",
            },
        ]

        self.calendar_events = []
        for evt_data in events_data:
            evt = CalendarEvent.objects.create(owner=self.user, **evt_data)
            self.calendar_events.append(evt)

        self._ok(f"Created {len(self.calendar_events)} calendar events")

    # ====================================================================
    # DOCUMENTS
    # ====================================================================

    def _seed_documents(self):
        from document.models import DocumentVaultItem

        docs_data = [
            {
                "name": "Passport Scan",
                "description": "Bangladeshi passport - scanned copy",
                "category": "id_proof",
                "format": "pdf",
                "status": "active",
                "file_size": 2500000,
                "file_name": "passport_rahim_2024.pdf",
                "document_date": date(2024, 3, 15),
                "expiry_date": date(2029, 3, 14),
                "reminder_before_days": 90,
                "is_important": True,
                "is_favorite": True,
            },
            {
                "name": "Tax Return 2025",
                "description": "Income tax return for assessment year 2025-2026",
                "category": "tax_return",
                "format": "pdf",
                "status": "active",
                "file_size": 1500000,
                "file_name": "tax_return_ay2025.pdf",
                "document_date": date(2025, 11, 30),
            },
            {
                "name": "MetLife Insurance Policy",
                "description": "Life insurance policy document",
                "category": "insurance_policy",
                "format": "pdf",
                "status": "active",
                "file_size": 3200000,
                "file_name": "metlife_policy_ML-2024-LI-78432.pdf",
                "document_date": date(2024, 1, 15),
                "is_important": True,
            },
            {
                "name": "Apartment Sale Deed",
                "description": "Property sale deed for Gulshan apartment",
                "category": "property_deed",
                "format": "pdf",
                "status": "active",
                "file_size": 8500000,
                "file_name": "sale_deed_gulshan_apt.pdf",
                "document_date": date(2020, 6, 15),
                "is_important": True,
                "is_favorite": True,
            },
            {
                "name": "Vehicle Registration",
                "description": "Car registration document - BRTA",
                "category": "vehicle_registration",
                "format": "pdf",
                "status": "active",
                "file_size": 1800000,
                "file_name": "vehicle_reg_corolla_2022.pdf",
                "document_date": date(2022, 1, 15),
                "expiry_date": date(2027, 1, 14),
                "reminder_before_days": 60,
            },
        ]

        self.documents = []
        for doc_data in docs_data:
            doc = DocumentVaultItem.objects.create(owner=self.user, **doc_data)
            self.documents.append(doc)

        self._ok(f"Created {len(self.documents)} document vault items")
