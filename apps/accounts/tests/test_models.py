"""Accounts – Model Tests."""
import pytest
from django.core.exceptions import ValidationError
from apps.accounts.models import User, UserRole
from .factories import UserFactory, AdminUserFactory, TenantFactory


@pytest.mark.django_db
class TestUserModel:
    def test_user_creation(self):
        user = UserFactory()
        assert user.pk is not None
        assert user.role == UserRole.EMPLOYEE

    def test_email_is_unique(self):
        UserFactory(email="unique@test.com")
        with pytest.raises(Exception):
            UserFactory(email="unique@test.com")

    def test_full_name_returns_full_name(self):
        user = UserFactory(first_name="John", last_name="Doe")
        assert user.full_name == "John Doe"

    def test_full_name_falls_back_to_email_prefix(self):
        user = UserFactory(first_name="", last_name="")
        assert "@" not in user.full_name

    def test_role_predicates(self):
        admin = AdminUserFactory()
        assert admin.is_admin is True
        assert admin.is_cafe_staff is False
        assert admin.can_generate_bills() is True
        assert admin.can_view_reports() is True

    def test_employee_cannot_generate_bills(self):
        user = UserFactory(role=UserRole.EMPLOYEE)
        assert user.can_generate_bills() is False

    def test_committee_can_approve_bills(self):
        from .factories import CommitteeUserFactory
        user = CommitteeUserFactory()
        assert user.can_approve_bills() is True

    def test_tenant_isolation_property(self):
        tenant_a = TenantFactory()
        tenant_b = TenantFactory()
        user_a = UserFactory(tenant=tenant_a)
        user_b = UserFactory(tenant=tenant_b)
        assert user_a.tenant != user_b.tenant

    def test_str_representation(self):
        user = UserFactory(first_name="Jane", last_name="Smith")
        assert "Jane Smith" in str(user)
