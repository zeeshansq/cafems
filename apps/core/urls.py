from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.DashboardRedirectView.as_view(), name="dashboard"),
    path("dashboard/admin/", views.AdminDashboardView.as_view(), name="admin_dashboard"),
    path("dashboard/me/", views.EmployeeDashboardView.as_view(), name="employee_dashboard"),
]
