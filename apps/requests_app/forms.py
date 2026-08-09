"""Requests App – Forms."""
from django import forms
from django.core.exceptions import ValidationError
from .models import TokenOpenCloseRequest, RequestType


class RequestForm(forms.ModelForm):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "id": "id_reason",
            "rows": 3,
            "placeholder": "Provide a clear reason for your request (e.g. Annual leave, official duty, remote training)...",
            "required": "required",
        }),
        required=True,
        label="Reason (Required)",
        help_text="Please provide a clear justification for auditing purposes.",
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reason"].required = True

    class Meta:
        model = TokenOpenCloseRequest
        fields = ["request_type", "requested_token_qty", "date_range_start", "date_range_end", "reason"]
        widgets = {
            "request_type": forms.Select(attrs={"class": "form-select", "id": "id_request_type", "@change": "toggleTokenQtyField()"}),
            "requested_token_qty": forms.NumberInput(attrs={"class": "form-control", "id": "id_req_token_qty", "min": "1", "max": "3"}),
            "date_range_start": forms.DateInput(attrs={"class": "form-control", "id": "id_date_start", "type": "date"}),
            "date_range_end": forms.DateInput(attrs={"class": "form-control", "id": "id_date_end", "type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        req_type = cleaned_data.get("request_type")
        start = cleaned_data.get("date_range_start")
        end = cleaned_data.get("date_range_end")
        qty = cleaned_data.get("requested_token_qty")
        reason = cleaned_data.get("reason", "").strip()

        if not reason:
            self.add_error("reason", "Reason is required for all open/close requests.")

        if req_type == RequestType.OPEN:
            if qty and (qty < 1 or qty > 3):
                self.add_error("requested_token_qty", "Requested token quantity must be between 1 and 3 tokens.")
        elif req_type == RequestType.CLOSE:
            cleaned_data["requested_token_qty"] = 1  # Default fallback for close

        if start and end and end < start:
            self.add_error("date_range_end", "End date must be on or after start date.")

        return cleaned_data


class RequestAcknowledgeForm(forms.Form):
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "id": "id_ack_note", "rows": 2}),
        label="Internal note (optional)",
    )
