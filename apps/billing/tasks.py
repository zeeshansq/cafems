"""Billing App – Celery Tasks."""
from celery import shared_task


@shared_task(name="billing.send_bill_reminders")
def send_bill_reminders():
    """
    Runs daily at 9:00 AM PKT — send reminder notifications to employees
    with unpaid published bills older than 7 days.
    """
    from apps.tenants.models import Tenant, TenantStatus
    from apps.billing.models import MonthlyBill, BillStatus
    from apps.notifications.services import create_notification
    from apps.notifications.models import NotificationType
    from django.utils import timezone
    import datetime

    cutoff = timezone.now().date() - datetime.timedelta(days=7)

    for tenant in Tenant.objects.filter(status=TenantStatus.ACTIVE):
        overdue_bills = MonthlyBill.objects.filter(
            tenant=tenant,
            status__in=[BillStatus.UNPAID, BillStatus.PARTIALLY_PAID],
        ).select_related("employee__user")

        for bill in overdue_bills:
            if bill.employee.user:
                create_notification(
                    tenant=tenant,
                    recipient=bill.employee.user,
                    notification_type=NotificationType.BILL_PENDING,
                    title=f"Bill Reminder — {bill.period_start.strftime('%B %Y')}",
                    message=f"Your bill of PKR {bill.total:,.2f} for {bill.period_start.strftime('%B %Y')} is still outstanding.",
                    link=f"/billing/my/{bill.pk}/",
                )
