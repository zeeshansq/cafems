"""Tokens App – Forms."""
from django import forms
from apps.employees.models import Employee


class TokenIssueForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        widget=forms.Select(attrs={"class": "form-select", "id": "id_token_employee"}),
    )
    token_qty = forms.IntegerField(
        min_value=0, max_value=5, initial=1, required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_token_qty", "min": "0", "max": "5"}),
    )
    extra_roti_qty = forms.IntegerField(
        min_value=0, max_value=10, initial=0, required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_extra_roti", "min": "0", "max": "10"}),
    )
    extra_sweet_qty = forms.IntegerField(
        min_value=0, max_value=10, initial=0, required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "id": "id_extra_sweet", "min": "0", "max": "10"}),
    )
    roti_override = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_roti_override"}),
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["employee"].queryset = Employee.objects.filter(
                tenant=tenant, is_active=True
            ).order_by("full_name")
