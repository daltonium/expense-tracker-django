from django.db import models
from django.contrib.auth.models import User

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