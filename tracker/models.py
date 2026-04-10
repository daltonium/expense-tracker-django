from django.db import models
from django.contrib.auth.models import User
# User is Django's built-in model with: username, email, password, is_staff, etc.
# We import it to link our data to specific users

class Category(models.Model):
    """
    Represents a spending category like 'Food', 'Rent', 'Entertainment'.
    Kept separate so users can create their own custom categories.
    """
    # ForeignKey = Many-to-One relationship
    # Each category belongs to ONE user; one user can have MANY categories
    # on_delete=CASCADE → if user is deleted, their categories are also deleted
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    # CharField = a short text field stored as VARCHAR in PostgreSQL
    # max_length is REQUIRED for CharField — sets column size in the DB

    # CHOICES: restricts the value to a defined set
    # Stored as 'income' or 'expense' in DB, displayed as 'Income'/'Expense' in forms
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    category_type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    icon = models.CharField(max_length=50, blank=True, default='💰')
    # blank=True → this field is optional in forms (but DB stores empty string if not given)

    class Meta:
        # unique_together = PostgreSQL enforces that (user + name) combo must be unique
        # So "Food" for User1 and "Food" for User2 are both allowed
        # But User1 can't have two "Food" categories
        unique_together = ['user', 'name']
        ordering = ['name']  # Default sort: alphabetical by name

    def __str__(self):
        # This controls what shows in Django Admin and dropdowns
        return f"{self.name} ({self.category_type})"


class Transaction(models.Model):
    """
    The core model. Each row = one income or expense entry.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # related_name='transactions' → lets you do user.transactions.all()
    # instead of the default user.transaction_set.all()

    # ForeignKey to Category — each transaction belongs to ONE category
    # on_delete=SET_NULL → if category is deleted, transaction stays but category = null
    # null=True allows NULL in the PostgreSQL column
    # blank=True allows empty in Django forms
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )

    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    # DecimalField is used for money — NEVER use FloatField for currency!
    # FloatField has floating-point precision errors (0.1 + 0.2 ≠ 0.3)
    # DecimalField stores exact values using PostgreSQL's NUMERIC type
    # max_digits=10 → total digits (including decimals)
    # decimal_places=2 → two digits after decimal point (e.g., 9999999.99)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    description = models.TextField(blank=True)
    # TextField → unlimited length text, stored as TEXT in PostgreSQL
    # CharFeld → fixed-length VARCHAR

    # DateField stores only the date (no time) → DATE in PostgreSQL
    # Using date here (not datetime) because a user picks "June 5" not a timestamp
    date = models.DateField()

    # auto_now_add=True → automatically sets this to NOW() when row is INSERTED
    # This is different from 'date' — this records when the record was created in system
    created_at = models.DateTimeField(auto_now_add=True)

    # auto_now=True → automatically updates this to NOW() on every SAVE (UPDATE)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        # Minus sign (-) = DESCENDING order
        # Latest transactions appear first

    def __str__(self):
        return f"{self.transaction_type}: ₹{self.amount} on {self.date}"