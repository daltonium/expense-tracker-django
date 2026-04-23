from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from .models import Workspace, Expense
from .forms import ExpenseForm
import datetime

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
