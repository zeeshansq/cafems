"""Accounts Admin."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["email", "first_name", "last_name", "role", "tenant", "is_staff", "is_active"]
    list_filter = ["role", "tenant", "is_staff", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["email"]

    fieldsets = UserAdmin.fieldsets + (
        ("CafeMS Extended Info", {"fields": ("role", "tenant", "mobile", "avatar", "dark_mode")}),
    )
