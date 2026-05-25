from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


# class RegisterForm(UserCreationForm):
#     role    = forms.ChoiceField(choices=User.ROLE_CHOICES)
#     phone   = forms.CharField(max_length=20, required=False,
#                               help_text="Manufacturers: add phone to receive SMS alerts")
#     company = forms.CharField(max_length=200, required=False)

#     class Meta:
#         model  = User
#         fields = ["username", "email", "first_name", "last_name",
#                   "role", "company", "phone", "password1", "password2"]


class LoginForm(AuthenticationForm):
    pass

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class ManufacturerRegisterForm(UserCreationForm):
    company_name = forms.CharField(max_length=200)
    phone = forms.CharField(max_length=20)
    class Meta:
        model = User
        fields = ['username', 'email', 'company_name', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'MANUFACTURER'
        user.company_name = self.cleaned_data['company_name']
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return user

class DistributorRegisterForm(UserCreationForm):
    company_name = forms.CharField(max_length=200)
    phone = forms.CharField(max_length=20)
    class Meta:
        model = User
        fields = ['username', 'email', 'company_name', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'DISTRIBUTOR'
        user.company_name = self.cleaned_data['company_name']
        user.phone = self.cleaned_data['phone']
        if commit:
            user.save()
        return user

class CustomerRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'CUSTOMER'
        if commit:
            user.save()
        return user