"""Notifications App – Views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, View
from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import redirect

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 30

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Notifications"
        return ctx


class MarkReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        Notification.objects.filter(pk=pk, recipient=request.user).update(
            is_read=True, read_at=timezone.now()
        )
        if request.headers.get("HX-Request"):
            return JsonResponse({"status": "ok"})
        return redirect("notifications:list")


class MarkAllReadView(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return redirect("notifications:list")


class UnreadCountView(LoginRequiredMixin, View):
    """API endpoint for navbar bell badge."""
    def get(self, request):
        from apps.requests_app.models import TokenOpenCloseRequest, RequestStatus
        tenant = getattr(request, "tenant", None)
        unread = Notification.objects.filter(recipient=request.user, is_read=False).count()
        pending_requests = 0
        if request.user.is_staff:
            pending_requests = TokenOpenCloseRequest.objects.filter(
                tenant=tenant, status=RequestStatus.PENDING
            ).count()
        return JsonResponse({
            "count": unread,
            "pending_requests": pending_requests,
        })
