"""Employees App – Forms."""
from django import forms
from .models import Employee, Department


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "full_name", "photo", "pno", "register_number", "system_id",
            "email", "mobile", "telephone_extension", "gender",
            "designation", "category", "department",
            "membership_status", "membership_type",
            "security_deposit_paid", "security_deposit_pending",
            "date_joined", "is_active", "notes",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "id": "id_full_name"}),
            "photo": forms.FileInput(attrs={"class": "form-control", "id": "id_photo", "accept": "image/*"}),
            "pno": forms.TextInput(attrs={"class": "form-control", "id": "id_pno"}),
            "register_number": forms.TextInput(attrs={"class": "form-control", "id": "id_register_number"}),
            "system_id": forms.TextInput(attrs={"class": "form-control", "id": "id_system_id"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "id": "id_emp_email"}),
            "mobile": forms.TextInput(attrs={"class": "form-control", "id": "id_mobile"}),
            "telephone_extension": forms.TextInput(attrs={"class": "form-control", "id": "id_tel_ext"}),
            "gender": forms.Select(attrs={"class": "form-select", "id": "id_gender"}),
            "designation": forms.TextInput(attrs={"class": "form-control", "id": "id_designation"}),
            "category": forms.Select(attrs={"class": "form-select", "id": "id_category"}),
            "department": forms.Select(attrs={"class": "form-select", "id": "id_department"}),
            "membership_status": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_membership_status"}),
            "membership_type": forms.Select(attrs={"class": "form-select", "id": "id_membership_type"}),
            "security_deposit_paid": forms.NumberInput(attrs={"class": "form-control", "id": "id_deposit_paid", "step": "0.01"}),
            "security_deposit_pending": forms.NumberInput(attrs={"class": "form-control", "id": "id_deposit_pending", "step": "0.01"}),
            "date_joined": forms.DateInput(attrs={"class": "form-control", "id": "id_date_joined", "type": "date"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_is_active"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "id": "id_notes", "rows": 3}),
        }
