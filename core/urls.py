from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('select-mode/', views.select_mode, name='select_mode'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('workspace/<int:workspace_id>/expenses/', views.expense_list, name='expense_list'),
    path('workspace/<int:workspace_id>/expenses/add/', views.expense_create, name='expense_create'),
    path('workspace/<int:workspace_id>/income/add/', views.income_create, name='income_create'),
    path('workspace/<int:workspace_id>/analytics/', views.analytics, name='analytics'),
    path('workspace/<int:workspace_id>/strategy/', views.strategy, name='strategy'),
]