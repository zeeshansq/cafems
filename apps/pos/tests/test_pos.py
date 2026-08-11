import json
import pytest
from django.test import RequestFactory
from apps.tenants.models import Tenant
from apps.accounts.models import User, UserRole
from apps.menu.models import TeaItem, MenuCategory
from apps.pos.views import POSSubmitView, POSThermalReceiptView


@pytest.mark.django_db
def test_pos_submit_view_restricts_zero_amount_paid():
    tenant = Tenant.objects.create(title="Test Tenant", slug="test-tenant-pos")
    user = User.objects.create(
        email="posstaff@test.com", username="posstaff", role=UserRole.CAFE_STAFF, tenant=tenant, is_staff=True
    )
    category = MenuCategory.objects.create(tenant=tenant, name="Hot Drinks")
    item = TeaItem.objects.create(tenant=tenant, name="Special Tea", price=50, category=category, is_available=True)

    factory = RequestFactory()

    # 1. Zero amount paid should be restricted (HTTP 400)
    req_zero = factory.post("/pos/submit/", data=json.dumps({
        "items": [{"id": item.id, "qty": 1}],
        "amount_paid": 0,
    }), content_type="application/json")
    req_zero.user = user
    req_zero.tenant = tenant

    view = POSSubmitView()
    view.setup(req_zero)
    res_zero = view.post(req_zero)
    assert res_zero.status_code == 400
    res_data = json.loads(res_zero.content)
    assert "Checkout restricted" in res_data["error"]

    # 2. Valid amount paid >= total should succeed (HTTP 200)
    req_valid = factory.post("/pos/submit/", data=json.dumps({
        "items": [{"id": item.id, "qty": 1}],
        "amount_paid": 100,
    }), content_type="application/json")
    req_valid.user = user
    req_valid.tenant = tenant

    view_valid = POSSubmitView()
    view_valid.setup(req_valid)
    res_valid = view_valid.post(req_valid)
    assert res_valid.status_code == 200
    res_valid_data = json.loads(res_valid.content)
    assert res_valid_data["status"] == "ok"
    assert res_valid_data["change"] == 50.0
