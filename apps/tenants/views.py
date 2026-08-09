"""Tenants App – Views (Full CRUD for Super Admin)."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse

from apps.core.mixins import SuperAdminRequiredMixin
from .models import Tenant, TenantStatus
from .forms import TenantForm


class TenantDashboardView(SuperAdminRequiredMixin, TemplateView):
    template_name = "tenants/tenant_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Platform Dashboard"
        ctx["tenants"] = Tenant.objects.all().order_by("-created_at")
        ctx["total_tenants"] = Tenant.objects.count()
        ctx["active_tenants"] = Tenant.objects.filter(status=TenantStatus.ACTIVE).count()
        ctx["suspended_tenants"] = Tenant.objects.filter(status=TenantStatus.SUSPENDED).count()
        return ctx


class TenantListView(SuperAdminRequiredMixin, ListView):
    model = Tenant
    template_name = "tenants/tenant_list.html"
    context_object_name = "tenants"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Manage Organizations & Tenants"
        return ctx


class TenantDetailView(SuperAdminRequiredMixin, DetailView):
    model = Tenant
    template_name = "tenants/tenant_detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = self.object.title
        return ctx


class TenantCreateView(SuperAdminRequiredMixin, CreateView):
    model = Tenant
    form_class = TenantForm
    template_name = "tenants/tenant_form.html"
    success_url = reverse_lazy("tenants:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Create New Tenant"
        ctx["action"] = "Create"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f"Tenant '{form.instance.title}' created successfully.")
        return super().form_valid(form)


class TenantUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Tenant
    form_class = TenantForm
    template_name = "tenants/tenant_form.html"
    success_url = reverse_lazy("tenants:list")
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"Edit {self.object.title}"
        ctx["action"] = "Update"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, f"Tenant '{self.object.title}' updated successfully.")
        return super().form_valid(form)


class TenantDeleteView(SuperAdminRequiredMixin, DeleteView):
    model = Tenant
    template_name = "tenants/tenant_confirm_delete.html"
    success_url = reverse_lazy("tenants:list")
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def delete(self, request, *args, **kwargs):
        tenant = self.get_object()
        title = tenant.title
        messages.success(request, f"Tenant '{title}' was deleted successfully.")
        return super().delete(request, *args, **kwargs)


class TenantSuspendView(SuperAdminRequiredMixin, View):
    def post(self, request, slug):
        tenant = get_object_or_404(Tenant, slug=slug)
        tenant.status = TenantStatus.SUSPENDED
        tenant.save(update_fields=["status"])
        messages.warning(request, f"Tenant '{tenant.title}' has been suspended.")
        return redirect("tenants:list")


class TenantActivateView(SuperAdminRequiredMixin, View):
    def post(self, request, slug):
        tenant = get_object_or_404(Tenant, slug=slug)
        tenant.status = TenantStatus.ACTIVE
        tenant.save(update_fields=["status"])
        messages.success(request, f"Tenant '{tenant.title}' has been activated.")
        return redirect("tenants:list")
