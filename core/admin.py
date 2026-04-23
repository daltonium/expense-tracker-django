from django.contrib import admin
from .models import Workspace, Expense, Income, BudgetRule, Investment

@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'mode', 'user', 'created_at']
    list_filter = ['mode']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'category', 'date', 'workspace']
    list_filter = ['category', 'workspace__mode']

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'source', 'date', 'workspace']

@admin.register(BudgetRule)
class BudgetRuleAdmin(admin.ModelAdmin):
    list_display = ['workspace', 'needs_percent', 'wants_percent', 'savings_percent']

@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'asset_type', 'amount_invested', 'current_value', 'status', 'workspace']
    list_filter  = ['asset_type', 'status']