import datetime
import pytest
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from apps.tenants.models import Tenant
from apps.accounts.models import User, UserRole
from apps.employees.models import Employee, MembershipType
from apps.menu.models import DailyLunchEstimate
from apps.tokens.views import TokenIssueView
from apps.tokens.forms import TokenIssueForm


@pytest.mark.django_db
def test_token_issue_view_filters_luncher_members_only():
    tenant = Tenant.objects.create(title="Test Tenant", slug="test-tenant-token")
    user = User.objects.create(
        email="staff@test.com", username="staffuser", role=UserRole.CAFE_STAFF, tenant=tenant, is_staff=True
    )

    # 1. Lunch member (Active, Full Open)
    emp_luncher = Employee.objects.create(
        tenant=tenant,
        full_name="Luncher Member",
        pno="L001",
        register_number="REG-001",
        membership_status=True,
        membership_type=MembershipType.FULL_OPEN,
        is_active=True,
    )
    # 2. Non-member employee (Not Member)
    emp_non_member = Employee.objects.create(
        tenant=tenant,
        full_name="Non Member Employee",
        pno="NM001",
        register_number="REG-002",
        membership_status=False,
        membership_type=MembershipType.NOT_MEMBER,
        is_active=True,
    )

    factory = RequestFactory()
    req = factory.get("/tokens/issue/")
    req.user = user
    req.tenant = tenant

    view = TokenIssueView()
    view.setup(req)
    ctx = view.get_context_data()

    eligible_ids = [e.pk for e in ctx["employees"]]
    assert emp_luncher.pk in eligible_ids
    assert emp_non_member.pk not in eligible_ids

    form = TokenIssueForm(tenant=tenant)
    form_emp_ids = list(form.fields["employee"].queryset.values_list("id", flat=True))
    assert emp_luncher.pk in form_emp_ids
    assert emp_non_member.pk not in form_emp_ids


@pytest.mark.django_db
def test_token_issue_temp_close_no_name_error():
    tenant = Tenant.objects.create(title="Test Tenant", slug="test-tenant-temp-close")
    user = User.objects.create(
        email="admin@test.com", username="adminuser", role=UserRole.ADMIN, tenant=tenant, is_staff=True
    )
    emp_temp_close = Employee.objects.create(
        tenant=tenant,
        full_name="Temp Close Member",
        pno="TC001",
        register_number="REG-003",
        membership_status=True,
        membership_type=MembershipType.TEMP_CLOSE,
        is_active=True,
    )

    today = datetime.date.today()
    DailyLunchEstimate.objects.create(tenant=tenant, date=today, dish_name="Biryani")

    factory = RequestFactory()
    req = factory.post("/tokens/issue/", data={
        "employee": emp_temp_close.pk,
        "token_qty": 1,
    })
    req.user = user
    req.tenant = tenant

    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(req)
    req.session.save()

    msg_middleware = MessageMiddleware(lambda r: None)
    msg_middleware.process_request(req)

    view = TokenIssueView()
    view.setup(req)
    res = view.post(req)
    assert res.status_code in [200, 302, 400]
