"""Billing App – Forms."""
from django import forms
from .models import MiscCharge, Payment


class MiscChargeForm(forms.ModelForm):
    class Meta:
        model = MiscCharge
        fields = ["month", "amount", "description"]
        widgets = {
            "month": forms.DateInput(attrs={"class": "form-control", "id": "id_misc_month", "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "id": "id_misc_amount", "step": "0.01"}),
            "description": forms.TextInput(attrs={"class": "form-control", "id": "id_misc_desc"}),
        }


from django.utils import timezone

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount_paid", "payment_date", "reference", "note"]
        widgets = {
            "amount_paid": forms.NumberInput(attrs={"class": "form-control", "id": "id_pay_amount", "step": "0.01"}),
            "payment_date": forms.DateInput(attrs={"class": "form-control", "id": "id_pay_date", "type": "date"}),
            "reference": forms.TextInput(attrs={"class": "form-control", "id": "id_pay_ref", "placeholder": "Receipt / Voucher # (Optional)"}),
            "note": forms.Textarea(attrs={"class": "form-control", "id": "id_pay_note", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get("payment_date"):
            self.initial["payment_date"] = timezone.localdate().strftime("%Y-%m-%d")
