from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class RegisterForm(UserCreationForm):
    role    = forms.ChoiceField(choices=User.ROLE_CHOICES)
    phone   = forms.CharField(max_length=20, required=False,
                              help_text="Manufacturers: add phone to receive SMS alerts")
    company = forms.CharField(max_length=200, required=False)

    class Meta:
        model  = User
        fields = ["username", "email", "first_name", "last_name",
                  "role", "company", "phone", "password1", "password2"]


class LoginForm(AuthenticationForm):
    pass