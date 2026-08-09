"""Requests App – Views (Open/Close Token Requests)."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from apps.core.mixins import StaffRequiredMixin
from apps.employees.models import Employee
from .models import TokenOpenCloseRequest, RequestStatus, RequestType
from .forms import RequestForm, RequestAcknowledgeForm


class RequestListView(StaffRequiredMixin, ListView):
    """Staff/Admin view: all open/close requests."""
    model = TokenOpenCloseRequest
    template_name = "requests_app/request_list.html"
    context_object_name = "requests"
    paginate_by = 30

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        qs = TokenOpenCloseRequest.objects.filter(
            tenant=tenant
        ).select_related("employee", "acknowledged_by").order_by("-submitted_at")

        status_filter = self.request.GET.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        ctx["page_title"] = "Open/Close Requests"
        ctx["status_choices"] = RequestStatus.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["pending_count"] = TokenOpenCloseRequest.objects.filter(
            tenant=tenant, status=RequestStatus.PENDING
        ).count()
        return ctx


class RequestDetailView(StaffRequiredMixin, DetailView):
    model = TokenOpenCloseRequest
    template_name = "requests_app/request_detail.html"
    context_object_name = "req"

    def get_queryset(self):
        return TokenOpenCloseRequest.objects.filter(
            tenant=getattr(self.request, "tenant", None)
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"Request #{self.object.pk}"
        ctx["acknowledge_form"] = RequestAcknowledgeForm()
        return ctx


class RequestAcknowledgeView(StaffRequiredMixin, View):
    """Acknowledge (approve) a pending request."""
    def post(self, request, pk):
        tenant = getattr(request, "tenant", None)
        req = get_object_or_404(TokenOpenCloseRequest, pk=pk, tenant=tenant, status=RequestStatus.PENDING)
        form = RequestAcknowledgeForm(request.POST)

        if form.is_valid():
            req.status = RequestStatus.ACKNOWLEDGED
            req.acknowledged_by = request.user
            req.acknowledged_at = timezone.now()
            req.save(update_fields=["status", "acknowledged_by", "acknowledged_at"])

            # Notify employee
            employee = req.employee
            if employee.user:
                from apps.notifications.services import create_notification
                from apps.notifications.models import NotificationType
                create_notification(
                    tenant=tenant,
                    recipient=employee.user,
                    notification_type=NotificationType.REQUEST_ACKNOWLEDGED,
                    title=f"Request {req.get_request_type_display()} Acknowledged",
                    message=f"Your {req.get_request_type_display().lower()} request for {req.date_range_start} – {req.date_range_end} has been acknowledged.",
                    link=f"/requests/my/",
                    actor=request.user,
                )

            messages.success(request, f"Request #{pk} acknowledged.")
        else:
            messages.error(request, "Failed to acknowledge request.")

        return redirect("requests_app:list")


class RequestRejectView(StaffRequiredMixin, View):
    """Reject a pending request with a reason."""
    def post(self, request, pk):
        tenant = getattr(request, "tenant", None)
        req = get_object_or_404(TokenOpenCloseRequest, pk=pk, tenant=tenant, status=RequestStatus.PENDING)
        reason = request.POST.get("rejection_reason", "").strip()
        req.status = RequestStatus.REJECTED
        req.acknowledged_by = request.user
        req.acknowledged_at = timezone.now()
        req.rejection_reason = reason
        req.save(update_fields=["status", "acknowledged_by", "acknowledged_at", "rejection_reason"])

        # Notify employee
        employee = req.employee
        if employee.user:
            from apps.notifications.services import create_notification
            from apps.notifications.models import NotificationType
            create_notification(
                tenant=tenant,
                recipient=employee.user,
                notification_type=NotificationType.REQUEST_REJECTED,
                title="Request Rejected",
                message=f"Your {req.get_request_type_display().lower()} request has been rejected. Reason: {reason or 'Not specified'}",
                link="/requests/my/",
                actor=request.user,
            )

        messages.warning(request, f"Request #{pk} rejected.")
        return redirect("requests_app:list")


# ── Employee Self-Service ────────────────────────────────────────────────────

class MyRequestListView(LoginRequiredMixin, ListView):
    """Employee: view their own requests."""
    model = TokenOpenCloseRequest
    template_name = "requests_app/my_requests.html"
    context_object_name = "requests"

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        try:
            employee = self.request.user.employee_profile
        except Exception:
            return TokenOpenCloseRequest.objects.none()
        return TokenOpenCloseRequest.objects.filter(
            tenant=tenant, employee=employee
        ).order_by("-submitted_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "My Open/Close Requests"
        ctx["form"] = RequestForm(tenant=getattr(self.request, "tenant", None))
        return ctx


class MyRequestCreateView(LoginRequiredMixin, CreateView):
    """Employee: submit a new open/close request."""
    model = TokenOpenCloseRequest
    form_class = RequestForm
    template_name = "requests_app/my_requests.html"
    success_url = reverse_lazy("requests_app:my_requests")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = getattr(self.request, "tenant", None)
        return kwargs

    def form_valid(self, form):
        tenant = getattr(self.request, "tenant", None)
        try:
            form.instance.employee = self.request.user.employee_profile
        except Exception:
            messages.error(self.request, "You do not have an employee profile.")
            return redirect("requests_app:my_requests")

        form.instance.tenant = tenant
        messages.success(self.request, "Request submitted successfully.")

        # Notify staff
        from apps.notifications.services import notify_staff
        from apps.notifications.models import NotificationType
        notify_staff(
            tenant=tenant,
            notification_type=NotificationType.REQUEST_SUBMITTED,
            title=f"New {form.instance.get_request_type_display()} Request",
            message=f"{form.instance.employee.full_name} submitted a {form.instance.get_request_type_display().lower()} request.",
            link="/requests/",
            actor=self.request.user,
        )
        return super().form_valid(form)


class MyRequestCancelView(LoginRequiredMixin, View):
    """Employee: cancel their own request (only if before cutoff)."""
    def post(self, request, pk):
        tenant = getattr(request, "tenant", None)
        try:
            employee = request.user.employee_profile
        except Exception:
            messages.error(request, "No employee profile found.")
            return redirect("requests_app:my_requests")

        req = get_object_or_404(TokenOpenCloseRequest, pk=pk, tenant=tenant, employee=employee)

        if not req.can_be_cancelled_by_employee:
            messages.error(request, "This request can no longer be cancelled. The cutoff has passed.")
            return redirect("requests_app:my_requests")

        req.status = RequestStatus.CANCELLED
        req.save(update_fields=["status"])
        messages.success(request, "Request cancelled.")
        return redirect("requests_app:my_requests")
