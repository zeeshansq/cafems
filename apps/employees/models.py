"""Employees App – Models."""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TenantModel


class MembershipType(models.TextChoices):
    FULL_OPEN = "full_open", _("Full Open")
    ROTI_OPEN = "roti_open", _("Roti Open")
    TEMP_CLOSE = "temp_close", _("Temp Close")
    NOT_MEMBER = "not_member", _("Not Member")


class EmployeeCategory(models.TextChoices):
    OFFICER = "officer", _("Officer")
    STAFF = "staff", _("Staff")


class Department(TenantModel):
    """Department or section within a tenant organization."""
    name = models.CharField(_("name"), max_length=100)
    code = models.CharField(_("code"), max_length=20, blank=True)

    class Meta:
        verbose_name = _("department")
        verbose_name_plural = _("departments")
        ordering = ["name"]
        unique_together = [["tenant", "name"]]

    def __str__(self):
        return self.name


class Employee(TenantModel):
    """
    Employee profile linked to a User account.
    Central model for membership, billing, and token operations.
    """
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_profile",
        verbose_name=_("user account"),
    )
    # Identifiers
    system_id = models.CharField(_("system ID"), max_length=50, blank=True)
    pno = models.CharField(_("P-No"), max_length=50, blank=True)
    register_number = models.CharField(_("register number"), max_length=50, blank=True)
    # Personal
    full_name = models.CharField(_("full name"), max_length=200)
    photo = models.ImageField(_("photo"), upload_to="employees/photos/", blank=True, null=True)
    email = models.EmailField(_("email"), blank=True)
    mobile = models.CharField(_("mobile"), max_length=20, blank=True)
    telephone_extension = models.CharField(_("telephone extension"), max_length=20, blank=True)
    gender = models.CharField(
        _("gender"),
        max_length=10,
        choices=[("M", _("Male")), ("F", _("Female")), ("O", _("Other"))],
        blank=True,
    )
    # Organizational
    designation = models.CharField(_("designation"), max_length=100, blank=True)
    category = models.CharField(
        _("category"),
        max_length=20,
        choices=EmployeeCategory.choices,
        default=EmployeeCategory.STAFF,
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        verbose_name=_("department"),
    )
    date_joined = models.DateField(_("date joined"), null=True, blank=True)
    # Membership
    membership_status = models.BooleanField(
        _("membership active"),
        default=False,
        help_text=_("Is this employee a cafe member?"),
    )
    membership_type = models.CharField(
        _("membership type"),
        max_length=20,
        choices=MembershipType.choices,
        default=MembershipType.TEMP_CLOSE,
    )
    # Security Deposit
    security_deposit_paid = models.DecimalField(
        _("security deposit paid"),
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    security_deposit_pending = models.DecimalField(
        _("security deposit pending"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Auto-appended to next monthly bill if > 0"),
    )
    # Status
    is_active = models.BooleanField(_("active"), default=True)
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("employee")
        verbose_name_plural = _("employees")
        ordering = ["full_name"]
        unique_together = [
            ["tenant", "pno"],
            ["tenant", "register_number"],
        ]

    def __str__(self):
        return f"{self.full_name} ({self.pno or self.system_id})"

    @property
    def is_full_open(self):
        return self.membership_type == MembershipType.FULL_OPEN

    @property
    def is_roti_open(self):
        return self.membership_type == MembershipType.ROTI_OPEN

    @property
    def is_temp_close(self):
        return self.membership_type == MembershipType.TEMP_CLOSE

    @property
    def pending_deposit_display(self):
        if self.security_deposit_pending > 0:
            return f"PKR {self.security_deposit_pending:,.2f}"
        return "None"


class AuditLog(TenantModel):
    """
    Immutable audit log for every backdated or sensitive edit.
    Required by spec §7: every backdated edit must be logged with before/after diff.
    """
    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
        verbose_name=_("actor"),
    )
    action = models.CharField(_("action"), max_length=100)
    model_name = models.CharField(_("model"), max_length=100)
    object_id = models.CharField(_("object ID"), max_length=100)
    before_data = models.JSONField(_("before"), null=True, blank=True)
    after_data = models.JSONField(_("after"), null=True, blank=True)
    note = models.TextField(_("note"), blank=True)
    ip_address = models.GenericIPAddressField(_("IP address"), null=True, blank=True)

    class Meta:
        verbose_name = _("audit log")
        verbose_name_plural = _("audit logs")
        ordering = ["-created_at"]
        # Audit logs are append-only — no editing allowed
        default_permissions = ("view",)

    def __str__(self):
        return f"[{self.created_at}] {self.actor} – {self.action} on {self.model_name}({self.object_id})"
