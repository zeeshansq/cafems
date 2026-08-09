"""Tenants App – URLs."""
from django.urls import path
from . import views

app_name = "tenants"

urlpatterns = [
    path("", views.TenantListView.as_view(), name="list"),
    path("dashboard/", views.TenantDashboardView.as_view(), name="dashboard"),
    path("new/", views.TenantCreateView.as_view(), name="create"),
    path("<slug:slug>/", views.TenantDetailView.as_view(), name="detail"),
    path("<slug:slug>/edit/", views.TenantUpdateView.as_view(), name="update"),
    path("<slug:slug>/delete/", views.TenantDeleteView.as_view(), name="delete"),
    path("<slug:slug>/suspend/", views.TenantSuspendView.as_view(), name="suspend"),
    path("<slug:slug>/activate/", views.TenantActivateView.as_view(), name="activate"),
]
