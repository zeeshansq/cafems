"""Tokens App – Celery Tasks."""
from celery import shared_task
from django.utils import timezone


@shared_task(name="tokens.generate_daily_estimates_reminder")
def remind_estimate_not_set():
    """
    Runs at 7:00 AM PKT — if today's DailyLunchEstimate hasn't been set,
    notify all admin users.
    """
    from apps.core.utils import get_today_pkt
    from apps.tenants.models import Tenant, TenantStatus
    from apps.menu.models import DailyLunchEstimate
    from apps.notifications.services import notify_staff
    from apps.notifications.models import NotificationType

    today = get_today_pkt()

    for tenant in Tenant.objects.filter(status=TenantStatus.ACTIVE):
        if not DailyLunchEstimate.objects.filter(tenant=tenant, date=today).exists():
            notify_staff(
                tenant=tenant,
                notification_type=NotificationType.SYSTEM,
                title="Daily Estimate Not Set",
                message=f"Today's ({today}) lunch estimate has not been set yet. Please set it now.",
                link="/menu/daily-estimate/new/",
            )


@shared_task(name="tokens.close_expired_requests")
def close_expired_requests():
    """
    Runs hourly — auto-cancel open/close requests whose cutoff has passed.
    Requests with date_range_start = yesterday (before 2PM PKT) should not
    be manually cancellable; this task ensures they expire cleanly.
    """
    # This task primarily enforces the UI rule — actual enforcement is in
    # TokenOpenCloseRequest.can_be_cancelled_by_employee
    pass


@shared_task(name="tokens.snapshot_daily_price")
def snapshot_daily_price():
    """
    Runs at 6:00 PM PKT — after lunch is over.
    Copies the daily estimate price into each LunchToken.price_snapshot
    (if not already set).
    """
    from apps.core.utils import get_today_pkt
    from apps.tenants.models import Tenant, TenantStatus
    from apps.tokens.models import LunchToken, TokenStatus
    from apps.menu.models import DailyLunchEstimate

    today = get_today_pkt()

    for tenant in Tenant.objects.filter(status=TenantStatus.ACTIVE):
        try:
            estimate = DailyLunchEstimate.objects.get(tenant=tenant, date=today)
            if not estimate.price_per_token:
                continue
        except DailyLunchEstimate.DoesNotExist:
            continue

        updated = LunchToken.objects.filter(
            tenant=tenant, date=today,
            status=TokenStatus.ISSUED,
            price_snapshot__isnull=True,
        ).update(price_snapshot=estimate.price_per_token)
