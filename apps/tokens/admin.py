"""Tokens Admin."""
from django.contrib import admin
from .models import LunchToken


@admin.register(LunchToken)
class LunchTokenAdmin(admin.ModelAdmin):
    list_display = ["date", "token_number", "employee", "status", "roti_override", "issued_by", "tenant"]
    list_filter = ["date", "status", "roti_override", "tenant"]
    search_fields = ["employee__full_name", "employee__pno"]
