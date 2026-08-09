"""Accounts App – Views."""
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect

from .forms import CafeLoginForm, ProfileForm, ChangePasswordForm
from .models import User


class CafeLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = CafeLoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.conf import settings
        ctx["ENABLE_DEMO_LOGIN"] = getattr(settings, "ENABLE_DEMO_LOGIN", True)
        return ctx

    def get_success_url(self):
        return reverse_lazy("core:dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        remember = form.cleaned_data.get("remember_me", False)
        if not remember:
            self.request.session.set_expiry(0)  # Expire on browser close
        return response


from django.contrib.auth import logout, update_session_auth_hash

class CafeLogoutView(View):
    """Handles both GET and POST logout requests cleanly."""
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "You have been signed out.")
        return redirect("accounts:login")

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "You have been signed out.")
        return redirect("accounts:login")


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "My Profile"
        ctx["password_form"] = ChangePasswordForm(user=self.request.user)
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)


class ChangePasswordView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = ChangePasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Password changed successfully.")
        else:
            messages.error(request, "Password change failed. Please check your current password.")
        return redirect("accounts:profile")


class ToggleDarkModeView(LoginRequiredMixin, View):
    """Toggle dark mode preference — called via JS."""
    def post(self, request, *args, **kwargs):
        user = request.user
        user.dark_mode = not user.dark_mode
        user.save(update_fields=["dark_mode"])
        return JsonResponse({"dark_mode": user.dark_mode})
