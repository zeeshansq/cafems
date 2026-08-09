"""Employees App – Views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from apps.core.mixins import StaffRequiredMixin, AdminRequiredMixin
from .models import Employee, Department, AuditLog
from .forms import EmployeeForm


class EmployeeListView(StaffRequiredMixin, ListView):
    model = Employee
    template_name = "employees/employee_list.html"
    context_object_name = "employees"
    paginate_by = 25

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        from django.db.models import Q
        qs = Employee.objects.filter(tenant=tenant).select_related("department", "user")

        q = self.request.GET.get("q", "").strip()
        dept = self.request.GET.get("department", "").strip()
        m_type = self.request.GET.get("membership_type", "").strip()
        m_status = self.request.GET.get("membership_status", "").strip()
        is_active = self.request.GET.get("is_active", "").strip()

        if q:
            qs = qs.filter(
                Q(full_name__icontains=q) |
                Q(pno__icontains=q) |
                Q(register_number__icontains=q) |
                Q(designation__icontains=q)
            )
        if dept:
            qs = qs.filter(department_id=dept)
        if m_type:
            qs = qs.filter(membership_type=m_type)
        if m_status != "":
            if m_status == "true":
                qs = qs.filter(membership_status=True)
            elif m_status == "false":
                qs = qs.filter(membership_status=False)
        if is_active != "":
            if is_active == "true":
                qs = qs.filter(is_active=True)
            elif is_active == "false":
                qs = qs.filter(is_active=False)

        return qs.order_by("full_name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        from .models import Department, MembershipType
        from django.db.models import Sum

        all_emps = Employee.objects.filter(tenant=tenant)
        ctx["page_title"] = "Employee Directory & Management"
        ctx["search_query"] = self.request.GET.get("q", "")
        ctx["current_dept"] = self.request.GET.get("department", "")
        ctx["current_mtype"] = self.request.GET.get("membership_type", "")
        ctx["current_mstatus"] = self.request.GET.get("membership_status", "")
        ctx["current_active"] = self.request.GET.get("is_active", "")

        ctx["departments"] = Department.objects.filter(tenant=tenant)
        ctx["membership_types"] = MembershipType.choices

        # KPI Metrics
        ctx["kpi_total_count"] = all_emps.count()
        ctx["kpi_active_members"] = all_emps.filter(is_active=True, membership_status=True).count()
        ctx["kpi_full_open"] = all_emps.filter(membership_type=MembershipType.FULL_OPEN).count()
        ctx["kpi_roti_open"] = all_emps.filter(membership_type=MembershipType.ROTI_OPEN).count()
        ctx["kpi_deposit_pending"] = all_emps.aggregate(sum_dep=Sum("security_deposit_pending"))["sum_dep"] or 0
        return ctx


class EmployeeCreateView(AdminRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "employees/employee_form.html"
    success_url = reverse_lazy("employees:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Add Employee"
        ctx["action"] = "Create"
        return ctx

    def form_valid(self, form):
        form.instance.tenant = getattr(self.request, "tenant", None)
        messages.success(self.request, f"Employee '{form.instance.full_name}' added successfully.")
        return super().form_valid(form)


class EmployeeUpdateView(AdminRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = "employees/employee_form.html"
    success_url = reverse_lazy("employees:list")

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        return Employee.objects.filter(tenant=tenant)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"Edit {self.object.full_name}"
        ctx["action"] = "Update"
        return ctx

    def form_valid(self, form):
        # Log the edit in AuditLog (backdated edit detection)
        old = Employee.objects.get(pk=self.object.pk)
        response = super().form_valid(form)
        AuditLog.objects.create(
            tenant=getattr(self.request, "tenant", None),
            actor=self.request.user,
            action="update_employee",
            model_name="Employee",
            object_id=str(self.object.pk),
            before_data={
                "full_name": old.full_name,
                "membership_type": old.membership_type,
                "security_deposit_pending": str(old.security_deposit_pending),
            },
            after_data={
                "full_name": self.object.full_name,
                "membership_type": self.object.membership_type,
                "security_deposit_pending": str(self.object.security_deposit_pending),
            },
        )
        messages.success(self.request, "Employee updated successfully.")
        return response


class EmployeeDetailView(StaffRequiredMixin, DetailView):
    model = Employee
    template_name = "employees/employee_detail.html"
    context_object_name = "employee"

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        return Employee.objects.filter(tenant=tenant).select_related("department", "user")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = self.object.full_name
        # Recent tokens
        from apps.tokens.models import LunchToken
        ctx["recent_tokens"] = LunchToken.objects.filter(
            employee=self.object
        ).order_by("-date")[:10]
        # Recent bills
        from apps.billing.models import MonthlyBill
        ctx["bills"] = MonthlyBill.objects.filter(
            employee=self.object
        ).order_by("-period_start")[:6]
        return ctx
