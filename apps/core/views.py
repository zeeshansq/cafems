"""Core App – Views (Dashboard routing, profile, etc.)."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View, UpdateView
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum

from apps.accounts.models import UserRole
from apps.core.mixins import StaffRequiredMixin, EmployeeRequiredMixin


class DashboardRedirectView(LoginRequiredMixin, View):
    """
    Role-based dashboard redirect.
    Sends each user role to their specific dashboard.
    """
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.role == UserRole.SUPER_ADMIN:
            return redirect("tenants:dashboard")
        elif user.role in (UserRole.ADMIN, UserRole.CAFE_STAFF):
            return redirect("core:admin_dashboard")
        elif user.role == UserRole.COMMITTEE_MEMBER:
            return redirect("core:admin_dashboard")  # Same dash, different nav
        else:  # Employee
            return redirect("core:employee_dashboard")


class AdminDashboardView(StaffRequiredMixin, TemplateView):
    template_name = "core/admin_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        today = timezone.localdate()

        from apps.employees.models import Employee
        from apps.tokens.models import LunchToken, TokenStatus
        from apps.pos.models import TeaItemSale
        from apps.billing.models import MonthlyBill, BillStatus
        from apps.requests_app.models import TokenOpenCloseRequest, RequestStatus
        from apps.menu.models import Cook, Sweet, RotiPrice, DailyLunchEstimate, LunchMenuPlan

        pos_today = TeaItemSale.objects.filter(tenant=tenant, date=today)
        pos_today_revenue = sum(sale.quantity * sale.unit_price for sale in pos_today)

        ctx["page_title"] = "Dashboard"
        ctx["today"] = today
        ctx["total_employees"] = Employee.objects.filter(
            tenant=tenant, is_active=True, membership_status=True
        ).count()
        ctx["tokens_today"] = LunchToken.objects.filter(
            tenant=tenant, date=today, status=TokenStatus.ISSUED
        ).aggregate(total=Sum("token_qty"))["total"] or 0
        ctx["pos_today_revenue"] = pos_today_revenue
        ctx["pending_bills"] = MonthlyBill.objects.filter(
            tenant=tenant, status=BillStatus.UNPAID
        ).count()
        ctx["pending_requests_count"] = TokenOpenCloseRequest.objects.filter(
            tenant=tenant, status=RequestStatus.PENDING
        ).count()

        ctx["cooks_count"] = Cook.objects.filter(tenant=tenant, is_active=True).count()
        ctx["sweets_count"] = Sweet.objects.filter(tenant=tenant, is_active=True).count()
        ctx["roti_count"] = RotiPrice.objects.filter(tenant=tenant, is_active=True).count()
        ctx["plans_count"] = LunchMenuPlan.objects.filter(tenant=tenant).count()
        ctx["today_entry"] = DailyLunchEstimate.objects.filter(tenant=tenant, date=today).select_related("cook", "sweet").first()
        ctx["is_menu_configured"] = ctx["today_entry"] is not None and bool(ctx["today_entry"].dish_name)
        return ctx


class EmployeeDashboardView(EmployeeRequiredMixin, TemplateView):
    template_name = "core/employee_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        today = timezone.localdate()
        ctx["page_title"] = "My Dining Dashboard"
        ctx["today"] = today

        try:
            employee = self.request.user.employee_profile
        except Exception:
            employee = None

        ctx["employee"] = employee

        if employee:
            from apps.tokens.models import LunchToken, TokenStatus
            from apps.pos.models import TeaItemSale
            from apps.billing.models import MonthlyBill, BillStatus
            from apps.requests_app.models import TokenOpenCloseRequest, RequestStatus
            from apps.menu.models import DailyLunchEstimate

            # Token metrics this month
            tokens_qs = LunchToken.objects.filter(
                tenant=tenant,
                employee=employee,
                date__year=today.year,
                date__month=today.month,
                status=TokenStatus.ISSUED,
            )
            ctx["tokens_this_month"] = tokens_qs.aggregate(t=Sum("token_qty"))["t"] or 0
            ctx["extra_roti_this_month"] = tokens_qs.aggregate(r=Sum("extra_roti_qty"))["r"] or 0
            ctx["extra_sweet_this_month"] = tokens_qs.aggregate(s=Sum("extra_sweet_qty"))["s"] or 0

            # POS spend this month
            pos_qs = TeaItemSale.objects.filter(
                tenant=tenant,
                buyer=employee,
                date__year=today.year,
                date__month=today.month,
            )
            ctx["pos_spend_this_month"] = sum(sale.quantity * sale.unit_price for sale in pos_qs)

            # Latest Bill & Pending requests
            ctx["latest_bill"] = MonthlyBill.objects.filter(
                tenant=tenant, employee=employee,
                status__in=[BillStatus.UNPAID, BillStatus.PARTIALLY_PAID, BillStatus.PAID]
            ).order_by("-period_start").first()

            ctx["pending_requests_count"] = TokenOpenCloseRequest.objects.filter(
                tenant=tenant, employee=employee, status=RequestStatus.PENDING
            ).count()

            # Today's Lunch Menu Estimate
            ctx["today_menu_estimate"] = DailyLunchEstimate.objects.filter(
                tenant=tenant, date=today
            ).select_related("cook", "sweet", "roti_price_obj").first()

            # Smart link to Master Menu Plan based on today's week of month and day of week
            week_of_month = (today.day - 1) // 7 + 1
            day_of_week = today.weekday()

            ctx["today_week_of_month"] = week_of_month
            ctx["today_day_name"] = today.strftime("%A")

            from apps.menu.models import LunchMenuPlan
            ctx["master_plan_today"] = LunchMenuPlan.objects.filter(
                tenant=tenant,
                week_of_month=week_of_month,
                day_of_week=day_of_week,
                is_published=True
            ).select_related("cook", "sweet", "roti_price_obj").first()

            # Recent 10 Tokens
            ctx["recent_tokens"] = LunchToken.objects.filter(
                tenant=tenant, employee=employee
            ).select_related("daily_estimate").order_by("-date", "-issue_time")[:10]

        return ctx


# ── Custom Error Handlers ────────────────────────────────────────────────────
from django.shortcuts import render

def custom_permission_denied_view(request, exception=None):
    """Custom 403 Forbidden Handler."""
    return render(request, "403.html", {"exception": exception}, status=403)

def custom_page_not_found_view(request, exception=None):
    """Custom 404 Not Found Handler."""
    return render(request, "404.html", {"exception": exception}, status=404)

def custom_server_error_view(request):
    """Custom 500 Server Error Handler."""
    return render(request, "500.html", status=500)

def custom_bad_request_view(request, exception=None):
    """Custom 400 Bad Request Handler."""
    return render(request, "400.html", {"exception": exception}, status=400)

