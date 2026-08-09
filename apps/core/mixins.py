"""Core App – Mixins for role-based access control."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin that enforces role-based access at the view level.
    Set `allowed_roles` as a list of UserRole values on the view.

    Example::

        class MyView(RoleRequiredMixin, View):
            allowed_roles = [UserRole.ADMIN, UserRole.CAFE_STAFF]
    """
    allowed_roles = []
    permission_denied_message = "You do not have permission to access this page."

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if self.allowed_roles and request.user.role not in self.allowed_roles:
            messages.error(request, self.permission_denied_message)
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    """Restricts access to Admin users only."""
    def get_allowed_roles(self):
        from apps.accounts.models import UserRole
        return [UserRole.ADMIN]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        from apps.accounts.models import UserRole
        if request.user.role != UserRole.ADMIN:
            raise PermissionDenied
        return super(RoleRequiredMixin, self).dispatch(request, *args, **kwargs)


class StaffRequiredMixin(RoleRequiredMixin):
    """Restricts access to Admin, Cafe Staff, Committee Member, or Super Admin."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        from apps.accounts.models import UserRole
        allowed = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CAFE_STAFF, UserRole.COMMITTEE_MEMBER]
        if request.user.role not in allowed:
            raise PermissionDenied
        return super(RoleRequiredMixin, self).dispatch(request, *args, **kwargs)


class CommitteeRequiredMixin(RoleRequiredMixin):
    """Restricts access to Admin or Committee Members (bill approval etc.)."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        from apps.accounts.models import UserRole
        if request.user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.COMMITTEE_MEMBER]:
            raise PermissionDenied
        return super(RoleRequiredMixin, self).dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(RoleRequiredMixin):
    """Restricts access to Super Admin only."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        from apps.accounts.models import UserRole
        if request.user.role != UserRole.SUPER_ADMIN:
            raise PermissionDenied
        return super(RoleRequiredMixin, self).dispatch(request, *args, **kwargs)


class TenantMixin:
    """
    Mixin that injects the current tenant from request into the view context.
    """
    def get_current_tenant(self):
        return getattr(self.request, "tenant", None)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_tenant"] = self.get_current_tenant()
        return ctx


class EmployeeRequiredMixin(LoginRequiredMixin):
    """
    Mixin ensuring that only users with an associated employee profile (or Employee role)
    can access personal member views. If an Admin without an employee profile visits,
    they are redirected to their Executive Admin views.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        from apps.accounts.models import UserRole
        has_profile = hasattr(request.user, "employee_profile") and request.user.employee_profile is not None
        if not has_profile and request.user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CAFE_STAFF]:
            if "reports" in request.path:
                messages.info(request, "Redirected to Executive Reports Hub.")
                return redirect("reports:index")
            return redirect("core:admin_dashboard")

        return super().dispatch(request, *args, **kwargs)

