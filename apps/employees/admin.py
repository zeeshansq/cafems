"""Employees Admin."""
from django.contrib import admin
from .models import Department, Employee, AuditLog


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "tenant"]
    search_fields = ["name", "code"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["full_name", "pno", "department", "membership_status", "membership_type", "is_active", "tenant"]
    list_filter = ["membership_status", "membership_type", "is_active", "tenant", "department"]
    search_fields = ["full_name", "pno", "email", "mobile"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["actor", "action", "model_name", "object_id", "created_at", "tenant"]
    list_filter = ["action", "model_name", "tenant"]
    search_fields = ["note", "object_id"]
    readonly_fields = ["actor", "action", "model_name", "object_id", "before_data", "after_data", "created_at"]
