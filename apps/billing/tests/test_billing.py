import datetime
from decimal import Decimal
import pytest
from apps.tenants.models import Tenant
from apps.employees.models import Employee, MembershipType
from apps.billing.services import BillingService
from apps.billing.models import MonthlyBill, BillStatus


@pytest.mark.django_db
def test_billing_service_generation():
    tenant = Tenant.objects.create(title="Test Tenant", slug="test-tenant")
    emp = Employee.objects.create(
        tenant=tenant,
        full_name="John Doe",
        pno="12345",
        membership_status=True,
        membership_type=MembershipType.FULL_OPEN,
    )

    today = datetime.date.today()
    service = BillingService(tenant=tenant, month=today)
    count = service.generate_all()

    assert count == 1
    bill = MonthlyBill.objects.get(tenant=tenant, employee=emp)
    assert bill.status == BillStatus.UNPAID
    assert bill.total >= Decimal("0.00")
