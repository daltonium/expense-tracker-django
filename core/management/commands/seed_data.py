"""
OkaneTrack — Auto Data Seeder
Django Management Command

Usage:
    python manage.py seed_data
    python manage.py seed_data --flush    # clears existing data first
    python manage.py seed_data --months 6

Place this file at:
    core/management/commands/seed_data.py

Also create these empty __init__.py files if they don't exist:
    core/management/__init__.py
    core/management/commands/__init__.py
"""

import datetime
import decimal
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Workspace, Expense, Income, BudgetRule, Investment


# ─────────────────────────────────────────────────────────────────
# SEED CONFIG
# ─────────────────────────────────────────────────────────────────
PERSONAL_USER = dict(username="ace_personal", password="Demo@1234")
COMPANY_USER  = dict(username="ace_company",  password="Demo@1234")
MONTHS_BACK   = 4
TODAY         = datetime.date.today()

# ─────────────────────────────────────────────────────────────────
# PERSONAL DATA POOLS
# ─────────────────────────────────────────────────────────────────
PERSONAL_INCOMES = [
    dict(title="Monthly Salary",    source="salary",     amount="72000.00"),
    dict(title="Freelance Project", source="freelance",  amount="18500.00"),
    dict(title="Dividend Credit",   source="investment", amount="2400.00"),
]

PERSONAL_EXPENSES = [
    dict(title="DMart Monthly",        category="grocery",       amount="3200.00"),
    dict(title="Vegetables & Fruits",  category="grocery",       amount="850.00"),
    dict(title="Milk & Dairy",         category="grocery",       amount="620.00"),
    dict(title="Zomato Orders",        category="food",          amount="2100.00"),
    dict(title="Swiggy Weekend",       category="food",          amount="980.00"),
    dict(title="Office Canteen",       category="food",          amount="1500.00"),
    dict(title="EB Bill",              category="bills",         amount="1450.00"),
    dict(title="Airtel Broadband",     category="bills",         amount="799.00"),
    dict(title="Jio Recharge",         category="bills",         amount="349.00"),
    dict(title="Petrol – Bike",        category="transport",     amount="1200.00"),
    dict(title="Ola/Uber",             category="transport",     amount="750.00"),
    dict(title="Bus Pass",             category="transport",     amount="300.00"),
    dict(title="Apollo Pharmacy",      category="health",        amount="680.00"),
    dict(title="Gym Membership",       category="health",        amount="1200.00"),
    dict(title="Netflix + Hotstar",    category="entertainment", amount="598.00"),
    dict(title="Movie Tickets",        category="entertainment", amount="550.00"),
    dict(title="Chess Tournament Fee", category="entertainment", amount="200.00"),
    dict(title="YouTube Premium",      category="subscription",  amount="189.00"),
    dict(title="Spotify",              category="subscription",  amount="119.00"),
    dict(title="Udemy Course",         category="subscription",  amount="399.00"),
    dict(title="House Rent",           category="other",         amount="12000.00"),
    dict(title="Books & Stationery",   category="other",         amount="450.00"),
]

PERSONAL_INVESTMENTS = [
    dict(name="Nifty 50 Index Fund",    asset_type="mutual_fund",   amount_invested="50000", current_value="58400", status="active"),
    dict(name="HDFC Small Cap Fund",    asset_type="mutual_fund",   amount_invested="25000", current_value="28750", status="active"),
    dict(name="Reliance Industries",    asset_type="stocks",        amount_invested="15000", current_value="17200", status="active"),
    dict(name="Infosys",                asset_type="stocks",        amount_invested="12000", current_value="11500", status="active"),
    dict(name="Gold ETF",               asset_type="gold",          amount_invested="10000", current_value="11800", status="active"),
    dict(name="SBI FD 2yr",             asset_type="fixed_deposit", amount_invested="20000", current_value="21600", status="active"),
    dict(name="Bitcoin (0.02 BTC)",     asset_type="crypto",        amount_invested="8000",  current_value="6500",  status="active"),
    dict(name="Tech Mahindra (exited)", asset_type="stocks",        amount_invested="5000",  current_value="5900",  status="exited"),
]

# ─────────────────────────────────────────────────────────────────
# COMPANY DATA POOLS
# ─────────────────────────────────────────────────────────────────
COMPANY_INCOMES = [
    dict(title="Client Project – Alpha Corp",  source="business",  amount="180000.00"),
    dict(title="Retainer Fee – Beta Ltd",      source="business",  amount="75000.00"),
    dict(title="Software License Revenue",     source="business",  amount="45000.00"),
    dict(title="Consulting Fee – Gamma Inc",   source="freelance", amount="30000.00"),
]

COMPANY_EXPENSES = [
    dict(title="Dev Team Payroll",          category="payroll",       amount="120000.00"),
    dict(title="Designer Salary",           category="payroll",       amount="45000.00"),
    dict(title="AWS Cloud Hosting",         category="vendor",        amount="18500.00"),
    dict(title="Zoho CRM Subscription",     category="subscription",  amount="3499.00"),
    dict(title="Slack Pro Plan",            category="subscription",  amount="1200.00"),
    dict(title="GitHub Teams",             category="subscription",  amount="840.00"),
    dict(title="Office Rent",               category="bills",         amount="25000.00"),
    dict(title="Electricity – Office",      category="bills",         amount="4200.00"),
    dict(title="Internet Leased Line",      category="bills",         amount="6000.00"),
    dict(title="Office Supplies",           category="other",         amount="2800.00"),
    dict(title="Team Lunch Outing",         category="food",          amount="5500.00"),
    dict(title="Cab Reimbursement",         category="transport",     amount="3200.00"),
    dict(title="Vendor Payment – Dev Tools",category="vendor",        amount="8000.00"),
    dict(title="Legal & Compliance",        category="other",         amount="12000.00"),
]

COMPANY_INVESTMENTS = [
    dict(name="FD – Business Reserve",        asset_type="fixed_deposit", amount_invested="200000", current_value="214000", status="active"),
    dict(name="Liquid Fund – Corpus",          asset_type="mutual_fund",   amount_invested="100000", current_value="104500", status="active"),
    dict(name="Office Equipment (Real Asset)", asset_type="real_estate",   amount_invested="80000",  current_value="80000",  status="active"),
]


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
def random_date_in_month(year, month):
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, random.randint(1, last_day))


def get_past_months(n):
    months, y, m = [], TODAY.year, TODAY.month
    for _ in range(n):
        months.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return months[::-1]


def jitter(amount_str, low=0.85, high=1.20):
    """Apply a random ±variation to a decimal amount."""
    return (
        decimal.Decimal(amount_str)
        * decimal.Decimal(str(round(random.uniform(low, high), 4)))
    ).quantize(decimal.Decimal("0.01"))


# ─────────────────────────────────────────────────────────────────
# MANAGEMENT COMMAND
# ─────────────────────────────────────────────────────────────────
class Command(BaseCommand):
    help = "Seeds OkaneTrack with realistic demo data (personal + company workspaces)"

    def add_arguments(self, parser):
        parser.add_argument("--flush",  action="store_true",
                            help="Delete all existing app data before seeding")
        parser.add_argument("--months", type=int, default=MONTHS_BACK,
                            help=f"Months of history to generate (default: {MONTHS_BACK})")

    def handle(self, *args, **options):
        months = options["months"]

        # ── Optional flush ─────────────────────────────────────
        if options["flush"]:
            self.stdout.write(self.style.WARNING("🗑  Flushing existing data..."))
            Investment.objects.all().delete()
            BudgetRule.objects.all().delete()
            Expense.objects.all().delete()
            Income.objects.all().delete()
            Workspace.objects.all().delete()
            User.objects.filter(
                username__in=[PERSONAL_USER["username"], COMPANY_USER["username"]]
            ).delete()
            self.stdout.write(self.style.SUCCESS("   Flush complete."))

        past_months = get_past_months(months)

        # ── 1. Users ───────────────────────────────────────────
        self.stdout.write("\n👤 Creating demo users...")
        p_user = self._get_or_create_user(**PERSONAL_USER)
        c_user = self._get_or_create_user(**COMPANY_USER)

        # ── 2. Personal Workspace ──────────────────────────────
        self.stdout.write("\n🏠 Seeding personal workspace...")
        p_ws, _ = Workspace.objects.get_or_create(
            user=p_user, name="Ace Personal Wallet", mode="personal"
        )

        for year, month in past_months:
            # Income: salary always; others ~50% chance
            for inc in PERSONAL_INCOMES:
                if inc["source"] == "salary" or random.random() > 0.5:
                    Income.objects.create(
                        workspace=p_ws,
                        title=inc["title"],
                        source=inc["source"],
                        amount=jitter(inc["amount"], 0.95, 1.05),
                        date=random_date_in_month(year, month),
                    )
            # Expenses: ~80% of items each month
            for exp in PERSONAL_EXPENSES:
                if random.random() > 0.20:
                    Expense.objects.create(
                        workspace=p_ws,
                        title=exp["title"],
                        category=exp["category"],
                        amount=jitter(exp["amount"]),
                        date=random_date_in_month(year, month),
                    )

        BudgetRule.objects.get_or_create(
            workspace=p_ws,
            defaults={"needs_percent": 50, "wants_percent": 30, "savings_percent": 20},
        )
        for inv in PERSONAL_INVESTMENTS:
            Investment.objects.get_or_create(
                workspace=p_ws, name=inv["name"],
                defaults=dict(
                    asset_type=inv["asset_type"],
                    amount_invested=decimal.Decimal(inv["amount_invested"]),
                    current_value=decimal.Decimal(inv["current_value"]),
                    date_invested=TODAY - datetime.timedelta(days=random.randint(90, 500)),
                    status=inv["status"],
                ),
            )

        # ── 3. Company Workspace ───────────────────────────────
        self.stdout.write("\n🏢 Seeding company workspace...")
        c_ws, _ = Workspace.objects.get_or_create(
            user=c_user, name="Ace Ventures Pvt Ltd", mode="company"
        )
        for year, month in past_months:
            for inc in COMPANY_INCOMES:
                if random.random() > 0.30:
                    Income.objects.create(
                        workspace=c_ws,
                        title=inc["title"],
                        source=inc["source"],
                        amount=jitter(inc["amount"], 0.90, 1.15),
                        date=random_date_in_month(year, month),
                    )
            for exp in COMPANY_EXPENSES:
                if random.random() > 0.20:
                    Expense.objects.create(
                        workspace=c_ws,
                        title=exp["title"],
                        category=exp["category"],
                        amount=jitter(exp["amount"], 0.90, 1.10),
                        date=random_date_in_month(year, month),
                    )

        BudgetRule.objects.get_or_create(
            workspace=c_ws,
            defaults={"needs_percent": 60, "wants_percent": 25, "savings_percent": 15},
        )
        for inv in COMPANY_INVESTMENTS:
            Investment.objects.get_or_create(
                workspace=c_ws, name=inv["name"],
                defaults=dict(
                    asset_type=inv["asset_type"],
                    amount_invested=decimal.Decimal(inv["amount_invested"]),
                    current_value=decimal.Decimal(inv["current_value"]),
                    date_invested=TODAY - datetime.timedelta(days=random.randint(60, 365)),
                    status=inv["status"],
                ),
            )

        # ── Summary ────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 52))
        self.stdout.write(self.style.SUCCESS("✅  OkaneTrack seed complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 52))
        self.stdout.write(f"  Personal workspace : {p_ws.name}")
        self.stdout.write(f"  Login              : {PERSONAL_USER['username']} / {PERSONAL_USER['password']}")
        self.stdout.write(f"  Company  workspace : {c_ws.name}")
        self.stdout.write(f"  Login              : {COMPANY_USER['username']} / {COMPANY_USER['password']}")
        self.stdout.write(self.style.SUCCESS("=" * 52))
        self.stdout.write(f"  Expenses    : {Expense.objects.count()}")
        self.stdout.write(f"  Incomes     : {Income.objects.count()}")
        self.stdout.write(f"  Investments : {Investment.objects.count()}")
        self.stdout.write(self.style.SUCCESS("=" * 52))

    def _get_or_create_user(self, username, password):
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f"  ✔ Created  : {username}")
        else:
            self.stdout.write(f"  ↩ Exists   : {username}")
        return user
