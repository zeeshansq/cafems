"""Notifications App – Models."""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TenantModel


class NotificationType(models.TextChoices):
    REQUEST_SUBMITTED = "request_submitted", _("Request Submitted")
    REQUEST_ACKNOWLEDGED = "request_acknowledged", _("Request Acknowledged")
    REQUEST_REJECTED = "request_rejected", _("Request Rejected")
    BILL_GENERATED = "bill_generated", _("Bill Generated")
    BILL_PENDING = "bill_pending", _("Bill Pending Payment")
    BILL_PUBLISHED = "bill_published", _("Bill Published")
    PAYMENT_RECEIVED = "payment_received", _("Payment Received")
    SYSTEM = "system", _("System")


class Notification(TenantModel):
    """
    In-app notification model.
    Displayed as bell icon with unread count in navbar.
    """
    recipient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("recipient"),
    )
    notification_type = models.CharField(
        _("type"),
        max_length=30,
        choices=NotificationType.choices,
        db_index=True,
    )
    title = models.CharField(_("title"), max_length=200)
    message = models.TextField(_("message"))
    link = models.CharField(_("link"), max_length=500, blank=True)
    is_read = models.BooleanField(_("read"), default=False, db_index=True)
    read_at = models.DateTimeField(_("read at"), null=True, blank=True)
    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
        verbose_name=_("actor"),
    )

    class Meta:
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"→ {self.recipient} | {self.title} | {'✓' if self.is_read else '●'}"

    def mark_read(self):
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])
