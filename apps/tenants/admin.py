"""Tenants Admin."""
from django.contrib import admin
from .models import Tenant, Domain


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "short_title", "contact_email", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["title", "slug", "contact_email"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "tenant", "is_primary"]
    search_fields = ["domain"]
