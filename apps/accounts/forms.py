"""Accounts App – Forms."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from .models import User


class CafeLoginForm(AuthenticationForm):
    """Custom login form with email field and remember-me."""
    username = forms.EmailField(
        label="Corporate Email Address",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "id": "id_email",
            "placeholder": "name@company.com",
            "autocomplete": "email",
        }),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "id": "id_password",
            "placeholder": "••••••••••••",
            "autocomplete": "current-password",
        }),
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_remember_me"}),
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "avatar"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "id": "id_first_name"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "id": "id_last_name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "id": "id_email_profile"}),
            "avatar": forms.FileInput(attrs={"class": "form-control", "id": "id_avatar", "accept": "image/*"}),
        }


class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "id": "id_old_password", "autocomplete": "current-password"}),
    )
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "id": "id_new_password1"}),
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "id": "id_new_password2"}),
    )
