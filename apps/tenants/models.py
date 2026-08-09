"""Tenants App – Models."""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class TenantStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    INACTIVE = "inactive", _("Inactive")
    SUSPENDED = "suspended", _("Suspended")


class Tenant(TimeStampedModel):
    """
    Organization/tenant model.
    In production: each tenant maps to a PostgreSQL schema (via django-tenants).
    In SQLite dev: used as a FK on every model for logical isolation.
    """
    title = models.CharField(_("title"), max_length=200)
    short_title = models.CharField(_("short title"), max_length=50)
    slug = models.SlugField(_("slug"), unique=True, db_index=True)
    logo = models.ImageField(_("logo"), upload_to="tenant_logos/", null=True, blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=TenantStatus.choices,
        default=TenantStatus.ACTIVE,
        db_index=True,
    )
    contact_email = models.EmailField(_("contact email"))
    contact_phone = models.CharField(_("contact phone"), max_length=30, blank=True)
    address = models.TextField(_("address"), blank=True)
    currency = models.CharField(_("currency"), max_length=10, default="PKR")
    timezone = models.CharField(_("timezone"), max_length=50, default="Asia/Karachi")
    max_tokens_per_day = models.PositiveSmallIntegerField(
        _("max tokens per day"),
        default=3,
        help_text=_("Maximum lunch tokens an employee can issue per day"),
    )
    # Schema name for django-tenants (production PostgreSQL)
    schema_name = models.CharField(
        _("schema name"),
        max_length=100,
        unique=True,
        default="public",
        help_text=_("PostgreSQL schema name. Set automatically from slug."),
    )
    paid_until = models.DateField(_("paid until"), null=True, blank=True)
    on_trial = models.BooleanField(_("on trial"), default=True)

    class Meta:
        verbose_name = _("tenant")
        verbose_name_plural = _("tenants")
        ordering = ["title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.schema_name or self.schema_name == "public":
            self.schema_name = self.slug.replace("-", "_")
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status == TenantStatus.ACTIVE

    @property
    def logo_url(self):
        if self.logo:
            return self.logo.url
        return None


class Domain(TimeStampedModel):
    """
    Domain model for tenant routing.
    In production (django-tenants + PostgreSQL): used for subdomain routing.
    In dev: informational only.
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="domains",
        verbose_name=_("tenant"),
    )
    domain = models.CharField(_("domain"), max_length=253, unique=True, db_index=True)
    is_primary = models.BooleanField(_("primary"), default=True)

    class Meta:
        verbose_name = _("domain")
        verbose_name_plural = _("domains")
        ordering = ["domain"]

    def __str__(self):
        return self.domain
