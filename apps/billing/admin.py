"""Billing Admin."""
from django.contrib import admin
from .models import MonthlyBill, MiscCharge, Payment


@admin.register(MonthlyBill)
class MonthlyBillAdmin(admin.ModelAdmin):
    list_display = ["employee", "period_start", "period_end", "token_total", "misc_charges_total", "total", "status", "tenant"]
    list_filter = ["status", "period_start", "tenant"]
    search_fields = ["employee__full_name"]


@admin.register(MiscCharge)
class MiscChargeAdmin(admin.ModelAdmin):
    list_display = ["month", "amount", "description", "tenant"]
    list_filter = ["month", "tenant"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["bill", "amount_paid", "payment_date", "method", "received_by"]
    list_filter = ["method", "payment_date"]
