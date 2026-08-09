"""Tenants App – Forms."""
from django import forms
from django.utils.text import slugify
from .models import Tenant


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = [
            "title", "short_title", "slug", "logo", "contact_email",
            "contact_phone", "address", "currency", "timezone",
            "max_tokens_per_day", "status",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "id": "id_title"}),
            "short_title": forms.TextInput(attrs={"class": "form-control", "id": "id_short_title"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "id": "id_slug"}),
            "logo": forms.FileInput(attrs={"class": "form-control", "id": "id_logo", "accept": "image/*"}),
            "contact_email": forms.EmailInput(attrs={"class": "form-control", "id": "id_contact_email"}),
            "contact_phone": forms.TextInput(attrs={"class": "form-control", "id": "id_contact_phone"}),
            "address": forms.Textarea(attrs={"class": "form-control", "id": "id_address", "rows": 3}),
            "currency": forms.TextInput(attrs={"class": "form-control", "id": "id_currency"}),
            "timezone": forms.Select(attrs={"class": "form-select", "id": "id_timezone"}),
            "max_tokens_per_day": forms.NumberInput(attrs={"class": "form-control", "id": "id_max_tokens_per_day", "min": 1, "max": 10}),
            "status": forms.Select(attrs={"class": "form-select", "id": "id_status"}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"]
        if not self.instance.pk and not self.cleaned_data.get("slug"):
            self.instance._auto_slug = slugify(title)
        return title

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if logo and hasattr(logo, "content_type"):
            from apps.core.utils import validate_file_upload
            try:
                validate_file_upload(logo)
            except ValueError as e:
                raise forms.ValidationError(str(e))
        return logo
