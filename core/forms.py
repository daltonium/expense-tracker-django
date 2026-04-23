from django import forms
from .models import Expense, Income, BudgetRule, Investment

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'date', 'note']
        
class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['title', 'amount', 'source', 'date', 'note']

class BudgetRuleForm(forms.ModelForm):
    class Meta:
        model = BudgetRule
        fields = ['needs_percent', 'wants_percent', 'savings_percent']

    def clean(self):
        cleaned_data = super().clean()
        needs = cleaned_data.get('needs_percent') or 0
        wants = cleaned_data.get('wants_percent') or 0
        savings = cleaned_data.get('savings_percent') or 0

        if needs + wants + savings != 100:
            raise forms.ValidationError(
                "Percentages must add up to 100. "
                f"Current total: {needs + wants + savings}"
            )
        return cleaned_data
    
class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = [
            'name', 'asset_type', 'amount_invested',
            'current_value', 'date_invested', 'status', 'note'
        ]

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount_invested')
        current = cleaned_data.get('current_value')

        if amount and current:
            if amount <= 0:
                raise forms.ValidationError(
                    "Amount invested must be greater than zero."
                )
        return cleaned_data
