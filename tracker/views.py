from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
# login()        → creates a session (logs the user in)
# logout()       → destroys the session (logs the user out)
# authenticate() → checks username + password, returns User or None

from django.contrib.auth.decorators import login_required
# @login_required → a decorator that protects views
# If the user is NOT logged in, they get redirected to the login page
# If they ARE logged in, the view runs normally

from django.contrib import messages
# messages → Django's "flash message" system
# A flash message is shown ONCE on the next page, then disappears
# Like: "Login successful!" or "Invalid password"

from .forms import RegisterForm


def register_view(request):
    """
    One function handles BOTH showing the form (GET) 
    AND processing the submitted form (POST).
    
    This GET/POST pattern is the standard Django way.
    """
    if request.method == 'POST':
        # User clicked "Submit" — data came in via request.POST
        # We "bind" the form: pass POST data into it for validation
        form = RegisterForm(request.POST)

        if form.is_valid():
            # is_valid() runs ALL validators at once:
            # ✓ Are required fields filled?
            # ✓ Does password meet strength requirements?
            # ✓ Do password1 and password2 match?
            # ✓ Is the email format valid?
            # ✓ Is the username already taken?

            user = form.save()
            # form.save() calls User.objects.create_user() internally
            # create_user() HASHES the password using PBKDF2 before storing
            # The DB NEVER stores plain text passwords — always a hash like:
            # "pbkdf2_sha256$720000$abc123$xHk9..."

            login(request, user)
            # login() does two things:
            # 1. Creates a row in django_session table in PostgreSQL
            # 2. Sends a "sessionid" cookie to the user's browser
            # On every future request, Django reads that cookie,
            # looks up the session row, and knows who the user is

            messages.success(request, f"Welcome, {user.username}! Account created.")
            # success, error, warning, info → different message levels
            # These show up in the template via {% for message in messages %}

            return redirect('dashboard')
            # redirect() sends HTTP 302 response
            # 'dashboard' is the URL name (from urls.py name='dashboard')
            # Django converts it to the actual URL — never hardcode '/dashboard/'

    else:
        # GET request → user just visited the page
        # Show a clean empty form
        form = RegisterForm()

    # render() does three things:
    # 1. Loads the template file
    # 2. Injects the context variables into it
    # 3. Returns an HTTP response with the rendered HTML
    return render(request, 'tracker/register.html', {'form': form})


def login_view(request):
    # If the user is already logged in, don't show them the login page
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # request.POST is a dict-like object of form data
        # .get() is safer than ['key'] — returns None instead of KeyError

        user = authenticate(request, username=username, password=password)
        # authenticate() does the following:
        # 1. Looks up the user by username in the DB
        # 2. Hashes the submitted password with the same algorithm
        # 3. Compares the hash to the stored hash
        # 4. Returns the User object if they match, or None if they don't
        # ✅ You NEVER compare plain-text passwords directly

        if user is not None:
            login(request, user)

            # "next" is a URL parameter Django adds automatically
            # When a logged-out user tries to visit /dashboard/,
            # Django redirects them to: /login/?next=/dashboard/
            # After login, we send them back to where they wanted to go
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
            # We deliberately don't say WHICH one is wrong
            # Telling "username doesn't exist" helps attackers enumerate users

    return render(request, 'tracker/login.html')


def logout_view(request):
    """
    Logout should ALWAYS be a POST request (via a form with CSRF token).
    Never a GET request like <a href="/logout/"> — that's a security risk
    because a malicious site could embed <img src="/logout/"> and log you out.
    """
    if request.method == 'POST':
        logout(request)
        # logout() deletes the session row from django_session table
        # The browser's sessionid cookie becomes invalid
        messages.success(request, "You've been logged out.")
    return redirect('login')


@login_required
# This decorator is the gatekeeper for the dashboard
# Place it above ANY view that requires authentication
# If not logged in → redirects to settings.LOGIN_URL (which we set to '/login/')
def dashboard_view(request):
    """
    Placeholder dashboard — will be fully built in Phase 3.
    For now, just confirms authentication is working.
    """
    return render(request, 'tracker/dashboard.html')