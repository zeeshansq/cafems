"""Requests App Admin."""
from django.contrib import admin
from .models import TokenOpenCloseRequest


@admin.register(TokenOpenCloseRequest)
class TokenOpenCloseRequestAdmin(admin.ModelAdmin):
    list_display = ["employee", "request_type", "date_range_start", "date_range_end", "status", "submitted_at", "tenant"]
    list_filter = ["request_type", "status", "tenant"]
    search_fields = ["employee__full_name", "reason"]
