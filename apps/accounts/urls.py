from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.CafeLoginView.as_view(), name="login"),
    path("logout/", views.CafeLogoutView.as_view(), name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/change-password/", views.ChangePasswordView.as_view(), name="change_password"),
    path("profile/dark-mode/", views.ToggleDarkModeView.as_view(), name="toggle_dark_mode"),
]
