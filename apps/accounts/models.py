"""Accounts App – Custom User Model with Role-Based Access Control."""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    SUPER_ADMIN = "super_admin", _("Super Admin")
    ADMIN = "admin", _("Admin")
    CAFE_STAFF = "cafe_staff", _("Cafe Staff")
    COMMITTEE_MEMBER = "committee_member", _("Committee Member")
    EMPLOYEE = "employee", _("Employee")


class User(AbstractUser):
    """
    Custom User model.
    - email is the login field (unique)
    - role drives all permission checks (enforced server-side via mixins)
    - tenant FK links the user to their organization
    - dark_mode preference is persisted per-user
    """
    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.EMPLOYEE,
        db_index=True,
    )
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name=_("tenant"),
        help_text=_("The organization this user belongs to. Null for Super Admin."),
    )
    mobile = models.CharField(_("mobile"), max_length=20, blank=True)
    avatar = models.ImageField(
        _("avatar"),
        upload_to="avatars/",
        null=True,
        blank=True,
    )
    dark_mode = models.BooleanField(
        _("dark mode"),
        default=False,
        help_text=_("User prefers dark mode"),
    )
    is_first_login = models.BooleanField(_("first login"), default=True)
    last_activity = models.DateTimeField(_("last activity"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["first_name", "last_name"]

    def __str__(self):
        name = self.get_full_name()
        return f"{name} <{self.email}> [{self.get_role_display()}]" if name else f"{self.email} [{self.get_role_display()}]"

    # ── Convenience properties ─────────────────────────────────────────────
    @property
    def full_name(self):
        return self.get_full_name() or self.email.split("@")[0]

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    # ── Role predicates ────────────────────────────────────────────────────
    @property
    def is_super_admin(self):
        return self.role == UserRole.SUPER_ADMIN

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_cafe_staff(self):
        return self.role == UserRole.CAFE_STAFF

    @property
    def is_committee_member(self):
        return self.role == UserRole.COMMITTEE_MEMBER

    @property
    def is_employee_role(self):
        return self.role == UserRole.EMPLOYEE

    # ── Permission helpers (server-side guards) ────────────────────────────
    def can_manage_employees(self):
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]

    def can_view_reports(self):
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.COMMITTEE_MEMBER]

    def can_access_pos(self):
        return self.role in [UserRole.ADMIN, UserRole.CAFE_STAFF]

    def can_issue_tokens(self):
        return self.role in [UserRole.ADMIN, UserRole.CAFE_STAFF]

    def can_generate_bills(self):
        return self.role == UserRole.ADMIN

    def can_approve_bills(self):
        return self.role in [UserRole.ADMIN, UserRole.COMMITTEE_MEMBER]

    def can_acknowledge_requests(self):
        return self.role in [UserRole.ADMIN, UserRole.CAFE_STAFF]

    def can_manage_menu(self):
        return self.role in [UserRole.ADMIN, UserRole.CAFE_STAFF]
