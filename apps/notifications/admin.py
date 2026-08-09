"""Notifications Admin."""
from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "notification_type", "title", "is_read", "created_at", "tenant"]
    list_filter = ["notification_type", "is_read", "tenant"]
    search_fields = ["recipient__email", "title", "message"]
