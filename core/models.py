from django.db import models
from django.contrib.auth.models import User

import decimal

class Workspace(models.Model):
    MODE_CHOICES = [
        ('personal', 'Personal / Family'),
        ('company', 'Company'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.mode})"
    
class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('grocery', 'Grocery'),
        ('food', 'Food & Dining'),
        ('bills', 'Bills & Utilities'),
        ('transport', 'Transport'),
        ('health', 'Health'),
        ('entertainment', 'Entertainment'),
        ('payroll', 'Payroll'),
        ('subscription', 'Subscription'),
        ('vendor', 'Vendor Payment'),
        ('other', 'Other'),
    ]

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    date = models.DateField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} – ₹{self.amount}"

class Income(models.Model):
    SOURCE_CHOICES = [
        ('salary', 'Salary'),
        ('freelance', 'Freelance'),
        ('business', 'Business Revenue'),
        ('investment', 'Investment Returns'),
        ('rental', 'Rental Income'),
        ('other', 'Other'),
    ]

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    date = models.DateField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} – ₹{self.amount}"
    
class BudgetRule(models.Model):
    workspace = models.OneToOneField(Workspace, on_delete=models.CASCADE)
    needs_percent = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    wants_percent = models.DecimalField(max_digits=5, decimal_places=2, default=30)
    savings_percent = models.DecimalField(max_digits=5, decimal_places=2, default=20)

    def __str__(self):
        return f"Budget Rule for {self.workspace.name}"

class Investment(models.Model):
    ASSET_CHOICES = [
        ('stocks', 'Stocks'),
        ('mutual_fund', 'Mutual Fund'),
        ('crypto', 'Cryptocurrency'),
        ('fixed_deposit', 'Fixed Deposit'),
        ('gold', 'Gold'),
        ('real_estate', 'Real Estate'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('exited', 'Exited'),
    ]

    workspace        = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    name             = models.CharField(max_length=200)
    asset_type       = models.CharField(max_length=50, choices=ASSET_CHOICES)
    amount_invested  = models.DecimalField(max_digits=14, decimal_places=2)
    current_value    = models.DecimalField(max_digits=14, decimal_places=2)
    date_invested    = models.DateField()
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    note             = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    @property
    def returns(self):
        return self.current_value - self.amount_invested

    @property
    def returns_percent(self):
        if self.amount_invested > 0:
            return (self.returns / self.amount_invested) * decimal.Decimal('100')
        return decimal.Decimal('0')

    @property
    def is_profitable(self):
        return self.returns > 0

    def __str__(self):
        return f"{self.name} – ₹{self.current_value}"
