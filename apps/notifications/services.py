"""Notifications App – Service functions."""
from .models import Notification, NotificationType


def create_notification(*, tenant, recipient, notification_type, title, message, link="", actor=None):
    """Create a single in-app notification."""
    return Notification.objects.create(
        tenant=tenant,
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
        actor=actor,
    )


def notify_staff(*, tenant, notification_type, title, message, link="", actor=None):
    """Notify all staff/admin users of a tenant."""
    from apps.accounts.models import User, UserRole
    staff = User.objects.filter(
        tenant=tenant,
        role__in=[UserRole.ADMIN, UserRole.STAFF],
        is_active=True,
    )
    notifications = []
    for user in staff:
        notifications.append(Notification(
            tenant=tenant,
            recipient=user,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link,
            actor=actor,
        ))
    Notification.objects.bulk_create(notifications)
    return len(notifications)


def notify_committee(*, tenant, notification_type, title, message, link="", actor=None):
    """Notify all committee members of a tenant."""
    from apps.accounts.models import User, UserRole
    members = User.objects.filter(
        tenant=tenant,
        role=UserRole.COMMITTEE,
        is_active=True,
    )
    notifications = [
        Notification(
            tenant=tenant,
            recipient=user,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link,
            actor=actor,
        )
        for user in members
    ]
    Notification.objects.bulk_create(notifications)
    return len(notifications)
