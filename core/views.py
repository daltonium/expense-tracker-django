from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from .models import Workspace, Expense, Income, BudgetRule
from .forms import ExpenseForm, IncomeForm, BudgetRuleForm
import datetime
import decimal

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'core/login.html', {'error': 'Invalid credentials'})
    return render(request, 'core/login.html', {})

def user_logout(request):
    logout(request)
    return redirect('login')

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html', {})

@login_required
def home(request):
    return render(request, 'core/home.html', {})

@login_required
def home(request):
    workspaces = Workspace.objects.filter(
        user=request.user
    ).annotate(
        total_spent=Sum('expense__amount')
    )
    return render(request, 'core/home.html', {'workspaces': workspaces})

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
            return redirect('home')

    return render(request, 'core/select_mode.html', {})

@login_required
def expense_list(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)
    expenses = Expense.objects.filter(workspace=workspace).order_by('-date')
    total = sum(e.amount for e in expenses)
    return render(request, 'core/expense_list.html', {
        'workspace': workspace,
        'expenses': expenses,
        'total': total,
    })

@login_required
def expense_create(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.workspace = workspace
            expense.save()
            return redirect('expense_list', workspace_id=workspace.id)
    else:
        form = ExpenseForm()

    return render(request, 'core/expense_create.html', {
        'workspace': workspace,
        'form': form,
    })
    
@login_required
def analytics(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)

    # --- Total spending all time ---
    total_all_time = Expense.objects.filter(
        workspace=workspace
    ).aggregate(total=Sum('amount'))['total'] or 0

    # --- This month's spending ---
    today = datetime.date.today()
    total_this_month = Expense.objects.filter(
        workspace=workspace,
        date__year=today.year,
        date__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or 0

    # --- Spending by category ---
    by_category = Expense.objects.filter(
        workspace=workspace
    ).values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    # --- Monthly totals (last 6 months) ---
    monthly_totals = Expense.objects.filter(
        workspace=workspace
    ).values('date__year', 'date__month').annotate(
        total=Sum('amount')
    ).order_by('date__year', 'date__month')

    return render(request, 'core/analytics.html', {
        'workspace': workspace,
        'total_all_time': total_all_time,
        'total_this_month': total_this_month,
        'by_category': by_category,
        'monthly_totals': monthly_totals,
    })

@login_required
def strategy(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)

    # Get or create the budget rule for this workspace
    budget_rule, created = BudgetRule.objects.get_or_create(
        workspace=workspace,
        defaults={'needs_percent': 50, 'wants_percent': 30, 'savings_percent': 20}
    )

    if request.method == 'POST':
        form = BudgetRuleForm(request.POST, instance=budget_rule)
        if form.is_valid():
            form.save()
            return redirect('strategy', workspace_id=workspace.id)
    else:
        form = BudgetRuleForm(instance=budget_rule)

    # Calculate this month's income and expenses
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

    # 50/30/20 allocations based on actual income
    needs_target    = monthly_income * (budget_rule.needs_percent   / 100)
    wants_target    = monthly_income * (budget_rule.wants_percent   / 100)
    savings_target  = monthly_income * (budget_rule.savings_percent / 100)

    # Burn rate: what % of income is being spent
    burn_rate = (
        (monthly_expenses / monthly_income * 100)
        if monthly_income > 0 else decimal.Decimal('0')
    )

    return render(request, 'core/strategy.html', {
        'workspace': workspace,
        'form': form,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'needs_target': needs_target,
        'wants_target': wants_target,
        'savings_target': savings_target,
        'burn_rate': burn_rate,
        'savings_actual': monthly_income - monthly_expenses,
    })

@login_required
def income_create(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id, user=request.user)

    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.workspace = workspace
            income.save()
            return redirect('strategy', workspace_id=workspace.id)
    else:
        form = IncomeForm()

    return render(request, 'core/income_create.html', {
        'workspace': workspace,
        'form': form,
    })
    
@login_required
def dashboard(request):
    today = datetime.date.today()

    # All workspaces for this user, with aggregated totals
    workspaces = Workspace.objects.filter(
        user=request.user
    ).annotate(
        total_expenses=Sum('expense__amount'),
        total_income=Sum('income__amount'),
    )

    # Global totals across ALL workspaces
    global_totals = Workspace.objects.filter(
        user=request.user
    ).aggregate(
        total_expenses=Sum('expense__amount'),
        total_income=Sum('income__amount'),
    )

    global_expenses = global_totals['total_expenses'] or decimal.Decimal('0')
    global_income   = global_totals['total_income']   or decimal.Decimal('0')
    net_worth       = global_income - global_expenses

    # This month across all workspaces
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
    })