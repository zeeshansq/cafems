"""Notifications App – Context Processor."""


def notifications_context(request):
    """Inject unread notification count and recent notifications into every template."""
    if not request.user.is_authenticated:
        return {"unread_notifications_count": 0, "recent_notifications": []}

    from .models import Notification
    qs = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).order_by("-created_at")

    return {
        "unread_notifications_count": qs.count(),
        "recent_notifications": qs[:5],
    }
