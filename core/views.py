from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.conf import settings

from django.db.models import Sum, Count, Avg
from django.utils import timezone

from .models import Workspace, Expense, Income, BudgetRule, Investment
from .forms import ExpenseForm, IncomeForm, BudgetRuleForm, InvestmentForm

import datetime
import decimal

import cohere


# ─────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html', {})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('select_mode')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'core/login.html', {'error': 'Invalid credentials'})
    return render(request, 'core/login.html', {})


def user_logout(request):
    logout(request)
    return redirect('login')


# ─────────────────────────────────────────
# WORKSPACE SETUP
# ─────────────────────────────────────────

@login_required
def select_mode(request):
    if request.method == 'POST':
        mode = request.POST.get('mode')
        name = request.POST.get('name')
        if mode in ['personal', 'company'] and name:
            Workspace.objects.create(
                user=request.user,
                name=name,
                mode=mode
            )
            return redirect('dashboard')
    return render(request, 'core/select_mode.html', {})


# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────

@login_required
def dashboard(request):
    today = datetime.date.today()

    workspaces = Workspace.objects.filter(
        user=request.user
    ).annotate(
        total_expenses=Sum('expense__amount'),
        total_income=Sum('income__amount'),
        total_invested=Sum('investment__amount_invested'),
        total_portfolio=Sum('investment__current_value'),
    )

    global_totals = Workspace.objects.filter(
        user=request.user
    ).aggregate(
        total_expenses=Sum('expense__amount'),
        total_income=Sum('income__amount'),
        total_invested=Sum('investment__amount_invested'),
        total_portfolio=Sum('investment__current_value'),
    )

    global_expenses = global_totals['total_expenses'] or decimal.Decimal('0')
    global_income   = global_totals['total_income']   or decimal.Decimal('0')
    total_invested  = global_totals['total_invested']  or decimal.Decimal('0')
    total_portfolio = global_totals['total_portfolio'] or decimal.Decimal('0')
    net_worth       = global_income - global_expenses + total_portfolio

    monthly_expenses = Expense.objects.filter(
        workspace__user=request.user,
        date__year=today.year,
        date__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0')

    monthly_income = Income.objects.filter(
        workspace__user=request.user,
        date__year=today.year,
        date__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0')

    return render(request, 'core/dashboard.html', {
        'workspaces': workspaces,
        'net_worth': net_worth,
        'global_expenses': global_expenses,
        'global_income': global_income,
        'monthly_expenses': monthly_expenses,
        'monthly_income': monthly_income,
        'total_portfolio': total_portfolio,
    })


# ─────────────────────────────────────────
# EXPENSES
# ─────────────────────────────────────────

@login_required
def expense_list(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)
    expenses  = Expense.objects.filter(workspace=workspace).order_by('-date')
    total     = expenses.aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0')
    return render(request, 'core/expense_list.html', {
        'workspace': workspace,
        'expenses':  expenses,
        'total':     total,
    })


@login_required
def expense_create(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense           = form.save(commit=False)
            expense.workspace = workspace
            expense.save()
            return redirect('expense_list', workspace_id=workspace.id)
    else:
        form = ExpenseForm()

    return render(request, 'core/expense_create.html', {
        'workspace': workspace,
        'form':      form,
    })


# ─────────────────────────────────────────
# INCOME
# ─────────────────────────────────────────

@login_required
def income_create(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)

    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income           = form.save(commit=False)
            income.workspace = workspace
            income.save()
            return redirect('strategy', workspace_id=workspace.id)
    else:
        form = IncomeForm()

    return render(request, 'core/income_create.html', {
        'workspace': workspace,
        'form':      form,
    })


# ─────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────

@login_required
def analytics(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)
    today     = datetime.date.today()

    total_all_time = Expense.objects.filter(
        workspace=workspace
    ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0')

    total_this_month = Expense.objects.filter(
        workspace=workspace,
        date__year=today.year,
        date__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0')

    by_category = Expense.objects.filter(
        workspace=workspace
    ).values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    monthly_totals = Expense.objects.filter(
        workspace=workspace
    ).values('date__year', 'date__month').annotate(
        total=Sum('amount')
    ).order_by('date__year', 'date__month')

    return render(request, 'core/analytics.html', {
        'workspace':       workspace,
        'total_all_time':  total_all_time,
        'total_this_month': total_this_month,
        'by_category':     by_category,
        'monthly_totals':  monthly_totals,
    })


# ─────────────────────────────────────────
# STRATEGY (50/30/20)
# ─────────────────────────────────────────

@login_required
def strategy(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)

    budget_rule, _ = BudgetRule.objects.get_or_create(
        workspace=workspace,
        defaults={
            'needs_percent':   50,
            'wants_percent':   30,
            'savings_percent': 20,
        }
    )

    if request.method == 'POST':
        form = BudgetRuleForm(request.POST, instance=budget_rule)
        if form.is_valid():
            form.save()
            return redirect('strategy', workspace_id=workspace.id)
    else:
        form = BudgetRuleForm(instance=budget_rule)

    today = datetime.date.today()

    monthly_income = Income.objects.filter(
        workspace=workspace,
        date__year=today.year,
        date__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0')

    monthly_expenses = Expense.objects.filter(
        workspace=workspace,
        date__year=today.year,
        date__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0')

    needs_target   = monthly_income * (budget_rule.needs_percent   / decimal.Decimal(100))
    wants_target   = monthly_income * (budget_rule.wants_percent   / decimal.Decimal(100))
    savings_target = monthly_income * (budget_rule.savings_percent / decimal.Decimal(100))

    burn_rate = (
        (monthly_expenses / monthly_income * 100)
        if monthly_income > 0 else decimal.Decimal('0')
    )

    return render(request, 'core/strategy.html', {
        'workspace':        workspace,
        'form':             form,
        'monthly_income':   monthly_income,
        'monthly_expenses': monthly_expenses,
        'needs_target':     needs_target,
        'wants_target':     wants_target,
        'savings_target':   savings_target,
        'burn_rate':        burn_rate,
        'savings_actual':   monthly_income - monthly_expenses,
    })


# ─────────────────────────────────────────
# GROW (INVESTMENTS)
# ─────────────────────────────────────────

@login_required
def grow(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)

    investments = Investment.objects.filter(
        workspace=workspace
    ).order_by('-date_invested')

    totals = investments.aggregate(
        total_invested=Sum('amount_invested'),
        total_current=Sum('current_value'),
    )

    total_invested       = totals['total_invested'] or decimal.Decimal('0')
    total_current        = totals['total_current']  or decimal.Decimal('0')
    total_returns        = total_current - total_invested
    portfolio_return_pct = (
        (total_returns / total_invested * 100)
        if total_invested > 0 else decimal.Decimal('0')
    )

    by_asset = investments.values('asset_type').annotate(
        invested=Sum('amount_invested'),
        current=Sum('current_value'),
    ).order_by('-current')

    return render(request, 'core/grow.html', {
        'workspace':           workspace,
        'investments':         investments,
        'total_invested':      total_invested,
        'total_current':       total_current,
        'total_returns':       total_returns,
        'portfolio_return_pct': portfolio_return_pct,
        'by_asset':            by_asset,
    })


@login_required
def investment_create(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)

    if request.method == 'POST':
        form = InvestmentForm(request.POST)
        if form.is_valid():
            investment           = form.save(commit=False)
            investment.workspace = workspace
            investment.save()
            return redirect('grow', workspace_id=workspace.id)
    else:
        form = InvestmentForm()

    return render(request, 'core/investment_create.html', {
        'workspace': workspace,
        'form':      form,
    })


@login_required
def investment_update(request, workspace_id, investment_id):
    workspace  = get_object_or_404(Workspace, id=workspace_id, user=request.user)
    investment = get_object_or_404(Investment, id=investment_id, workspace=workspace)

    if request.method == 'POST':
        form = InvestmentForm(request.POST, instance=investment)
        if form.is_valid():
            form.save()
            return redirect('grow', workspace_id=workspace.id)
    else:
        form = InvestmentForm(instance=investment)

    return render(request, 'core/investment_create.html', {
        'workspace':  workspace,
        'form':       form,
        'investment': investment,
    })


# ─────────────────────────────────────────
# AI CHATBOT
# ─────────────────────────────────────────

@login_required
def chatbot(request, workspace_id):
    workspace     = get_object_or_404(Workspace, id=workspace_id, user=request.user)
    response_text = None
    user_message  = None

    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()

        if user_message:
            today = datetime.date.today()

            monthly_income = Income.objects.filter(
                workspace=workspace,
                date__year=today.year,
                date__month=today.month,
            ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0')

            monthly_expenses = Expense.objects.filter(
                workspace=workspace,
                date__year=today.year,
                date__month=today.month,
            ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0')

            by_category = Expense.objects.filter(
                workspace=workspace,
                date__year=today.year,
                date__month=today.month,
            ).values('category').annotate(
                total=Sum('amount')
            ).order_by('-total')

            savings   = monthly_income - monthly_expenses
            burn_rate = (
                (monthly_expenses / monthly_income * 100)
                if monthly_income > 0 else decimal.Decimal('0')
            )

            category_lines = '\n'.join([
                f"  - {row['category']}: ₹{row['total']}"
                for row in by_category
            ])

            if workspace.mode == 'personal':
                persona = (
                    "You are a caring, empathetic personal finance advisor. "
                    "If the user is overspending, gently guide them. "
                    "If they are doing well, congratulate and encourage them. "
                    "Keep responses concise, warm, and actionable."
                )
            else:
                persona = (
                    "You are a strategic AI CFO for a company. "
                    "Analyze financial data professionally. "
                    "Give precise, data-driven advice on cost control, "
                    "revenue growth, and financial health. "
                    "Keep responses concise and business-focused."
                )

            financial_context = f"""
Current workspace: {workspace.name} ({workspace.mode} mode)
This month's data:
  - Income:    ₹{monthly_income}
  - Expenses:  ₹{monthly_expenses}
  - Savings:   ₹{savings}
  - Burn rate: {burn_rate:.1f}% of income spent

Expense breakdown by category:
{category_lines if category_lines else '  No expenses recorded yet.'}

User's question: {user_message}
"""

            try:
                co     = cohere.ClientV2(api_key=settings.COHERE_API_KEY)
                result = co.chat(
                    model='command-r-plus',
                    messages=[
                        {'role': 'system', 'content': persona},
                        {'role': 'user',   'content': financial_context},
                    ]
                )
                response_text = result.message.content[0].text

            except Exception as e:
                response_text = f"Sorry, I couldn't connect right now. Please try again. (Error: {e})"

    return render(request, 'core/chatbot.html', {
        'workspace':    workspace,
        'user_message': user_message,
        'response_text': response_text,
    })