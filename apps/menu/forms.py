"""Menu App – Forms."""
from django import forms
from .models import TeaItem, LunchMenuPlan, DailyLunchEstimate, MenuCategory, Cook, Sweet, RotiPrice


class TeaItemForm(forms.ModelForm):
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["category"].queryset = MenuCategory.objects.filter(tenant=tenant)

    class Meta:
        model = TeaItem
        fields = ["name", "category", "price", "image", "description", "is_available", "sort_order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "id": "id_item_name"}),
            "category": forms.Select(attrs={"class": "form-select", "id": "id_item_category"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "id": "id_item_price", "step": "0.01"}),
            "image": forms.FileInput(attrs={"class": "form-control", "id": "id_item_image", "accept": "image/*"}),
            "description": forms.Textarea(attrs={"class": "form-control", "id": "id_item_desc", "rows": 2}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_item_available"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control", "id": "id_item_order"}),
        }


class LunchMenuPlanForm(forms.ModelForm):
    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["cook"].queryset = Cook.objects.filter(tenant=tenant, is_active=True)
            self.fields["sweet"].queryset = Sweet.objects.filter(tenant=tenant, is_active=True)
            self.fields["roti_price_obj"].queryset = RotiPrice.objects.filter(tenant=tenant, is_active=True)

    class Meta:
        model = LunchMenuPlan
        fields = [
            "week_of_month", "day_of_week", "dish_name", "description",
            "cook", "roti_price_obj", "sweet", "contains_sweet", "is_published"
        ]
        widgets = {
            "week_of_month": forms.Select(attrs={"class": "form-select", "id": "id_week"}),
            "day_of_week": forms.Select(attrs={"class": "form-select", "id": "id_day"}),
            "dish_name": forms.TextInput(attrs={"class": "form-control", "id": "id_dish_name", "placeholder": "e.g. Beef Haleem with Rice"}),
            "description": forms.Textarea(attrs={"class": "form-control", "id": "id_dish_desc", "rows": 2, "placeholder": "Ingredients, specials, or serving notes..."}),
            "cook": forms.Select(attrs={"class": "form-select", "id": "id_cook"}),
            "roti_price_obj": forms.Select(attrs={"class": "form-select", "id": "id_roti_price_obj"}),
            "sweet": forms.Select(attrs={"class": "form-select", "id": "id_sweet"}),
            "contains_sweet": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_contains_sweet"}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_is_published"}),
        }


class DailyLunchEstimateForm(forms.ModelForm):
    dish_select = forms.ChoiceField(required=False, widget=forms.Select(attrs={"class": "form-select mb-1", "id": "id_dish_select"}))

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["cook"].queryset = Cook.objects.filter(tenant=tenant, is_active=True)
            self.fields["sweet"].queryset = Sweet.objects.filter(tenant=tenant, is_active=True)
            self.fields["roti_price_obj"].queryset = RotiPrice.objects.filter(tenant=tenant, is_active=True)
            
            # Populate unique dish choices from LunchMenuPlan catalog
            plans = LunchMenuPlan.objects.filter(tenant=tenant).values_list("dish_name", flat=True).distinct()
            dish_choices = [("", "— Select from Dish Catalog (or enter below) —")] + [(d, d) for d in plans if d]
            self.fields["dish_select"].choices = dish_choices

    class Meta:
        model = DailyLunchEstimate
        fields = [
            "date", "dish_name", "cook", "roti_price_obj", "roti_type", "sweet",
            "planned_count", "actual_tokens_issued",
            "estimated_extra_roti", "actual_extra_roti_issued", "roti_unit_price",
            "estimated_extra_sweet", "actual_extra_sweet_issued", "sweet_unit_price",
            "total_expense", "adjustment_amount", "token_expense", "price_per_token"
        ]
        widgets = {
            "date": forms.DateInput(attrs={"class": "form-control", "id": "id_est_date", "type": "date"}),
            "dish_name": forms.TextInput(attrs={"class": "form-control", "id": "id_dish_name", "placeholder": "Enter dish name or choose from dropdown above"}),
            "cook": forms.Select(attrs={"class": "form-select", "id": "id_cook"}),
            "roti_price_obj": forms.Select(attrs={"class": "form-select", "id": "id_roti_price_obj"}),
            "roti_type": forms.HiddenInput(attrs={"id": "id_roti_type"}),
            "sweet": forms.Select(attrs={"class": "form-select", "id": "id_sweet"}),

            "planned_count": forms.NumberInput(attrs={"class": "form-control", "id": "id_planned_count", "min": "0"}),
            "actual_tokens_issued": forms.NumberInput(attrs={"class": "form-control bg-light", "id": "id_actual_tokens_issued", "readonly": "readonly"}),

            "estimated_extra_roti": forms.NumberInput(attrs={"class": "form-control", "id": "id_estimated_extra_roti", "min": "0"}),
            "actual_extra_roti_issued": forms.NumberInput(attrs={"class": "form-control bg-light", "id": "id_actual_extra_roti_issued", "readonly": "readonly"}),
            "roti_unit_price": forms.NumberInput(attrs={"class": "form-control bg-light", "id": "id_roti_unit_price", "step": "0.01", "readonly": "readonly"}),

            "estimated_extra_sweet": forms.NumberInput(attrs={"class": "form-control", "id": "id_estimated_extra_sweet", "min": "0"}),
            "actual_extra_sweet_issued": forms.NumberInput(attrs={"class": "form-control bg-light", "id": "id_actual_extra_sweet_issued", "readonly": "readonly"}),
            "sweet_unit_price": forms.NumberInput(attrs={"class": "form-control bg-light", "id": "id_sweet_unit_price", "step": "0.01", "readonly": "readonly"}),

            "total_expense": forms.NumberInput(attrs={"class": "form-control", "id": "id_total_expense", "step": "0.01", "min": "0"}),
            "adjustment_amount": forms.NumberInput(attrs={"class": "form-control", "id": "id_adjustment_amount", "step": "0.01", "placeholder": "0.00 (+/- adjustment)"}),

            "token_expense": forms.NumberInput(attrs={"class": "form-control bg-light fw-bold", "id": "id_token_expense", "step": "0.01", "readonly": "readonly"}),
            "price_per_token": forms.NumberInput(attrs={"class": "form-control bg-light fw-bold text-primary", "id": "id_price_per_token", "step": "0.01", "readonly": "readonly"}),
        }


class CookForm(forms.ModelForm):
    class Meta:
        model = Cook
        fields = ["name", "phone", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "id": "id_cook_name", "placeholder": "e.g., Chef Umer"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "id": "id_cook_phone", "placeholder": "e.g., 0300-1234567"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_cook_active"}),
        }


class SweetForm(forms.ModelForm):
    class Meta:
        model = Sweet
        fields = ["name", "price", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "id": "id_sweet_name", "placeholder": "e.g., Gulab Jamun"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "id": "id_sweet_price", "step": "0.01", "min": "0"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_sweet_active"}),
        }


class RotiPriceForm(forms.ModelForm):
    class Meta:
        model = RotiPrice
        fields = ["name", "price", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "id": "id_roti_name", "placeholder": "e.g., Standard Roti, Tandoori Naan, Khamiri Roti"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "id": "id_roti_price_val", "step": "0.01", "min": "0"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_roti_active"}),
        }



