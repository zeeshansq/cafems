"""Requests App – Forms."""
from django import forms
from django.core.exceptions import ValidationError
from .models import TokenOpenCloseRequest, RequestType


class RequestForm(forms.ModelForm):
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = TokenOpenCloseRequest
        fields = ["request_type", "requested_token_qty", "date_range_start", "date_range_end", "reason"]
        widgets = {
            "request_type": forms.Select(attrs={"class": "form-select", "id": "id_request_type"}),
            "requested_token_qty": forms.NumberInput(attrs={"class": "form-control", "id": "id_req_token_qty", "min": "1", "max": "5"}),
            "date_range_start": forms.DateInput(attrs={"class": "form-control", "id": "id_date_start", "type": "date"}),
            "date_range_end": forms.DateInput(attrs={"class": "form-control", "id": "id_date_end", "type": "date"}),
            "reason": forms.Textarea(attrs={"class": "form-control", "id": "id_reason", "rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("date_range_start")
        end = cleaned_data.get("date_range_end")

        if start and end and end < start:
            raise ValidationError("End date must be on or after start date.")

        from apps.core.utils import is_before_cutoff
        if start and not is_before_cutoff(start):
            raise ValidationError(
                "Request must be submitted at least 1 day before the start date, by 2:00 PM Pakistan Standard Time."
            )

        return cleaned_data


class RequestAcknowledgeForm(forms.Form):
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "id": "id_ack_note", "rows": 2}),
        label="Internal note (optional)",
    )
