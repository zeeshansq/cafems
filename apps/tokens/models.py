"""Tokens App – Models."""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TenantModel


class TokenStatus(models.TextChoices):
    ISSUED = "issued", _("Issued")
    CANCELLED = "cancelled", _("Cancelled")


class LunchToken(TenantModel):
    """
    Issuance record for a lunch token.
    - 1 per member per day by default; max 3 (configurable per tenant)
    - Roti-Open members require staff override (logged in AuditLog)
    - price_snapshot is null until the daily price is finalized
    """
    date = models.DateField(_("date"), db_index=True)
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="lunch_tokens",
        verbose_name=_("employee"),
    )
    token_number = models.PositiveSmallIntegerField(
        _("token number"),
        help_text=_("Sequence number for today"),
    )
    token_qty = models.PositiveSmallIntegerField(
        _("token quantity"),
        default=1,
        help_text=_("Number of tokens issued in this transaction (1–5)"),
    )
    issued_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="issued_tokens",
        verbose_name=_("issued by"),
    )
    issue_time = models.DateTimeField(_("issue time"), auto_now_add=True)
    extra_roti_qty = models.PositiveSmallIntegerField(_("extra roti qty"), default=0)
    extra_sweet_qty = models.PositiveSmallIntegerField(_("extra sweet qty"), default=0)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=TokenStatus.choices,
        default=TokenStatus.ISSUED,
        db_index=True,
    )
    # Pricing (populated when daily estimate is finalized)
    price_snapshot = models.DecimalField(
        _("price snapshot"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Estimated price at issuance; hidden from employee until billed"),
    )
    adjustment_amount = models.DecimalField(
        _("month-end adjustment"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Pro-rata adjustment applied at billing time"),
    )
    # Roti-Open override flag
    roti_override = models.BooleanField(
        _("roti-open override"),
        default=False,
        help_text=_("True if staff overrode the Roti-Open lock for this token"),
    )
    is_retroactive = models.BooleanField(
        _("is retroactive charge"),
        default=False,
        help_text=_("True if retroactively charged via daily closing report"),
    )
    daily_estimate = models.ForeignKey(
        "menu.DailyLunchEstimate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tokens",
        verbose_name=_("daily estimate"),
    )

    class Meta:
        verbose_name = _("lunch token")
        verbose_name_plural = _("lunch tokens")
        ordering = ["-date", "-issue_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "date", "employee", "token_number"],
                name="unique_token_per_employee_per_day",
            )
        ]

    def __str__(self):
        return f"#{self.token_number} | {self.employee} | {self.date}"

    @property
    def total_day_cost(self):
        """
        Calculates total daily cost for this token issuance,
        including Token Price + Extra Roti Amount + Extra Sweet Amount + Adjustments.
        """
        from decimal import Decimal
        token_cost = (self.price_snapshot or Decimal("0.00")) * self.token_qty
        roti_cost = Decimal(str((self.extra_roti_qty or 0) * 15.00))
        sweet_cost = Decimal(str((self.extra_sweet_qty or 0) * 35.00))
        adj = (self.adjustment_amount or Decimal("0.00")) * self.token_qty
        return token_cost + roti_cost + sweet_cost + adj
