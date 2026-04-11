from django.urls import path
from django.views.generic import RedirectView   # ← built-in Django redirect view
from . import views

urlpatterns = [
    # Redirect root URL to login page
    path('', RedirectView.as_view(url='/login/'), name='home'),
    # RedirectView is a built-in Django class-based view
    # It sends a 302 redirect to whatever url= you give it
    # No need to write a view function for simple redirects

    # Auth URLs
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
]