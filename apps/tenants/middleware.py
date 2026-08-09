"""Tenants App – Middleware."""
from django.utils.deprecation import MiddlewareMixin


class TenantMiddleware(MiddlewareMixin):
    """
    Simple tenant middleware for SQLite/dev mode.

    In production with PostgreSQL + django-tenants, this is replaced by
    TenantMainMiddleware from django_tenants.

    This middleware:
    1. Reads tenant slug from session or subdomain
    2. Sets request.tenant for use in views and context processors
    """

    def process_request(self, request):
        from .models import Tenant

        tenant = None

        # Check session for tenant
        tenant_slug = request.session.get("tenant_slug")
        if tenant_slug:
            try:
                tenant = Tenant.objects.get(slug=tenant_slug, status="active")
            except Tenant.DoesNotExist:
                request.session.pop("tenant_slug", None)

        # Check subdomain from HTTP_HOST
        if not tenant:
            host = request.get_host().split(":")[0]  # strip port
            parts = host.split(".")
            if len(parts) > 1:
                subdomain = parts[0]
                try:
                    from .models import Domain
                    domain_obj = Domain.objects.select_related("tenant").get(
                        domain__in=[host, subdomain]
                    )
                    tenant = domain_obj.tenant
                except Exception:
                    pass

        # Fall back to first active tenant (dev convenience)
        if not tenant:
            tenant = Tenant.objects.filter(status="active").first()

        request.tenant = tenant

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Prioritize authenticated user's tenant if assigned
        if hasattr(request, "user") and request.user.is_authenticated and getattr(request.user, "tenant", None):
            request.tenant = request.user.tenant

