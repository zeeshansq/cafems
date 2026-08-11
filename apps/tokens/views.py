"""Tokens App – Views (Lunch Token Issuance)."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count, Q

from apps.core.mixins import StaffRequiredMixin, AdminRequiredMixin
from apps.employees.models import Employee, AuditLog, MembershipType
from apps.menu.models import DailyLunchEstimate
from apps.requests_app.models import TokenOpenCloseRequest, RequestType, RequestStatus
from .models import LunchToken, TokenStatus
from .forms import TokenIssueForm


class TokenIssueView(StaffRequiredMixin, TemplateView):
    """
    Lunch token issuance screen.
    Shows daily counter: Issued X / Estimated Y (color-coded).
    Enforces: 1 per member by default, max 3, Roti-Open lock.
    """
    template_name = "tokens/issue.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        user = self.request.user
        is_admin = user.is_superuser or getattr(user, "role", None) in ["super_admin", "admin"]
        today = timezone.localdate()

        import datetime
        date_str = self.request.GET.get("date")
        if is_admin and date_str:
            try:
                target_date = datetime.date.fromisoformat(date_str)
            except (ValueError, TypeError):
                target_date = today
        else:
            target_date = today

        # Daily estimate
        try:
            estimate = DailyLunchEstimate.objects.get(tenant=tenant, date=target_date)
        except DailyLunchEstimate.DoesNotExist:
            estimate = None

        # Today's issued count (Sum of token_qty)
        from django.db.models import Sum
        issued_today = LunchToken.objects.filter(
            tenant=tenant, date=target_date, status=TokenStatus.ISSUED
        ).aggregate(total=Sum("token_qty"))["total"] or 0

        close_reqs = TokenOpenCloseRequest.objects.filter(
            tenant=tenant,
            request_type=RequestType.CLOSE,
            status=RequestStatus.ACKNOWLEDGED,
            date_range_start__lte=target_date,
            date_range_end__gte=target_date,
        )
        close_requests_map = {r.employee_id: r for r in close_reqs}
        close_requests_today = list(close_requests_map.keys())

        open_reqs = TokenOpenCloseRequest.objects.filter(
            tenant=tenant,
            request_type=RequestType.OPEN,
            status=RequestStatus.ACKNOWLEDGED,
            date_range_start__lte=target_date,
            date_range_end__gte=target_date,
        )
        open_requests_map = {r.employee_id: r for r in open_reqs}
        open_requests_today = list(open_requests_map.keys())

        eligible_employees = (
            Employee.objects.filter(tenant=tenant, is_active=True, membership_status=True)
            .exclude(membership_type=MembershipType.NOT_MEMBER)
            .select_related("department")
            .order_by("full_name")
        )

        today_tokens_map = {
            tok.employee_id: tok
            for tok in LunchToken.objects.filter(
                tenant=tenant, date=target_date, status=TokenStatus.ISSUED
            )
        }

        employees_json = []
        for emp in eligible_employees:
            existing_tok = today_tokens_map.get(emp.pk)
            open_req = open_requests_map.get(emp.pk)
            close_req = close_requests_map.get(emp.pk)
            employees_json.append({
                "id": emp.pk,
                "full_name": emp.full_name,
                "pno": emp.pno or "N/A",
                "designation": emp.designation or "Member",
                "department": emp.department.name if emp.department else "General",
                "membership_type": emp.get_membership_type_display(),
                "membership_code": emp.membership_type,
                "has_close_request": bool(close_req),
                "close_request_details": {
                    "id": close_req.pk,
                    "start_date": close_req.date_range_start.strftime("%b. %d, %Y"),
                    "end_date": close_req.date_range_end.strftime("%b. %d, %Y"),
                    "reason": close_req.reason,
                } if close_req else None,
                "has_open_request": bool(open_req),
                "open_request_details": {
                    "id": open_req.pk,
                    "requested_token_qty": open_req.requested_token_qty,
                    "start_date": open_req.date_range_start.strftime("%b. %d, %Y"),
                    "end_date": open_req.date_range_end.strftime("%b. %d, %Y"),
                    "reason": open_req.reason,
                } if open_req else None,
                "photo_url": emp.photo.url if emp.photo else None,
                "initials": emp.full_name[:2].upper(),
                "issued_today": bool(existing_tok),
                "existing_token": {
                    "id": existing_tok.pk,
                    "token_number": existing_tok.token_number,
                    "token_qty": existing_tok.token_qty,
                    "extra_roti_qty": existing_tok.extra_roti_qty,
                    "extra_sweet_qty": existing_tok.extra_sweet_qty,
                } if existing_tok else None,
            })

        planned_count = estimate.planned_count if estimate else 0
        remaining_count = max(0, planned_count - issued_today)
        pct_count = (issued_today / planned_count * 100) if planned_count > 0 else 0

        recent_tokens = LunchToken.objects.filter(
            tenant=tenant, date=target_date, status=TokenStatus.ISSUED
        ).select_related("employee", "issued_by").order_by("-issue_time")[:10]

        is_menu_configured = bool(estimate and estimate.dish_name and estimate.dish_name.strip())

        ctx.update({
            "page_title": f"Issue Lunch Tokens ({target_date})" if target_date != today else "Issue Lunch Tokens",
            "today": today,
            "target_date": target_date,
            "is_admin": is_admin,
            "estimate": estimate,
            "is_menu_configured": is_menu_configured,
            "issued": issued_today,
            "planned": planned_count,
            "remaining": remaining_count,
            "pct": pct_count,
            "tokens": recent_tokens,
            "issued_today": issued_today,
            "next_token_number": issued_today + 1,
            "estimated_count": planned_count,
            "employees": eligible_employees,
            "employees_json": employees_json,
            "issued_employee_ids": list(today_tokens_map.keys()),
            "form": TokenIssueForm(tenant=tenant),
        })
        return ctx

    def post(self, request, *args, **kwargs):
        tenant = getattr(request, "tenant", None)
        user = request.user
        is_admin = user.is_superuser or getattr(user, "role", None) in ["super_admin", "admin"]
        today = timezone.localdate()

        import datetime
        date_str = request.POST.get("date") or request.GET.get("date")
        if is_admin and date_str:
            try:
                target_date = datetime.date.fromisoformat(date_str)
            except (ValueError, TypeError):
                target_date = today
        else:
            target_date = today

        # Check if lunch menu main item is configured for target_date
        try:
            estimate = DailyLunchEstimate.objects.get(tenant=tenant, date=target_date)
            is_menu_configured = bool(estimate.dish_name and estimate.dish_name.strip())
        except DailyLunchEstimate.DoesNotExist:
            is_menu_configured = False

        form = TokenIssueForm(request.POST, tenant=tenant)

        if not form.is_valid():
            err_msg = ", ".join([f"{k}: {v[0]}" for k, v in form.errors.items()])
            if request.headers.get("HX-Request"):
                return JsonResponse({"error": err_msg}, status=400)
            messages.error(request, f"Form error: {err_msg}")
            return self.get(request, *args, **kwargs)

        employee = form.cleaned_data["employee"]
        token_qty = int(form.cleaned_data.get("token_qty") or request.POST.get("token_qty") or 0)
        extra_roti = int(form.cleaned_data.get("extra_roti_qty") or request.POST.get("extra_roti_qty") or 0)
        extra_sweet = int(form.cleaned_data.get("extra_sweet_qty") or request.POST.get("extra_sweet_qty") or 0)
        is_roti_override = bool(form.cleaned_data.get("roti_override") or request.POST.get("roti_override"))

        if not is_menu_configured and not is_roti_override:
            msg = f"Issuance Restricted: Daily lunch menu item has not been entered for {target_date}. Please configure the daily menu before issuing tokens."
            if request.headers.get("HX-Request"):
                return JsonResponse({"error": msg}, status=400)
            messages.error(request, msg)
            return redirect(f"/tokens/issue/?date={target_date}" if target_date != today else "tokens:issue")

        # Check Acknowledged Close Requests for target_date
        from apps.requests_app.models import TokenOpenCloseRequest, RequestType, RequestStatus
        close_req = TokenOpenCloseRequest.objects.filter(
            tenant=tenant,
            employee=employee,
            request_type=RequestType.CLOSE,
            status=RequestStatus.ACKNOWLEDGED,
            date_range_start__lte=target_date,
            date_range_end__gte=target_date,
        ).first()

        if close_req and not is_roti_override:
            msg = f"Issuance Restricted: Token service is Closed via Request #{close_req.pk} for {employee.full_name} ({close_req.date_range_start} to {close_req.date_range_end}). Authorize Staff Override to issue."
            if request.headers.get("HX-Request"):
                return JsonResponse({"error": msg}, status=400)
            messages.error(request, msg)
            return redirect(f"/tokens/issue/?date={target_date}" if target_date != today else "tokens:issue")

        # Check Roti-Open lock (staff override is ONLY required if requesting Lunch Tokens or Extra Sweet)
        if employee.is_roti_open and (token_qty > 0 or extra_sweet > 0) and not is_roti_override:
            msg = f"{employee.full_name} is Roti-Open. Authorize staff override to issue Lunch Tokens or Extra Sweet."
            if request.headers.get("HX-Request"):
                return JsonResponse({"error": msg}, status=400)
            messages.error(request, msg)
            return redirect(f"/tokens/issue/?date={target_date}" if target_date != today else "tokens:issue")

        # Check Temp Close lock
        if employee.is_temp_close and not is_roti_override:
            msg = f"{employee.full_name} is Temp Close / Closed Today. Authorize staff override."
            if request.headers.get("HX-Request"):
                return JsonResponse({"error": msg}, status=400)
            messages.error(request, msg)
            return redirect(f"/tokens/issue/?date={target_date}" if target_date != today else "tokens:issue")

        # Check existing token today for this employee
        existing_token = LunchToken.objects.filter(
            tenant=tenant, employee=employee, date=target_date, status=TokenStatus.ISSUED
        ).first()

        if existing_token:
            if not is_roti_override:
                msg = f"Token Already Issued! {employee.full_name} has already received a lunch token today. Enable override to update."
                if request.headers.get("HX-Request"):
                    return JsonResponse({"error": msg}, status=400)
                messages.error(request, msg)
                return redirect(f"/tokens/issue/?date={target_date}" if target_date != today else "tokens:issue")

            # Override & update existing record in-place
            existing_token.token_qty = token_qty
            existing_token.extra_roti_qty = extra_roti
            existing_token.extra_sweet_qty = extra_sweet
            existing_token.roti_override = True
            existing_token.save()

            AuditLog.objects.create(
                tenant=tenant,
                actor=request.user,
                action="update_existing_token_override",
                model_name="LunchToken",
                object_id=str(existing_token.pk),
                note=f"Overrode/updated token #{existing_token.token_number} for {employee.full_name} on {target_date} (Token Qty: {token_qty}, Roti: {extra_roti}, Sweet: {extra_sweet})",
            )

            messages.success(request, f"Updated & overrode existing Token #{existing_token.token_number} for {employee.full_name} on {target_date}.")
            return redirect(f"/tokens/issue/?date={target_date}" if target_date != today else "tokens:issue")

        # Get estimate for this day
        try:
            estimate = DailyLunchEstimate.objects.get(tenant=tenant, date=target_date)
            if not estimate.is_locked:
                estimate.is_locked = True
                estimate.save(update_fields=["is_locked"])
        except DailyLunchEstimate.DoesNotExist:
            estimate = None

        today_issuance_count = LunchToken.objects.filter(
            tenant=tenant, date=target_date
        ).count()

        token = LunchToken.objects.create(
            tenant=tenant,
            date=target_date,
            employee=employee,
            token_number=today_issuance_count + 1,
            token_qty=token_qty,
            issued_by=request.user,
            extra_roti_qty=extra_roti,
            extra_sweet_qty=extra_sweet,
            status=TokenStatus.ISSUED,
            roti_override=is_roti_override,
            daily_estimate=estimate,
        )

        # If Roti-Open override — log it
        if is_roti_override:
            AuditLog.objects.create(
                tenant=tenant,
                actor=request.user,
                action="roti_open_override",
                model_name="LunchToken",
                object_id=str(token.pk),
                note=f"Roti-Open override for {employee.full_name} on {target_date}",
            )

        # Create notification for employee (if they have a user account)
        if employee.user:
            from apps.notifications.services import create_notification
            from apps.notifications.models import NotificationType
            create_notification(
                tenant=tenant,
                recipient=employee.user,
                notification_type=NotificationType.SYSTEM,
                title="Lunch Token Issued",
                message=f"Token #{token.token_number} ({token.token_qty} token/s) issued for {target_date}.",
                actor=request.user,
            )

        receipt_url = reverse_lazy("tokens:token_receipt", kwargs={"pk": token.pk})

        if request.headers.get("HX-Request"):
            return JsonResponse({
                "success": True,
                "token_number": token.token_number,
                "employee": employee.full_name,
                "qty": token.token_qty,
                "receipt_url": str(receipt_url),
            })

        messages.success(request, f"Token #{token.token_number} issued for {employee.full_name} ({target_date}).")
        return redirect(f"/tokens/issue/?receipt_token={token.pk}&date={target_date}")


class LunchTokenReceiptView(StaffRequiredMixin, TemplateView):
    """Compact 80mm thermal receipt printer template for Lunch Token Issuance."""
    template_name = "tokens/token_receipt.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        token_id = self.kwargs.get("pk")

        token = get_object_or_404(
            LunchToken.objects.select_related("employee", "employee__department", "issued_by", "daily_estimate"),
            tenant=tenant,
            pk=token_id,
        )

        ctx["page_title"] = f"Lunch Token Receipt #{token.token_number}"
        ctx["token"] = token
        ctx["employee"] = token.employee
        return ctx


class EstimateCounterView(StaffRequiredMixin, View):
    """htmx endpoint — returns live estimate counter HTML partial."""
    def get(self, request):
        tenant = getattr(request, "tenant", None)
        today = timezone.localdate()

        try:
            estimate = DailyLunchEstimate.objects.get(tenant=tenant, date=today)
            planned = estimate.planned_count
        except DailyLunchEstimate.DoesNotExist:
            planned = 0

        from django.db.models import Sum
        issued = LunchToken.objects.filter(
            tenant=tenant, date=today, status=TokenStatus.ISSUED
        ).aggregate(total=Sum("token_qty"))["total"] or 0

        remaining = max(0, planned - issued)
        pct = (issued / planned * 100) if planned > 0 else 0

        from django.template.loader import render_to_string
        html = render_to_string("tokens/partials/estimate_counter.html", {
            "planned": planned,
            "issued": issued,
            "remaining": remaining,
            "pct": pct,
        }, request=request)
        from django.http import HttpResponse
        return HttpResponse(html)


class RecentActivityView(StaffRequiredMixin, View):
    """htmx endpoint — returns recent token activity HTML partial for today."""
    def get(self, request):
        tenant = getattr(request, "tenant", None)
        today = timezone.localdate()
        recent = LunchToken.objects.filter(
            tenant=tenant, date=today, status=TokenStatus.ISSUED
        ).select_related(
            "employee", "issued_by"
        ).order_by("-issue_time")[:10]

        from django.template.loader import render_to_string
        from django.http import HttpResponse
        html = render_to_string("tokens/partials/recent_activity.html", {
            "tokens": recent,
        }, request=request)
        return HttpResponse(html)


class DailyClosingReportView(StaffRequiredMixin, TemplateView):
    """
    Daily closing report: employees who didn't issue a token
    and didn't submit a close request for today.
    Quick inline action: 'Charge Token' (retroactively creates a token).
    """
    template_name = "tokens/daily_closing_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        user = self.request.user
        is_admin = user.is_superuser or getattr(user, "role", None) in ["super_admin", "admin"]
        today = timezone.localdate()

        import datetime
        date_str = self.request.GET.get("date")
        if is_admin and date_str:
            try:
                report_date = datetime.date.fromisoformat(date_str)
            except (ValueError, TypeError):
                report_date = today
        else:
            report_date = today

        # All full-open members + temp-close with an open request for this date
        from apps.requests_app.models import TokenOpenCloseRequest, RequestType, RequestStatus
        open_requests = list(TokenOpenCloseRequest.objects.filter(
            tenant=tenant,
            request_type=RequestType.OPEN,
            status=RequestStatus.ACKNOWLEDGED,
            date_range_start__lte=report_date,
            date_range_end__gte=report_date,
        ).values_list("employee_id", flat=True))

        close_requests = list(TokenOpenCloseRequest.objects.filter(
            tenant=tenant,
            request_type=RequestType.CLOSE,
            status=RequestStatus.ACKNOWLEDGED,
            date_range_start__lte=report_date,
            date_range_end__gte=report_date,
        ).values_list("employee_id", flat=True))

        expected = Employee.objects.filter(
            Q(tenant=tenant, is_active=True, membership_status=True)
            | Q(pk__in=open_requests, tenant=tenant, is_active=True)
        ).exclude(pk__in=close_requests)

        issued_ids = list(LunchToken.objects.filter(
            tenant=tenant, date=report_date, status=TokenStatus.ISSUED
        ).values_list("employee_id", flat=True))

        charged_tokens = LunchToken.objects.filter(
            tenant=tenant, date=report_date, status=TokenStatus.ISSUED
        ).select_related("employee", "employee__department", "issued_by").order_by("-issue_time")

        missing = expected.exclude(pk__in=issued_ids)

        ctx.update({
            "page_title": f"Daily Closing Report — {report_date}",
            "report_date": report_date,
            "today": today,
            "is_admin": is_admin,
            "expected_employees": expected,
            "missing_employees": missing,
            "charged_tokens": charged_tokens,
            "issued_count": len(issued_ids),
            "expected_count": expected.count(),
            "missing_count": missing.count(),
        })
        return ctx


class ChargeTokenView(StaffRequiredMixin, View):
    """Retroactively charge a token for a specific employee on a date."""

    def _process_charge(self, request, employee_id):
        tenant = getattr(request, "tenant", None)
        employee = get_object_or_404(Employee, pk=employee_id, tenant=tenant)
        import datetime
        date_str = request.POST.get("date") or request.GET.get("date")
        today = timezone.localdate()
        try:
            target_date = datetime.date.fromisoformat(date_str) if date_str else today
        except (ValueError, TypeError):
            target_date = today

        # Cafe staff restriction: can only charge tokens for current date!
        is_admin = request.user.is_superuser or getattr(request.user, "role", None) in ["super_admin", "admin"]
        if not is_admin and target_date != today:
            messages.error(request, "Cafe staff can only charge tokens for today's date.")
            return redirect(f"/tokens/daily-report/?date={target_date}")

        existing = LunchToken.objects.filter(
            tenant=tenant, employee=employee, date=target_date, status=TokenStatus.ISSUED
        ).count()
        if existing >= 3:
            messages.error(request, f"Max tokens already issued for {employee.full_name} on {target_date}.")
            return redirect(f"/tokens/daily-report/?date={target_date}")

        today_issuance_count = LunchToken.objects.filter(
            tenant=tenant, date=target_date
        ).count()

        token = LunchToken.objects.create(
            tenant=tenant,
            date=target_date,
            employee=employee,
            token_number=today_issuance_count + 1,
            token_qty=1,
            issued_by=request.user,
            status=TokenStatus.ISSUED,
            is_retroactive=True,
        )

        AuditLog.objects.create(
            tenant=tenant,
            actor=request.user,
            action="charge_token_retroactive",
            model_name="LunchToken",
            object_id=str(token.pk),
            note=f"Retroactive token charge for {employee.full_name} on {target_date}",
        )
        messages.success(request, f"Token #{token.token_number} charged for {employee.full_name} on {target_date}.")
        return redirect(f"/tokens/daily-report/?date={target_date}")

    def get(self, request, employee_id):
        return self._process_charge(request, employee_id)

    def post(self, request, employee_id):
        return self._process_charge(request, employee_id)


class EmployeeTokenHistoryView(StaffRequiredMixin, TemplateView):
    """
    Token issuance history log.
    Staff/Admin can filter by any employee; regular employee members see their own history.
    """
    template_name = "tokens/employee_history.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        today = timezone.localdate()
        user = self.request.user

        is_staff_or_admin = user.role in ["super_admin", "admin", "cafe_staff", "committee_member"] or user.is_staff

        import datetime

        # Query parameters
        employee_id = self.request.GET.get("employee_id")
        q = self.request.GET.get("q", "").strip()
        start_date_str = self.request.GET.get("start_date")
        end_date_str = self.request.GET.get("end_date")
        status_filter = self.request.GET.get("status", "").strip()

        # Parse date range (default to current month: 1st of month to today)
        try:
            start_date = datetime.date.fromisoformat(start_date_str) if start_date_str else today.replace(day=1)
        except (ValueError, TypeError):
            start_date = today.replace(day=1)

        try:
            end_date = datetime.date.fromisoformat(end_date_str) if end_date_str else today
        except (ValueError, TypeError):
            end_date = today

        # Base queryset
        tokens_qs = LunchToken.objects.filter(
            tenant=tenant,
            date__gte=start_date,
            date__lte=end_date,
        ).select_related("employee", "employee__department", "issued_by")

        # Employee Filter & Data Authorization
        selected_employee = None
        if not is_staff_or_admin:
            try:
                selected_employee = user.employee_profile
                tokens_qs = tokens_qs.filter(employee=selected_employee)
            except Exception:
                tokens_qs = LunchToken.objects.none()
        else:
            if employee_id and employee_id.isdigit():
                try:
                    selected_employee = Employee.objects.get(pk=int(employee_id), tenant=tenant)
                    tokens_qs = tokens_qs.filter(employee=selected_employee)
                except Employee.DoesNotExist:
                    pass

        if q:
            tokens_qs = tokens_qs.filter(
                Q(employee__full_name__icontains=q) |
                Q(employee__pno__icontains=q)
            )

        if status_filter:
            tokens_qs = tokens_qs.filter(status=status_filter)

        tokens_qs = tokens_qs.order_by("-date", "-issue_time")

        # KPI Aggregations
        from django.db.models import Sum
        total_tokens = tokens_qs.aggregate(t=Sum("token_qty"))["t"] or 0
        total_roti = tokens_qs.aggregate(r=Sum("extra_roti_qty"))["r"] or 0
        total_sweet = tokens_qs.aggregate(s=Sum("extra_sweet_qty"))["s"] or 0
        total_days = tokens_qs.values("date").distinct().count()

        # Pagination (25 entries per page)
        from django.core.paginator import Paginator
        paginator = Paginator(tokens_qs, 25)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        # All employees dropdown list
        all_employees = Employee.objects.filter(tenant=tenant, is_active=True).select_related("department").order_by("full_name")

        ctx.update({
            "page_title": "Employee Token Issuance History",
            "today": today,
            "tokens": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
            "is_paginated": page_obj.has_other_pages(),
            "selected_employee": selected_employee,
            "current_emp_id": int(employee_id) if (employee_id and employee_id.isdigit()) else "",
            "current_q": q,
            "start_date": start_date,
            "end_date": end_date,
            "current_status": status_filter,
            "total_tokens": total_tokens,
            "total_roti": total_roti,
            "total_sweet": total_sweet,
            "total_days": total_days,
            "all_employees": all_employees,
            "status_choices": TokenStatus.choices,
        })
        return ctx

