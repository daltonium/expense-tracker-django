from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import Workspace

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
    workspaces = Workspace.objects.filter(user=request.user)
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
