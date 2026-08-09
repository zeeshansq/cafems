"""Menu App – Models."""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TenantModel


class MenuCategory(TenantModel):
    """Category for tea/snack items (e.g., Hot Beverages, Cold Drinks, Snacks)."""
    name = models.CharField(_("name"), max_length=100)
    icon = models.CharField(_("icon"), max_length=50, blank=True, help_text=_("Bootstrap Icons class"))
    sort_order = models.PositiveSmallIntegerField(_("sort order"), default=0)

    class Meta:
        verbose_name = _("menu category")
        verbose_name_plural = _("menu categories")
        ordering = ["sort_order", "name"]
        unique_together = [["tenant", "name"]]

    def __str__(self):
        return self.name


class TeaItem(TenantModel):
    """A POS item — tea, snack, or any sold item at the cafe counter."""
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
        verbose_name=_("category"),
    )
    name = models.CharField(_("name"), max_length=200)
    price = models.DecimalField(_("price"), max_digits=8, decimal_places=2)
    image = models.ImageField(_("image"), upload_to="menu_items/", null=True, blank=True)
    description = models.TextField(_("description"), blank=True)
    is_available = models.BooleanField(_("available"), default=True)
    sort_order = models.PositiveSmallIntegerField(_("sort order"), default=0)

    class Meta:
        verbose_name = _("tea/snack item")
        verbose_name_plural = _("tea/snack items")
        ordering = ["sort_order", "name"]

    def __str__(self):
        return f"{self.name} — PKR {self.price}"


class RotiType(models.TextChoices):
    ROTI = "roti", _("Standard Roti")
    NAAN = "naan", _("Tandoori Naan")
    ROGHNI = "roghni", _("Roghni Naan")
    NA = "na", _("N/A (Rice / No Roti)")


class LunchMenuPlan(TenantModel):
    """
    Generic Master Lunch Menu Plan entry for a 5-week rotating roster.
    Not tied to any specific year or month.
    """
    WEEK_CHOICES = [(i, f"Week {i}") for i in range(1, 6)]
    DAY_CHOICES = [
        (0, _("Monday")),
        (1, _("Tuesday")),
        (2, _("Wednesday")),
        (3, _("Thursday")),
        (4, _("Friday")),
        (5, _("Saturday")),
        (6, _("Sunday")),
    ]

    month = models.DateField(_("month"), null=True, blank=True, help_text=_("Optional month reference"))
    week_of_month = models.PositiveSmallIntegerField(_("week"), choices=WEEK_CHOICES)
    day_of_week = models.PositiveSmallIntegerField(_("day"), choices=DAY_CHOICES)
    dish_name = models.CharField(_("dish name"), max_length=200)
    description = models.TextField(_("description"), blank=True)
    
    cook = models.ForeignKey(
        "Cook",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="menu_plans",
        verbose_name=_("default cook"),
    )
    roti_price_obj = models.ForeignKey(
        "RotiPrice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="menu_plans",
        verbose_name=_("roti / naan selection"),
    )
    roti_type = models.CharField(
        _("roti type"),
        max_length=50,
        choices=RotiType.choices,
        default=RotiType.ROTI,
        blank=True,
    )
    sweet = models.ForeignKey(
        "Sweet",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="menu_plans",
        verbose_name=_("default sweet"),
    )
    contains_sweet = models.BooleanField(_("contains sweet"), default=False)
    planned_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planned_menus",
        verbose_name=_("planned by"),
    )
    is_published = models.BooleanField(_("published"), default=True)

    class Meta:
        verbose_name = _("master lunch menu plan")
        verbose_name_plural = _("master lunch menu plans")
        ordering = ["week_of_month", "day_of_week"]
        unique_together = [["tenant", "week_of_month", "day_of_week"]]

    def __str__(self):
        day_name = dict(self.DAY_CHOICES).get(self.day_of_week, "?")
        return f"Week {self.week_of_month} {day_name}: {self.dish_name}"

    @property
    def get_roti_type_display(self):
        if self.roti_price_obj:
            return self.roti_price_obj.name
        roti_choices_dict = dict(RotiType.choices)
        if self.roti_type in roti_choices_dict:
            return str(roti_choices_dict[self.roti_type])
        return str(self.roti_type) if self.roti_type else "Standard Roti"


class Cook(TenantModel):
    name = models.CharField(_("cook name"), max_length=150)
    phone = models.CharField(_("phone"), max_length=30, blank=True)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("cook")
        verbose_name_plural = _("cooks")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Sweet(TenantModel):
    name = models.CharField(_("sweet name"), max_length=150)
    price = models.DecimalField(_("fixed price"), max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("sweet")
        verbose_name_plural = _("sweets")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} (PKR {self.price})"


class RotiPrice(TenantModel):
    name = models.CharField(_("roti / naan name"), max_length=100, default="Standard Roti")
    roti_type = models.CharField(
        _("roti type code"),
        max_length=50,
        default="roti",
        blank=True,
    )
    price = models.DecimalField(_("price per unit"), max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("roti price setup")
        verbose_name_plural = _("roti price setup")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} — PKR {self.price}"


class DailyLunchEstimate(TenantModel):
    """
    Daily Lunch Menu Entry & Costing calculation model.
    """
    date = models.DateField(_("date"), db_index=True)
    dish_name = models.CharField(_("dish name"), max_length=200, blank=True)
    cook = models.ForeignKey(
        Cook,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="daily_entries",
        verbose_name=_("cook"),
    )
    roti_price_obj = models.ForeignKey(
        RotiPrice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="daily_entries",
        verbose_name=_("roti / naan selection"),
    )
    roti_type = models.CharField(
        _("roti type"),
        max_length=50,
        default=RotiType.ROTI,
    )
    sweet = models.ForeignKey(
        Sweet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="daily_entries",
        verbose_name=_("sweet"),
        help_text=_("Select NA / leave empty if no sweet included"),
    )
    menu_plan = models.ForeignKey(
        LunchMenuPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estimates",
        verbose_name=_("menu plan"),
    )

    # Token estimation & actuals
    planned_count = models.PositiveIntegerField(_("planned token count"), default=0)
    actual_tokens_issued = models.PositiveIntegerField(_("actual tokens issued"), default=0)

    # Extra Roti estimation, actuals & pricing
    estimated_extra_roti = models.PositiveIntegerField(_("estimated extra roti count"), default=0)
    actual_extra_roti_issued = models.PositiveIntegerField(_("actual extra roti issued"), default=0)
    roti_unit_price = models.DecimalField(_("roti unit price"), max_digits=8, decimal_places=2, default=0)

    # Extra Sweet estimation, actuals & pricing
    estimated_extra_sweet = models.PositiveIntegerField(_("estimated extra sweet count"), default=0)
    actual_extra_sweet_issued = models.PositiveIntegerField(_("actual extra sweet issued"), default=0)
    sweet_unit_price = models.DecimalField(_("sweet unit price"), max_digits=8, decimal_places=2, default=0)

    # Expense & Adjustment
    total_expense = models.DecimalField(_("total daily expense"), max_digits=10, decimal_places=2, default=0)
    adjustment_amount = models.DecimalField(
        _("adjustment amount"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Can be positive or negative amount"),
    )

    # Auto-calculated totals
    token_expense = models.DecimalField(_("net token expense"), max_digits=10, decimal_places=2, default=0)
    price_per_token = models.DecimalField(
        _("token unit cost"),
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text=_("Auto calculated: Net Token Expense / Actual Tokens Issued"),
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="daily_estimates",
        verbose_name=_("created by"),
    )
    is_locked = models.BooleanField(
        _("locked"),
        default=False,
        help_text=_("Locked once token issuance starts"),
    )

    class Meta:
        verbose_name = _("daily lunch estimate")
        verbose_name_plural = _("daily lunch estimates")
        ordering = ["-date"]
        unique_together = [["tenant", "date"]]

    def __str__(self):
        return f"{self.date} – {self.dish_name or 'Lunch'} | Unit Cost: PKR {self.price_per_token}"

    @property
    def get_roti_type_display(self):
        """Returns readable label for roti selection."""
        if self.roti_price_obj:
            return self.roti_price_obj.name
        if self.roti_type:
            roti_choices_dict = dict(RotiType.choices)
            if self.roti_type in roti_choices_dict:
                return str(roti_choices_dict[self.roti_type])
            return str(self.roti_type)
        return "Standard Roti"

    def recalculate(self):
        """
        Recalculates actual issued numbers from LunchToken records and recomputes costing totals.
        """
        from decimal import Decimal
        from django.db.models import Sum
        from apps.tokens.models import LunchToken, TokenStatus

        # 1. Calculate actual issuance numbers for this date
        tokens = LunchToken.objects.filter(tenant=self.tenant, date=self.date, status=TokenStatus.ISSUED)
        agg = tokens.aggregate(
            tot_tokens=Sum("token_qty"),
            tot_roti=Sum("extra_roti_qty"),
            tot_sweet=Sum("extra_sweet_qty"),
        )
        self.actual_tokens_issued = agg["tot_tokens"] or 0
        self.actual_extra_roti_issued = agg["tot_roti"] or 0
        self.actual_extra_sweet_issued = agg["tot_sweet"] or 0

        # 2. Get Roti Unit Price
        if self.roti_price_obj:
            self.roti_unit_price = self.roti_price_obj.price
            self.roti_type = self.roti_price_obj.name
        elif self.roti_type:
            roti_obj = RotiPrice.objects.filter(tenant=self.tenant, roti_type=self.roti_type).first()
            if not roti_obj:
                roti_obj = RotiPrice.objects.filter(tenant=self.tenant, name__icontains=self.roti_type).first()
            if roti_obj:
                self.roti_unit_price = roti_obj.price
            elif self.roti_type == RotiType.ROTI:
                self.roti_unit_price = Decimal("15.00")
            elif self.roti_type == RotiType.NAAN:
                self.roti_unit_price = Decimal("20.00")
            elif self.roti_type == RotiType.ROGHNI:
                self.roti_unit_price = Decimal("40.00")
            else:
                self.roti_unit_price = Decimal("0.00")

        # 3. Get Sweet Unit Price if sweet selected
        if self.sweet:
            self.sweet_unit_price = self.sweet.price
        else:
            self.sweet_unit_price = Decimal("0.00")

        # 4. Calculate Extra Roti & Sweet Costs
        extra_roti_cost = Decimal(self.actual_extra_roti_issued) * Decimal(self.roti_unit_price or 0)
        extra_sweet_cost = Decimal(self.actual_extra_sweet_issued) * Decimal(self.sweet_unit_price or 0)

        # 5. Token Expense = max(0, Total Expense - Extra Roti Cost - Extra Sweet Cost + Adjustment)
        calc_exp = Decimal(self.total_expense or 0) - extra_roti_cost - extra_sweet_cost + Decimal(self.adjustment_amount or 0)
        self.token_expense = max(Decimal("0.00"), calc_exp)

        # 6. Token Unit Cost = Token Expense / Actual Tokens Issued (or 0 if none)
        if self.actual_tokens_issued > 0:
            self.price_per_token = (self.token_expense / Decimal(self.actual_tokens_issued)).quantize(Decimal("0.01"))
        else:
            self.price_per_token = Decimal("0.00")

    def save(self, *args, **kwargs):
        # Auto-run recalculation logic if actuals or prices need computing
        self.recalculate()
        super().save(*args, **kwargs)

