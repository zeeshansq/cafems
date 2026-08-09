"""Tenants App – Context Processors."""
from django.conf import settings


def tenant_context(request):
    """
    Inject tenant branding into every template.
    Used in: page title, navbar, sidebar, login page, PDFs, emails.
    """
    tenant = getattr(request, "tenant", None)

    if tenant:
        return {
            "tenant": tenant,
            "site_name": tenant.title,
            "site_short_name": tenant.short_title,
            "site_logo": tenant.logo_url,
            "tenant_currency": tenant.currency,
            "tenant_timezone": tenant.timezone,
        }

    # Public schema / no tenant
    cafems = settings.CAFEMS
    return {
        "tenant": None,
        "site_name": cafems.get("SITE_NAME", "CafeMS"),
        "site_short_name": "CMS",
        "site_logo": None,
        "tenant_currency": "PKR",
        "tenant_timezone": settings.TIME_ZONE,
    }
