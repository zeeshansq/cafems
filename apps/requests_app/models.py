"""Requests App – Models (Open/Close Token Requests)."""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TenantModel


class RequestType(models.TextChoices):
    OPEN = "open", _("Open (Resume Membership)")
    CLOSE = "close", _("Close (Pause Membership)")


class RequestStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    ACKNOWLEDGED = "acknowledged", _("Acknowledged")
    REJECTED = "rejected", _("Rejected")
    CANCELLED = "cancelled", _("Cancelled")


class TokenOpenCloseRequest(TenantModel):
    """
    Employee open/close token request.

    Business rules enforced here:
    1. Must be submitted ≥1 day before date_range_start, by 2:00 PM PKT
    2. Immutable once submitted (no edits by employee)
    3. Cancellation only by staff/admin, or by employee if before cutoff

    See apps/core/utils.py::is_before_cutoff() for cutoff logic.
    """
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="open_close_requests",
        verbose_name=_("employee"),
    )
    request_type = models.CharField(
        _("type"),
        max_length=10,
        choices=RequestType.choices,
    )
    date_range_start = models.DateField(_("from date"))
    date_range_end = models.DateField(_("to date"))
    requested_token_qty = models.PositiveSmallIntegerField(
        _("requested token quantity"),
        default=1,
        help_text=_("Number of tokens requested for open request (1-5)"),
    )
    reason = models.TextField(_("reason"), blank=True)
    submitted_at = models.DateTimeField(_("submitted at"), auto_now_add=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
        db_index=True,
    )
    acknowledged_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_requests",
        verbose_name=_("acknowledged by"),
    )
    acknowledged_at = models.DateTimeField(_("acknowledged at"), null=True, blank=True)
    rejection_reason = models.TextField(_("rejection reason"), blank=True)

    class Meta:
        verbose_name = _("open/close request")
        verbose_name_plural = _("open/close requests")
        ordering = ["-submitted_at"]

    def __str__(self):
        return (
            f"{self.employee} | {self.get_request_type_display()} | "
            f"{self.date_range_start}–{self.date_range_end} | {self.get_status_display()}"
        )

    def clean(self):
        """Validate the 2:00 PM PKT cutoff rule."""
        from django.core.exceptions import ValidationError
        from apps.core.utils import is_before_cutoff
        if self.date_range_start and not self.pk:  # Only on creation
            if not is_before_cutoff(self.date_range_start):
                raise ValidationError(
                    _(
                        "Request must be submitted at least 1 day before the start date, "
                        "by 2:00 PM Pakistan Standard Time. The cutoff has passed."
                    )
                )

    @property
    def can_be_cancelled_by_employee(self):
        """Employee can cancel only if the cutoff hasn't passed yet."""
        from apps.core.utils import is_before_cutoff
        return (
            self.status == RequestStatus.PENDING
            and is_before_cutoff(self.date_range_start)
        )
