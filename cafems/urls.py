"""CafeMS – Main URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "CafeMS Administration"
admin.site.site_title = "CafeMS Admin"
admin.site.index_title = "Welcome to CafeMS"

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),
    # Accounts (login/logout/profile)
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    # Tenant management (super-admin only)
    path("tenants/", include("apps.tenants.urls", namespace="tenants")),
    # Main app routes
    path("", include("apps.core.urls", namespace="core")),
    path("employees/", include("apps.employees.urls", namespace="employees")),
    path("menu/", include("apps.menu.urls", namespace="menu")),
    path("pos/", include("apps.pos.urls", namespace="pos")),
    path("tokens/", include("apps.tokens.urls", namespace="tokens")),
    path("requests/", include("apps.requests_app.urls", namespace="requests_app")),
    path("billing/", include("apps.billing.urls", namespace="billing")),
    path("notifications/", include("apps.notifications.urls", namespace="notifications")),
    path("reports/", include("apps.reports.urls", namespace="reports")),
    # REST API
    path("api/v1/", include("cafems.api_urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom Error Handlers
handler403 = "apps.core.views.custom_permission_denied_view"
handler404 = "apps.core.views.custom_page_not_found_view"
handler500 = "apps.core.views.custom_server_error_view"
handler400 = "apps.core.views.custom_bad_request_view"
