"""Accounts – View Tests."""
import pytest
from django.urls import reverse
from .factories import UserFactory, AdminUserFactory


@pytest.mark.django_db
class TestLoginView:
    def test_login_page_renders(self, client):
        url = reverse("accounts:login")
        response = client.get(url)
        assert response.status_code == 200
        assert "form" in response.context

    def test_login_with_valid_credentials(self, client):
        user = UserFactory()
        url = reverse("accounts:login")
        response = client.post(url, {"username": user.email, "password": "testpass123"})
        assert response.status_code == 302  # redirect on success

    def test_login_with_invalid_credentials(self, client):
        url = reverse("accounts:login")
        response = client.post(url, {"username": "bad@email.com", "password": "wrong"})
        assert response.status_code == 200
        assert response.context["form"].errors

    def test_authenticated_user_redirected_from_login(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse("accounts:login")
        response = client.get(url)
        assert response.status_code == 302

    def test_logout_redirects(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse("accounts:logout")
        response = client.post(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestProfileView:
    def test_profile_requires_login(self, client):
        url = reverse("accounts:profile")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_profile_view_authenticated(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse("accounts:profile")
        response = client.get(url)
        assert response.status_code == 200
