"""CafeMS REST API – Root URL Configuration (v1)."""
from django.urls import path
from apps.notifications.views import UnreadCountView

urlpatterns = [
    path("notifications/unread-count/", UnreadCountView.as_view(), name="notif_unread_count"),
]
