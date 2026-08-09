"""Billing App – Views."""
import datetime
from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView, View, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from apps.core.mixins import AdminRequiredMixin, CommitteeRequiredMixin, StaffRequiredMixin
from apps.employees.models import Employee
from .models import MonthlyBill, Payment, MiscCharge, BillStatus
from .forms import MiscChargeForm, PaymentForm
from .services import BillingService


class BillListView(StaffRequiredMixin, ListView):
    model = MonthlyBill
    template_name = "billing/bill_list.html"
    context_object_name = "bills"
    paginate_by = 20

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        qs = MonthlyBill.objects.filter(tenant=tenant).select_related("employee", "employee__department").order_by("-period_start", "-created_at")

        # Determine default month filter if not explicitly specified
        month_param = self.request.GET.get("month")
        if not month_param and "month" not in self.request.GET:
            # Default to latest billed month (e.g. 2026-07) or current month
            latest_bill = MonthlyBill.objects.filter(tenant=tenant).order_by("-period_start").first()
            if latest_bill:
                month_param = latest_bill.period_start.strftime("%Y-%m")
            else:
                month_param = timezone.localdate().strftime("%Y-%m")

        self.selected_month = month_param

        if month_param and month_param != "all":
            try:
                parts = month_param.split("-")
                qs = qs.filter(period_start__year=int(parts[0]), period_start__month=int(parts[1]))
            except (ValueError, IndexError):
                pass

        # Text search (Name, PNo, Register #, Bill ID)
        q = self.request.GET.get("q", "").strip()
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(employee__full_name__icontains=q) |
                Q(employee__pno__icontains=q) |
                Q(employee__register_number__icontains=q) |
                Q(id__icontains=q)
            )

        # Status filter
        status_f = self.request.GET.get("status")
        if status_f:
            qs = qs.filter(status=status_f)

        # Department filter
        dept_f = self.request.GET.get("department")
        if dept_f:
            qs = qs.filter(employee__department_id=dept_f)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)

        from django.db.models import Sum
        filtered_qs = self.get_queryset()
        
        ctx["page_title"] = "Monthly Bills Directory"
        ctx["status_choices"] = BillStatus.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["current_q"] = self.request.GET.get("q", "")
        ctx["current_dept"] = self.request.GET.get("department", "")
        ctx["selected_month"] = getattr(self, "selected_month", timezone.localdate().strftime("%Y-%m"))

        # Department list for filter dropdown
        from apps.employees.models import Department
        ctx["departments"] = Department.objects.filter(tenant=tenant).order_by("name")

        # KPI Metrics for current filtered bills
        kpi = filtered_qs.aggregate(
            total_amount=Sum("total"),
            token_sum=Sum("token_total"),
            misc_sum=Sum("misc_charges_total"),
            prev_sum=Sum("previous_balance")
        )
        ctx["kpi_total_count"] = filtered_qs.count()
        ctx["kpi_total_amount"] = kpi["total_amount"] or 0
        ctx["kpi_token_sum"] = kpi["token_sum"] or 0
        ctx["kpi_misc_sum"] = kpi["misc_sum"] or 0

        # Payments collected for these bills
        paid_sum = Payment.objects.filter(tenant=tenant, bill__in=filtered_qs).aggregate(total=Sum("amount_paid"))["total"] or 0
        ctx["kpi_paid_amount"] = paid_sum
        ctx["kpi_pending_amount"] = (kpi["total_amount"] or 0) - paid_sum

        return ctx


class BillDetailView(StaffRequiredMixin, DetailView):
    model = MonthlyBill
    template_name = "billing/bill_detail.html"
    context_object_name = "bill"

    def get_queryset(self):
        return MonthlyBill.objects.filter(tenant=getattr(self.request, "tenant", None))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"Bill – {self.object.employee} – {self.object.period_start.strftime('%b %Y')}"
        ctx["payments"] = self.object.payments.order_by("-payment_date")
        ctx["payment_form"] = PaymentForm()

        from apps.tokens.models import LunchToken
        from apps.menu.models import DailyLunchEstimate
        tokens = list(LunchToken.objects.filter(
            tenant=self.object.tenant,
            employee=self.object.employee,
            date__range=(self.object.period_start, self.object.period_end)
        ).select_related("daily_estimate").order_by("date"))

        for tok in tokens:
            if not tok.daily_estimate:
                tok.daily_estimate = DailyLunchEstimate.objects.filter(tenant=self.object.tenant, date=tok.date).first()

        ctx["daily_tokens"] = tokens

        return ctx


class GenerateBillsView(AdminRequiredMixin, TemplateView):
    """Generate monthly bills and manage monthly bill entries/batches."""
    template_name = "billing/generate_bills.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        ctx["page_title"] = "Generate Monthly Bills & Entries"
        today = timezone.localdate()
        def_month = today.replace(day=1)
        ctx["default_month"] = def_month

        # Fetch existing misc charge for default month
        existing_misc = MiscCharge.objects.filter(tenant=tenant, month=def_month).first()
        ctx["default_misc_amount"] = existing_misc.amount if existing_misc else Decimal("30.00")
        ctx["default_misc_desc"] = existing_misc.description if existing_misc else "Cafeteria Maintenance & Administrative Overhead"

        # List all monthly bill runs with employee counts and totals
        from .models import MonthlyBillRun
        from django.db.models import Sum, Count
        runs = MonthlyBillRun.objects.filter(tenant=tenant).order_by("-period_start")
        run_data = []
        for run in runs:
            bills = MonthlyBill.objects.filter(tenant=tenant, period_start=run.period_start)
            agg = bills.aggregate(total_sum=Sum("total"))
            run_data.append({
                "run": run,
                "month_str": run.period_start.strftime("%Y-%m"),
                "employee_count": bills.count(),
                "total_amount": agg["total_sum"] or Decimal("0.00"),
            })
        ctx["bill_runs"] = run_data

        return ctx

    def post(self, request, *args, **kwargs):
        tenant = getattr(request, "tenant", None)
        month_str = request.POST.get("month")
        if not month_str:
            messages.error(request, "Please select a billing month.")
            return self.get(request, *args, **kwargs)

        try:
            month = datetime.date.fromisoformat(month_str + "-01")
        except ValueError:
            messages.error(request, "Invalid month.")
            return self.get(request, *args, **kwargs)

        # Update or create MiscCharge for target month if amount provided
        misc_amount_str = request.POST.get("misc_amount")
        misc_desc = request.POST.get("misc_description", "Cafeteria Maintenance & Administrative Overhead").strip()
        if misc_amount_str:
            try:
                misc_amt = Decimal(misc_amount_str)
                MiscCharge.objects.update_or_create(
                    tenant=tenant,
                    month=month,
                    defaults={
                        "amount": misc_amt,
                        "description": misc_desc,
                        "created_by": request.user,
                    }
                )
            except Exception as e:
                messages.warning(request, f"Could not update misc charge: {e}")

        service = BillingService(tenant=tenant, month=month, actor=request.user)
        count = service.generate_all()

        messages.success(request, f"Successfully generated {count} bill entry rows for {month.strftime('%B %Y')}.")
        return redirect("billing:generate")


class PublishBillRunView(AdminRequiredMixin, View):
    """Publish an entire monthly bill entry batch and dispatch in-app notifications to all employees."""
    def post(self, request, pk):
        tenant = getattr(request, "tenant", None)
        from .models import MonthlyBillRun, MonthlyBillRunStatus
        run = get_object_or_404(MonthlyBillRun, pk=pk, tenant=tenant)

        run.status = MonthlyBillRunStatus.PUBLISHED
        run.published_at = timezone.now()
        run.published_by = request.user
        run.save(update_fields=["status", "published_at", "published_by"])

        # Send in-app notifications to all billed employees
        from apps.notifications.services import create_notification
        from apps.notifications.models import NotificationType
        bills = MonthlyBill.objects.filter(tenant=tenant, period_start=run.period_start).select_related("employee", "employee__user")
        notify_count = 0
        for bill in bills:
            if bill.employee and bill.employee.user:
                create_notification(
                    tenant=tenant,
                    recipient=bill.employee.user,
                    notification_type=NotificationType.BILL_PUBLISHED,
                    title=f"Monthly Bill for {run.period_start.strftime('%B %Y')} Published",
                    message=f"Your monthly cafeteria invoice for {run.period_start.strftime('%B %Y')} has been published. Net Amount Payable: {bill.total:,.2f}",
                    link=f"/billing/my/{bill.pk}/",
                    actor=request.user,
                )
                notify_count += 1

        messages.success(request, f"Published monthly bill entry for {run.period_start.strftime('%B %Y')} and sent in-app notifications to {notify_count} employees.")
        return redirect("billing:generate")


class BillRunReportView(StaffRequiredMixin, TemplateView):
    """HTML Executive Master Monthly Billing Summary Report with search, filters, pagination, and overall stats."""
    template_name = "billing/bill_run_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        month_str = self.kwargs.get("month_str")

        try:
            parts = month_str.split("-")
            month_date = datetime.date(int(parts[0]), int(parts[1]), 1)
        except (ValueError, IndexError):
            month_date = timezone.localdate().replace(day=1)

        from .models import MonthlyBillRun, MonthlyBill, BillStatus
        from apps.employees.models import Department
        from django.db.models import Sum, Q
        from django.core.paginator import Paginator

        run = MonthlyBillRun.objects.filter(tenant=tenant, period_start=month_date).first()
        base_qs = MonthlyBill.objects.filter(tenant=tenant, period_start=month_date).select_related("employee", "employee__department")

        # Aggregation across ALL bills for overall month stats
        overall_agg = base_qs.aggregate(
            token_qty=Sum("total_token_qty"),
            token_amt=Sum("token_total"),
            roti_qty=Sum("total_extra_roti_qty"),
            roti_amt=Sum("extra_roti_total"),
            sweet_qty=Sum("total_extra_sweet_qty"),
            sweet_amt=Sum("extra_sweet_total"),
            misc_amt=Sum("misc_charges_total"),
            prev_amt=Sum("previous_balance"),
            deposit_amt=Sum("security_deposit_pending"),
            subtotal_amt=Sum("subtotal"),
            total_amt=Sum("total"),
        )

        qs = base_qs.order_by("employee__pno")

        # Filters
        q = self.request.GET.get("q", "").strip()
        dept_id = self.request.GET.get("department", "").strip()
        status_val = self.request.GET.get("status", "").strip()

        if q:
            qs = qs.filter(
                Q(employee__full_name__icontains=q) |
                Q(employee__pno__icontains=q) |
                Q(employee__register_number__icontains=q)
            )
        if dept_id:
            qs = qs.filter(employee__department_id=dept_id)
        if status_val:
            qs = qs.filter(status=status_val)

        # Aggregation across filtered bills
        filtered_agg = qs.aggregate(
            token_qty=Sum("total_token_qty"),
            token_amt=Sum("token_total"),
            roti_qty=Sum("total_extra_roti_qty"),
            roti_amt=Sum("extra_roti_total"),
            sweet_qty=Sum("total_extra_sweet_qty"),
            sweet_amt=Sum("extra_sweet_total"),
            misc_amt=Sum("misc_charges_total"),
            prev_amt=Sum("previous_balance"),
            deposit_amt=Sum("security_deposit_pending"),
            total_amt=Sum("total"),
        )

        # Pagination (25 items per page)
        paginator = Paginator(qs, 25)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        ctx["page_title"] = f"Master Billing Summary – {month_date.strftime('%B %Y')}"
        ctx["month_date"] = month_date
        ctx["month_str"] = month_str
        ctx["bill_run"] = run
        ctx["bills"] = page_obj.object_list
        ctx["page_obj"] = page_obj
        ctx["paginator"] = paginator
        ctx["is_paginated"] = page_obj.has_other_pages()
        ctx["employee_count"] = base_qs.count()
        ctx["filtered_count"] = qs.count()
        ctx["stats"] = overall_agg
        ctx["filtered_stats"] = filtered_agg
        ctx["departments"] = Department.objects.filter(tenant=tenant)
        ctx["status_choices"] = BillStatus.choices
        ctx["current_q"] = q
        ctx["current_dept"] = dept_id
        ctx["current_status"] = status_val
        return ctx


class BillRunPrintView(StaffRequiredMixin, TemplateView):
    """Dedicated A4 Printable Executive Master Monthly Billing Summary Report."""
    template_name = "billing/bill_run_print.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        month_str = self.kwargs.get("month_str")

        try:
            parts = month_str.split("-")
            month_date = datetime.date(int(parts[0]), int(parts[1]), 1)
        except (ValueError, IndexError):
            month_date = timezone.localdate().replace(day=1)

        from .models import MonthlyBillRun, MonthlyBill
        from django.db.models import Sum

        run = MonthlyBillRun.objects.filter(tenant=tenant, period_start=month_date).first()
        bills = MonthlyBill.objects.filter(tenant=tenant, period_start=month_date).select_related("employee", "employee__department").order_by("employee__pno")

        agg = bills.aggregate(
            token_qty=Sum("total_token_qty"),
            token_amt=Sum("token_total"),
            roti_qty=Sum("total_extra_roti_qty"),
            roti_amt=Sum("extra_roti_total"),
            sweet_qty=Sum("total_extra_sweet_qty"),
            sweet_amt=Sum("extra_sweet_total"),
            misc_amt=Sum("misc_charges_total"),
            prev_amt=Sum("previous_balance"),
            deposit_amt=Sum("security_deposit_pending"),
            subtotal_amt=Sum("subtotal"),
            total_amt=Sum("total"),
        )

        ctx["page_title"] = f"Print Master Report – {month_date.strftime('%B %Y')}"
        ctx["month_date"] = month_date
        ctx["month_str"] = month_str
        ctx["bill_run"] = run
        ctx["bills"] = bills
        ctx["employee_count"] = bills.count()
        ctx["stats"] = agg
        return ctx


class ApproveBillView(CommitteeRequiredMixin, View):
    """Committee member approves a reviewed bill."""
    def post(self, request, pk):
        tenant = getattr(request, "tenant", None)
        bill = get_object_or_404(MonthlyBill, pk=pk, tenant=tenant)
        if not bill.can_transition_to(BillStatus.APPROVED, request.user):
            messages.error(request, f"Cannot approve bill in status: {bill.get_status_display()}")
            return redirect("billing:detail", pk=pk)

        bill.status = BillStatus.APPROVED
        bill.approved_by = request.user
        bill.save(update_fields=["status", "approved_by"])
        messages.success(request, "Bill approved.")
        return redirect("billing:detail", pk=pk)


class PublishBillView(AdminRequiredMixin, View):
    """Admin publishes a bill — triggers notification to employee."""
    def post(self, request, pk):
        tenant = getattr(request, "tenant", None)
        bill = get_object_or_404(MonthlyBill, pk=pk, tenant=tenant)
        if not bill.can_transition_to(BillStatus.PUBLISHED, request.user):
            messages.error(request, f"Cannot publish bill in status: {bill.get_status_display()}")
            return redirect("billing:detail", pk=pk)

        bill.status = BillStatus.PUBLISHED
        bill.published_at = timezone.now()
        bill.save(update_fields=["status", "published_at"])

        # Notify employee
        employee = bill.employee
        if employee.user:
            from apps.notifications.services import create_notification
            from apps.notifications.models import NotificationType
            create_notification(
                tenant=tenant,
                recipient=employee.user,
                notification_type=NotificationType.BILL_PUBLISHED,
                title=f"Bill for {bill.period_start.strftime('%B %Y')} Published",
                message=f"Your bill for {bill.period_start.strftime('%B %Y')} is now available. Total: PKR {bill.total:,.2f}",
                link=f"/billing/my/{bill.pk}/",
                actor=request.user,
            )

        messages.success(request, f"Bill published and employee notified.")
        return redirect("billing:detail", pk=pk)


class BulkBillActionView(StaffRequiredMixin, View):
    """Perform batch operations (Bulk Approve, Bulk Publish, Bulk Delete) on selected bills."""
    def post(self, request):
        tenant = getattr(request, "tenant", None)
        action = request.POST.get("action")
        bill_ids = request.POST.getlist("bill_ids")

        if not bill_ids:
            messages.warning(request, "No bills were selected for batch processing.")
            return redirect("billing:list")

        bills = MonthlyBill.objects.filter(tenant=tenant, id__in=bill_ids)
        count = 0

        if action == "bulk_approve":
            for bill in bills:
                if bill.status in [BillStatus.DRAFT, BillStatus.REVIEWED]:
                    bill.status = BillStatus.APPROVED
                    bill.approved_by = request.user
                    bill.save(update_fields=["status", "approved_by"])
                    count += 1
            messages.success(request, f"Successfully approved {count} bill(s) in bulk.")

        elif action == "bulk_publish":
            from apps.notifications.services import create_notification
            from apps.notifications.models import NotificationType
            for bill in bills:
                if bill.status == BillStatus.APPROVED or bill.status in [BillStatus.DRAFT, BillStatus.REVIEWED]:
                    bill.status = BillStatus.PUBLISHED
                    bill.published_at = timezone.now()
                    bill.save(update_fields=["status", "published_at"])
                    count += 1
                    # Send notification to employee
                    if bill.employee and bill.employee.user:
                        create_notification(
                            tenant=tenant,
                            recipient=bill.employee.user,
                            notification_type=NotificationType.BILL_PUBLISHED,
                            title=f"Bill for {bill.period_start.strftime('%B %Y')} Published",
                            message=f"Your bill for {bill.period_start.strftime('%B %Y')} is now available. Net Payable: {bill.total:,.2f}",
                            link=f"/billing/my/{bill.pk}/",
                            actor=request.user,
                        )
            messages.success(request, f"Successfully published {count} bill(s) and notified employees.")

        elif action == "bulk_delete":
            deleted_count, _ = bills.filter(status=BillStatus.DRAFT).delete()
            messages.success(request, f"Successfully deleted {deleted_count} draft bill(s).")

        else:
            messages.error(request, "Invalid batch action specified.")

        return redirect("billing:list")


class RecordPaymentView(AdminRequiredMixin, View):
    """Record a payment against a bill."""
    def post(self, request, pk):
        tenant = getattr(request, "tenant", None)
        bill = get_object_or_404(MonthlyBill, pk=pk, tenant=tenant, status__in=[
            BillStatus.PUBLISHED, BillStatus.PARTIALLY_PAID
        ])
        form = PaymentForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid payment form.")
            return redirect("billing:detail", pk=pk)

        payment = form.save(commit=False)
        payment.bill = bill
        payment.method = "cash"
        payment.received_by = request.user

        total_paid = sum(p.amount_paid for p in bill.payments.all()) + payment.amount_paid
        payment.remaining_balance = max(0, bill.total - total_paid)
        payment.save()

        # Update bill status
        if payment.remaining_balance <= 0:
            bill.status = BillStatus.PAID
            # Zero out pending security deposit on employee if paid
            if bill.security_deposit_pending > 0:
                emp = bill.employee
                emp.security_deposit_paid += bill.security_deposit_pending
                emp.security_deposit_pending = Decimal("0.00")
                emp.save(update_fields=["security_deposit_paid", "security_deposit_pending"])

            # Send payment confirmation notification
            if bill.employee.user:
                from apps.notifications.services import create_notification
                from apps.notifications.models import NotificationType
                create_notification(
                    tenant=tenant,
                    recipient=bill.employee.user,
                    notification_type=NotificationType.SYSTEM,
                    title=f"Payment Received — {bill.period_start.strftime('%B %Y')}",
                    message=f"Thank you! Full payment of PKR {bill.total:,.2f} for {bill.period_start.strftime('%B %Y')} has been confirmed.",
                    link=f"/billing/my/{bill.pk}/",
                    actor=request.user,
                )
        else:
            bill.status = BillStatus.PARTIALLY_PAID
        bill.save(update_fields=["status"])

        messages.success(request, f"Payment of PKR {payment.amount_paid:,.2f} recorded.")
        return redirect("billing:detail", pk=pk)


class AddMiscChargeView(AdminRequiredMixin, TemplateView):
    template_name = "billing/misc_charges.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        ctx["page_title"] = "Manage Monthly Misc Charges"
        ctx["misc_charges"] = MiscCharge.objects.filter(tenant=tenant).order_by("-month")
        ctx["form"] = MiscChargeForm(initial={"month": timezone.localdate().replace(day=1).strftime("%Y-%m-%d")})
        return ctx

    def post(self, request):
        tenant = getattr(request, "tenant", None)
        form = MiscChargeForm(request.POST)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.tenant = tenant
            charge.created_by = request.user
            charge.save()
            messages.success(request, f"Misc charge of {charge.amount:,.2f} added for {charge.month.strftime('%B %Y')}.")
        else:
            messages.error(request, "Invalid misc charge data.")
        return redirect("billing:add_misc_charge")


# ── Employee: My Bills ───────────────────────────────────────────────────────

from apps.core.mixins import StaffRequiredMixin, EmployeeRequiredMixin


class MyBillsView(EmployeeRequiredMixin, ListView):
    model = MonthlyBill
    template_name = "billing/my_bills.html"
    context_object_name = "bills"

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        try:
            employee = self.request.user.employee_profile
        except Exception:
            return MonthlyBill.objects.none()
        from .models import MonthlyBillRun, MonthlyBillRunStatus
        published_months = MonthlyBillRun.objects.filter(
            tenant=tenant, status=MonthlyBillRunStatus.PUBLISHED
        ).values_list("period_start", flat=True)
        return MonthlyBill.objects.filter(
            tenant=tenant, employee=employee, period_start__in=published_months
        ).order_by("-period_start")


class MyBillDetailView(EmployeeRequiredMixin, DetailView):
    model = MonthlyBill
    template_name = "billing/my_bill_detail.html"
    context_object_name = "bill"

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        try:
            employee = self.request.user.employee_profile
        except Exception:
            return MonthlyBill.objects.none()
        from .models import MonthlyBillRun, MonthlyBillRunStatus
        published_months = MonthlyBillRun.objects.filter(
            tenant=tenant, status=MonthlyBillRunStatus.PUBLISHED
        ).values_list("period_start", flat=True)
        return MonthlyBill.objects.filter(
            tenant=tenant, employee=employee, period_start__in=published_months
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"Bill – {self.object.period_start.strftime('%B %Y')}"
        ctx["show_price_details"] = False

        from apps.tokens.models import LunchToken
        from apps.menu.models import DailyLunchEstimate
        tokens = list(LunchToken.objects.filter(
            tenant=self.object.tenant,
            employee=self.object.employee,
            date__range=(self.object.period_start, self.object.period_end)
        ).select_related("daily_estimate").order_by("date"))

        for tok in tokens:
            if not tok.daily_estimate:
                tok.daily_estimate = DailyLunchEstimate.objects.filter(tenant=self.object.tenant, date=tok.date).first()

        ctx["daily_tokens"] = tokens

        return ctx
