"""POS App – Models."""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TenantModel


class PaymentMethod(models.TextChoices):
    CASH = "cash", _("Cash")
    CARD = "card", _("Card")
    MOBILE = "mobile", _("Mobile Payment")
    ACCOUNT = "account", _("Account Deduction")


class TeaItemSale(TenantModel):
    """
    POS transaction log for tea/snack sales.
    buyer is nullable for walk-in (non-employee) customers.
    """
    date = models.DateField(_("date"), db_index=True)
    item = models.ForeignKey(
        "menu.TeaItem",
        on_delete=models.PROTECT,
        related_name="sales",
        verbose_name=_("item"),
    )
    quantity = models.PositiveIntegerField(_("quantity"), default=1)
    unit_price = models.DecimalField(_("unit price"), max_digits=8, decimal_places=2)
    amount_paid = models.DecimalField(_("amount paid"), max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        _("payment method"),
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    buyer = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tea_purchases",
        verbose_name=_("buyer (employee)"),
    )
    is_walk_in = models.BooleanField(
        _("walk-in customer"),
        default=False,
        help_text=_("True if buyer is not an employee"),
    )
    issued_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="pos_sales",
        verbose_name=_("issued by"),
    )
    order_reference = models.CharField(
        _("order reference"),
        max_length=50,
        blank=True,
        db_index=True,
        help_text=_("Unique reference grouping items of a single checkout order"),
    )
    note = models.CharField(_("note"), max_length=200, blank=True)

    class Meta:
        verbose_name = _("tea/snack sale")
        verbose_name_plural = _("tea/snack sales")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.date} | {self.item.name} x{self.quantity} = {self.amount_paid}"

    @property
    def total_amount(self):
        return self.unit_price * self.quantity

    @property
    def change_given(self):
        return self.amount_paid - self.total_amount
