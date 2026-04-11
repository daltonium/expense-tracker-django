from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    """
    UserCreationForm is Django's built-in registration form.
    It already gives you:
      - username field
      - password field (with strength rules)
      - password confirmation field
      - all validators (password match, length, etc.)
    
    We EXTEND it (inheritance) to add one extra field: email.
    """
    email = forms.EmailField(required=True)
    # EmailField automatically validates "user@example.com" format
    # required=True means the form won't submit without it

    class Meta:
        """
        Meta class tells Django which model this form is tied to
        and which fields to include.
        """
        model = User
        # model = User → form.save() will create a User object in the DB
        
        fields = ['username', 'email', 'password1', 'password2']
        # password1 = "Enter password"
        # password2 = "Confirm password"
        # We exclude fields like is_staff, is_superuser — users shouldn't set those!