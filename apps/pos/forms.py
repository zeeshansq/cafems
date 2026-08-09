"""POS App – Forms."""
from django import forms
from .models import TeaItemSale, PaymentMethod


class SaleForm(forms.ModelForm):
    class Meta:
        model = TeaItemSale
        fields = ["item", "quantity", "amount_paid", "payment_method", "buyer", "note"]
        widgets = {
            "item": forms.Select(attrs={"class": "form-select", "id": "id_sale_item"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "id": "id_sale_qty", "min": "1"}),
            "amount_paid": forms.NumberInput(attrs={"class": "form-control", "id": "id_amount_paid", "step": "0.01"}),
            "payment_method": forms.Select(attrs={"class": "form-select", "id": "id_payment_method"}),
            "buyer": forms.Select(attrs={"class": "form-select", "id": "id_buyer"}),
            "note": forms.TextInput(attrs={"class": "form-control", "id": "id_sale_note"}),
        }
