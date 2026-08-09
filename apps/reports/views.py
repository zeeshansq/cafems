"""Reports App – Views."""
import csv
import datetime
from django.views.generic import TemplateView, View
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q, F, ExpressionWrapper, DecimalField
from django.core.paginator import Paginator

from apps.core.mixins import StaffRequiredMixin
from apps.tokens.models import LunchToken, TokenStatus
from apps.pos.models import TeaItemSale
from apps.employees.models import Employee, Department
from apps.requests_app.models import TokenOpenCloseRequest, RequestType, RequestStatus
from apps.billing.models import MonthlyBill, BillStatus


def get_common_report_filters(request):
    """Helper function to parse common filter parameters from request GET."""
    tenant = getattr(request, "tenant", None)
    today = timezone.localdate()

    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    emp_id = request.GET.get("employee_id")
    dept_id = request.GET.get("department_id")
    q = request.GET.get("q", "").strip()

    try:
        start_date = datetime.date.fromisoformat(start_date_str) if start_date_str else today.replace(day=1)
    except (ValueError, TypeError):
        start_date = today.replace(day=1)

    try:
        end_date = datetime.date.fromisoformat(end_date_str) if end_date_str else today
    except (ValueError, TypeError):
        end_date = today

    all_departments = Department.objects.filter(tenant=tenant).order_by("name")
    all_employees = Employee.objects.filter(tenant=tenant, is_active=True).select_related("department").order_by("full_name")

    return {
        "tenant": tenant,
        "today": today,
        "start_date": start_date,
        "end_date": end_date,
        "emp_id": emp_id,
        "current_emp_id": int(emp_id) if (emp_id and emp_id.isdigit()) else "",
        "dept_id": dept_id,
        "current_dept_id": int(dept_id) if (dept_id and dept_id.isdigit()) else "",
        "q": q,
        "all_departments": all_departments,
        "all_employees": all_employees,
    }


class ReportsIndexView(StaffRequiredMixin, TemplateView):
    """Reports Hub main index page rendering a grid of 7 report cards."""
    template_name = "reports/reports_index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Reports & Analytics Hub"
        return ctx


class MonthlyTokenReportView(StaffRequiredMixin, TemplateView):
    """1. Monthly / Period Lunch Token Summary Report."""
    template_name = "reports/monthly_token_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = get_common_report_filters(self.request)

        tokens_qs = LunchToken.objects.filter(
            tenant=f["tenant"],
            date__gte=f["start_date"],
            date__lte=f["end_date"],
            status=TokenStatus.ISSUED,
        ).select_related("employee", "employee__department")

        if f["emp_id"] and f["emp_id"].isdigit():
            tokens_qs = tokens_qs.filter(employee_id=int(f["emp_id"]))
        if f["dept_id"] and f["dept_id"].isdigit():
            tokens_qs = tokens_qs.filter(employee__department_id=int(f["dept_id"]))
        if f["q"]:
            tokens_qs = tokens_qs.filter(
                Q(employee__full_name__icontains=f["q"]) | Q(employee__pno__icontains=f["q"])
            )

        token_summary = tokens_qs.values(
            "employee_id", "employee__full_name", "employee__pno", "employee__department__name"
        ).annotate(
            total_tokens=Sum("token_qty"),
            total_roti=Sum("extra_roti_qty"),
            total_sweet=Sum("extra_sweet_qty"),
            days_attended=Count("date", distinct=True)
        ).order_by("-total_tokens")

        total_tokens_sum = tokens_qs.aggregate(t=Sum("token_qty"))["t"] or 0
        total_roti_sum = tokens_qs.aggregate(r=Sum("extra_roti_qty"))["r"] or 0
        total_sweet_sum = tokens_qs.aggregate(s=Sum("extra_sweet_qty"))["s"] or 0

        ctx.update(f)
        ctx.update({
            "page_title": "Monthly Token Summary Report",
            "token_summary": token_summary,
            "total_tokens_sum": total_tokens_sum,
            "total_roti_sum": total_roti_sum,
            "total_sweet_sum": total_sweet_sum,
            "report_type": "tokens",
        })
        return ctx


class POSCollectionReportView(StaffRequiredMixin, TemplateView):
    """2. Misc Charges & POS Cash Collection History Report."""
    template_name = "reports/pos_collection_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = get_common_report_filters(self.request)

        pos_qs = TeaItemSale.objects.filter(
            tenant=f["tenant"],
            date__gte=f["start_date"],
            date__lte=f["end_date"],
        ).annotate(
            total_val=ExpressionWrapper(F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=10, decimal_places=2))
        ).select_related("item", "buyer", "buyer__department", "issued_by")

        if f["emp_id"] and f["emp_id"].isdigit():
            pos_qs = pos_qs.filter(buyer_id=int(f["emp_id"]))
        if f["dept_id"] and f["dept_id"].isdigit():
            pos_qs = pos_qs.filter(buyer__department_id=int(f["dept_id"]))
        if f["q"]:
            pos_qs = pos_qs.filter(
                Q(item__name__icontains=f["q"]) |
                Q(buyer__full_name__icontains=f["q"]) |
                Q(buyer__pno__icontains=f["q"]) |
                Q(order_reference__icontains=f["q"])
            )

        pos_total_revenue = pos_qs.aggregate(t=Sum("total_val"))["t"] or 0
        pos_total_items = pos_qs.aggregate(q=Sum("quantity"))["q"] or 0
        pos_walkin_revenue = pos_qs.filter(is_walk_in=True).aggregate(t=Sum("total_val"))["t"] or 0
        pos_member_revenue = pos_qs.filter(is_walk_in=False).aggregate(t=Sum("total_val"))["t"] or 0

        pos_paginator = Paginator(pos_qs.order_by("-created_at"), 25)
        pos_page = pos_paginator.get_page(self.request.GET.get("page", 1))

        ctx.update(f)
        ctx.update({
            "page_title": "Misc Charges & POS Collection History",
            "pos_sales": pos_page.object_list,
            "page_obj": pos_page,
            "is_paginated": pos_page.has_other_pages(),
            "pos_total_revenue": pos_total_revenue,
            "pos_total_items": pos_total_items,
            "pos_walkin_revenue": pos_walkin_revenue,
            "pos_member_revenue": pos_member_revenue,
            "report_type": "pos_misc",
        })
        return ctx


class EmployeeIssuanceReportView(StaffRequiredMixin, TemplateView):
    """3. Employee Profiles & Issuance History Report."""
    template_name = "reports/employee_issuance_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = get_common_report_filters(self.request)

        issuance_type = self.request.GET.get("issuance_type", "tokens").strip()

        emp_qs = Employee.objects.filter(tenant=f["tenant"]).select_related("department")
        if f["emp_id"] and f["emp_id"].isdigit():
            emp_qs = emp_qs.filter(id=int(f["emp_id"]))
        if f["dept_id"] and f["dept_id"].isdigit():
            emp_qs = emp_qs.filter(department_id=int(f["dept_id"]))
        if f["q"]:
            emp_qs = emp_qs.filter(
                Q(full_name__icontains=f["q"]) | Q(pno__icontains=f["q"])
            )

        # Filter by issuance category (tokens, pos, all) - Defaults to 'tokens'
        if issuance_type == "tokens":
            emp_ids_tokens = LunchToken.objects.filter(
                tenant=f["tenant"], date__gte=f["start_date"], date__lte=f["end_date"], status=TokenStatus.ISSUED
            ).values_list("employee_id", flat=True).distinct()
            emp_qs = emp_qs.filter(id__in=emp_ids_tokens)
        elif issuance_type == "pos":
            emp_ids_pos = TeaItemSale.objects.filter(
                tenant=f["tenant"], date__gte=f["start_date"], date__lte=f["end_date"]
            ).values_list("buyer_id", flat=True).distinct()
            emp_qs = emp_qs.filter(id__in=emp_ids_pos)

        emp_summary_list = []
        for emp in emp_qs.order_by("full_name"):
            toks = LunchToken.objects.filter(
                tenant=f["tenant"], employee=emp, date__gte=f["start_date"], date__lte=f["end_date"], status=TokenStatus.ISSUED
            )
            pos_sales = TeaItemSale.objects.filter(
                tenant=f["tenant"], buyer=emp, date__gte=f["start_date"], date__lte=f["end_date"]
            ).annotate(
                total_val=ExpressionWrapper(F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=10, decimal_places=2))
            )
            emp_summary_list.append({
                "emp": emp,
                "token_count": toks.aggregate(t=Sum("token_qty"))["t"] or 0,
                "extra_roti": toks.aggregate(r=Sum("extra_roti_qty"))["r"] or 0,
                "extra_sweet": toks.aggregate(s=Sum("extra_sweet_qty"))["s"] or 0,
                "pos_spend": pos_sales.aggregate(t=Sum("total_val"))["t"] or 0,
                "days_attended": toks.values("date").distinct().count(),
            })

        ctx.update(f)
        ctx.update({
            "page_title": "Employee Profiles & Issuance History",
            "emp_summary_list": emp_summary_list,
            "issuance_type": issuance_type,
            "report_type": "emp_issuance",
        })
        return ctx


class EmployeeDepositsReportView(StaffRequiredMixin, TemplateView):
    """4. Employee Security Deposits Report."""
    template_name = "reports/employee_deposits_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = get_common_report_filters(self.request)

        deposits_qs = Employee.objects.filter(tenant=f["tenant"]).select_related("department")
        if f["dept_id"] and f["dept_id"].isdigit():
            deposits_qs = deposits_qs.filter(department_id=int(f["dept_id"]))
        if f["q"]:
            deposits_qs = deposits_qs.filter(
                Q(full_name__icontains=f["q"]) | Q(pno__icontains=f["q"])
            )

        total_active_members = deposits_qs.filter(membership_status=True).count()
        total_deposits_held = deposits_qs.aggregate(d=Sum("security_deposit_paid"))["d"] or 0
        total_temp_close = deposits_qs.filter(membership_type="temp_close").count()

        ctx.update(f)
        ctx.update({
            "page_title": "Employee Security Deposits Report",
            "deposits_list": deposits_qs.order_by("full_name"),
            "total_active_members": total_active_members,
            "total_deposits_held": total_deposits_held,
            "total_temp_close": total_temp_close,
            "report_type": "deposits",
        })
        return ctx


class IssuanceRequestsReportView(StaffRequiredMixin, TemplateView):
    """5. Token Issuance Requests Report."""
    template_name = "reports/issuance_requests_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = get_common_report_filters(self.request)

        issuance_req_qs = TokenOpenCloseRequest.objects.filter(
            tenant=f["tenant"],
            request_type=RequestType.OPEN,
            created_at__date__gte=f["start_date"],
            created_at__date__lte=f["end_date"],
        ).select_related("employee", "employee__department", "acknowledged_by")

        if f["emp_id"] and f["emp_id"].isdigit():
            issuance_req_qs = issuance_req_qs.filter(employee_id=int(f["emp_id"]))
        if f["dept_id"] and f["dept_id"].isdigit():
            issuance_req_qs = issuance_req_qs.filter(employee__department_id=int(f["dept_id"]))

        ctx.update(f)
        ctx.update({
            "page_title": "Token Issuance Requests Report",
            "issuance_requests": issuance_req_qs.order_by("-created_at"),
            "report_type": "issuance_requests",
        })
        return ctx


class ClosureRequestsReportView(StaffRequiredMixin, TemplateView):
    """6. Token Closure Requests Report."""
    template_name = "reports/closure_requests_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = get_common_report_filters(self.request)

        closure_req_qs = TokenOpenCloseRequest.objects.filter(
            tenant=f["tenant"],
            request_type=RequestType.CLOSE,
            created_at__date__gte=f["start_date"],
            created_at__date__lte=f["end_date"],
        ).select_related("employee", "employee__department", "acknowledged_by")

        if f["emp_id"] and f["emp_id"].isdigit():
            closure_req_qs = closure_req_qs.filter(employee_id=int(f["emp_id"]))
        if f["dept_id"] and f["dept_id"].isdigit():
            closure_req_qs = closure_req_qs.filter(employee__department_id=int(f["dept_id"]))

        ctx.update(f)
        ctx.update({
            "page_title": "Token Closure Requests Report",
            "closure_requests": closure_req_qs.order_by("-created_at"),
            "report_type": "closure_requests",
        })
        return ctx


class BillingReportView(StaffRequiredMixin, TemplateView):
    """7. Billing & Collections Summary Report."""
    template_name = "reports/billing_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = get_common_report_filters(self.request)

        bills_qs = MonthlyBill.objects.filter(
            tenant=f["tenant"],
            period_start__lte=f["end_date"],
            period_end__gte=f["start_date"],
        ).select_related("employee", "employee__department")

        if f["emp_id"] and f["emp_id"].isdigit():
            bills_qs = bills_qs.filter(employee_id=int(f["emp_id"]))
        if f["dept_id"] and f["dept_id"].isdigit():
            bills_qs = bills_qs.filter(employee__department_id=int(f["dept_id"]))

        billing_total_billed = bills_qs.aggregate(t=Sum("total"))["t"] or 0
        billing_total_paid = bills_qs.filter(status=BillStatus.PAID).aggregate(t=Sum("total"))["t"] or 0
        billing_outstanding = billing_total_billed - billing_total_paid

        ctx.update(f)
        ctx.update({
            "page_title": "Billing & Collections Summary Report",
            "bills_list": bills_qs.order_by("-period_start"),
            "billing_total_billed": billing_total_billed,
            "billing_total_paid": billing_total_paid,
            "billing_outstanding": billing_outstanding,
            "report_type": "billing",
        })
        return ctx


class ExportReportCSVView(StaffRequiredMixin, View):
    """Universal CSV Exporter respecting all filters for any selected report."""
    def get(self, request):
        f = get_common_report_filters(request)
        report_type = request.GET.get("report_type", "tokens").strip()

        response = HttpResponse(content_type="text/csv")
        filename = f"{report_type}_report_{f['start_date']}_to_{f['end_date']}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)

        if report_type == "pos_misc":
            writer.writerow(["#", "Date/Time", "Order Ref", "Item Name", "Qty", "Unit Price", "Total (PKR)", "Buyer Name", "P-No", "Type"])
            pos_qs = TeaItemSale.objects.filter(tenant=f["tenant"], date__gte=f["start_date"], date__lte=f["end_date"]).annotate(
                total_val=ExpressionWrapper(F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=10, decimal_places=2))
            ).select_related("item", "buyer")
            if f["emp_id"] and f["emp_id"].isdigit():
                pos_qs = pos_qs.filter(buyer_id=int(f["emp_id"]))
            for idx, sale in enumerate(pos_qs.order_by("-created_at"), 1):
                writer.writerow([
                    idx, sale.created_at.strftime("%Y-%m-%d %H:%M"), sale.order_reference, sale.item.name,
                    sale.quantity, float(sale.unit_price), float(sale.total_val),
                    sale.buyer.full_name if sale.buyer else "Walk-in", sale.buyer.pno if sale.buyer else "—",
                    "Walk-in" if sale.is_walk_in else "Member"
                ])

        elif report_type == "deposits":
            writer.writerow(["#", "Employee Name", "P-No", "Department", "Membership Status", "Membership Type", "Security Deposit (PKR)", "Date Joined"])
            emp_qs = Employee.objects.filter(tenant=f["tenant"]).select_related("department")
            if f["dept_id"] and f["dept_id"].isdigit():
                emp_qs = emp_qs.filter(department_id=int(f["dept_id"]))
            for idx, emp in enumerate(emp_qs.order_by("full_name"), 1):
                writer.writerow([
                    idx, emp.full_name, emp.pno or "—", emp.department.name if emp.department else "General",
                    "Active" if emp.membership_status else "Inactive", emp.get_membership_type_display(),
                    float(emp.security_deposit_paid or 0), emp.date_joined.strftime("%Y-%m-%d") if emp.date_joined else "—"
                ])

        elif report_type == "issuance_requests":
            writer.writerow(["#", "Request Date", "Employee Name", "P-No", "Department", "Requested Period", "Reason", "Status"])
            req_qs = TokenOpenCloseRequest.objects.filter(tenant=f["tenant"], request_type=RequestType.OPEN, created_at__date__gte=f["start_date"], created_at__date__lte=f["end_date"]).select_related("employee", "employee__department")
            for idx, req in enumerate(req_qs.order_by("-created_at"), 1):
                writer.writerow([
                    idx, req.created_at.strftime("%Y-%m-%d"), req.employee.full_name, req.employee.pno or "—",
                    req.employee.department.name if req.employee.department else "General",
                    f"{req.date_range_start} to {req.date_range_end}", req.reason, req.get_status_display()
                ])

        elif report_type == "closure_requests":
            writer.writerow(["#", "Request Date", "Employee Name", "P-No", "Department", "Closure Period", "Reason", "Status"])
            req_qs = TokenOpenCloseRequest.objects.filter(tenant=f["tenant"], request_type=RequestType.CLOSE, created_at__date__gte=f["start_date"], created_at__date__lte=f["end_date"]).select_related("employee", "employee__department")
            for idx, req in enumerate(req_qs.order_by("-created_at"), 1):
                writer.writerow([
                    idx, req.created_at.strftime("%Y-%m-%d"), req.employee.full_name, req.employee.pno or "—",
                    req.employee.department.name if req.employee.department else "General",
                    f"{req.date_range_start} to {req.date_range_end}", req.reason, req.get_status_display()
                ])

        else:
            # Default: Monthly Lunch Token Summary
            writer.writerow(["#", "Employee Name", "P-No", "Department", "Tokens Issued", "Extra Roti", "Extra Sweets", "Days Attended"])
            tokens_qs = LunchToken.objects.filter(tenant=f["tenant"], date__gte=f["start_date"], date__lte=f["end_date"], status=TokenStatus.ISSUED).select_related("employee", "employee__department")
            summary = tokens_qs.values("employee__full_name", "employee__pno", "employee__department__name").annotate(
                total_tokens=Sum("token_qty"), total_roti=Sum("extra_roti_qty"), total_sweet=Sum("extra_sweet_qty"), days_attended=Count("date", distinct=True)
            ).order_by("-total_tokens")
            for idx, row in enumerate(summary, 1):
                writer.writerow([
                    idx, row["employee__full_name"], row["employee__pno"] or "—", row["employee__department__name"] or "General",
                    row["total_tokens"], row["total_roti"], row["total_sweet"], row["days_attended"]
                ])

        return response


class ExportTokenReportCSVView(ExportReportCSVView):
    """Legacy alias for token export."""
    pass


class ExportBillingReportCSVView(ExportReportCSVView):
    """Legacy alias for billing export."""
    pass


# ── Member Authorized Reports Views ──────────────────────────────────────────

from apps.core.mixins import EmployeeRequiredMixin


class MyReportsIndexView(EmployeeRequiredMixin, TemplateView):
    """Member Reports Hub index rendering a grid of 4 member reports."""
    template_name = "reports/my_reports_index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "My Cafeteria Reports"
        return ctx


class MyTokenReportView(EmployeeRequiredMixin, TemplateView):
    """1. My Monthly Token Summary & Attendance Log."""
    template_name = "reports/my_token_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = get_common_report_filters(self.request)
        employee = getattr(self.request.user, "employee_profile", None)

        tokens_list = []
        total_tokens = 0
        total_roti = 0
        total_sweet = 0

        if employee:
            tokens_qs = LunchToken.objects.filter(
                tenant=f["tenant"],
                employee=employee,
                date__gte=f["start_date"],
                date__lte=f["end_date"],
                status=TokenStatus.ISSUED,
            ).select_related("daily_estimate").order_by("-date", "-issue_time")

            tokens_list = tokens_qs
            total_tokens = tokens_qs.aggregate(t=Sum("token_qty"))["t"] or 0
            total_roti = tokens_qs.aggregate(r=Sum("extra_roti_qty"))["r"] or 0
            total_sweet = tokens_qs.aggregate(s=Sum("extra_sweet_qty"))["s"] or 0

        ctx.update(f)
        ctx.update({
            "page_title": "My Token Summary & Attendance Log",
            "tokens_list": tokens_list,
            "total_tokens": total_tokens,
            "total_roti": total_roti,
            "total_sweet": total_sweet,
            "employee": employee,
        })
        return ctx


class MyPOSReportView(EmployeeRequiredMixin, TemplateView):
    """2. My Tea & Snack POS Purchase History."""
    template_name = "reports/my_pos_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = get_common_report_filters(self.request)
        employee = getattr(self.request.user, "employee_profile", None)

        pos_sales = []
        pos_total_spend = 0
        pos_total_items = 0

        if employee:
            pos_qs = TeaItemSale.objects.filter(
                tenant=f["tenant"],
                buyer=employee,
                date__gte=f["start_date"],
                date__lte=f["end_date"],
            ).annotate(
                total_val=ExpressionWrapper(F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=10, decimal_places=2))
            ).select_related("item").order_by("-created_at")

            if f["q"]:
                pos_qs = pos_qs.filter(Q(item__name__icontains=f["q"]) | Q(order_reference__icontains=f["q"]))

            pos_total_spend = pos_qs.aggregate(t=Sum("total_val"))["t"] or 0
            pos_total_items = pos_qs.aggregate(q=Sum("quantity"))["q"] or 0

            paginator = Paginator(pos_qs, 25)
            page_obj = paginator.get_page(self.request.GET.get("page", 1))
            pos_sales = page_obj.object_list
            ctx["page_obj"] = page_obj
            ctx["is_paginated"] = page_obj.has_other_pages()

        ctx.update(f)
        ctx.update({
            "page_title": "My POS Purchase History",
            "pos_sales": pos_sales,
            "pos_total_spend": pos_total_spend,
            "pos_total_items": pos_total_items,
            "employee": employee,
        })
        return ctx


class MyBillingReportView(EmployeeRequiredMixin, TemplateView):
    """3. My Account Financial Statement & Monthly Bills."""
    template_name = "reports/my_billing_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = get_common_report_filters(self.request)
        employee = getattr(self.request.user, "employee_profile", None)

        bills_list = []
        total_billed = 0
        total_paid = 0
        total_outstanding = 0

        if employee:
            bills_qs = MonthlyBill.objects.filter(
                tenant=f["tenant"],
                employee=employee,
                period_start__lte=f["end_date"],
                period_end__gte=f["start_date"],
                status__in=[BillStatus.UNPAID, BillStatus.PARTIALLY_PAID, BillStatus.PAID]
            ).order_by("-period_start")

            bills_list = bills_qs
            total_billed = bills_qs.aggregate(t=Sum("total"))["t"] or 0
            total_paid = bills_qs.filter(status=BillStatus.PAID).aggregate(t=Sum("total"))["t"] or 0
            total_outstanding = total_billed - total_paid

        ctx.update(f)
        ctx.update({
            "page_title": "My Monthly Invoices & Financial Statement",
            "bills_list": bills_list,
            "total_billed": total_billed,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
            "employee": employee,
        })
        return ctx


class MyRequestsReportView(EmployeeRequiredMixin, TemplateView):
    """4. My Token Open/Close Requests History."""
    template_name = "reports/my_requests_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = get_common_report_filters(self.request)
        employee = getattr(self.request.user, "employee_profile", None)

        requests_list = []
        if employee:
            req_qs = TokenOpenCloseRequest.objects.filter(
                tenant=f["tenant"],
                employee=employee,
                created_at__date__gte=f["start_date"],
                created_at__date__lte=f["end_date"],
            ).select_related("acknowledged_by").order_by("-created_at")

            requests_list = req_qs

        ctx.update(f)
        ctx.update({
            "page_title": "My Token Requests History",
            "requests_list": requests_list,
            "employee": employee,
        })
        return ctx
