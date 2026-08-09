import datetime
from decimal import Decimal
from django.test import TestCase
from apps.tenants.models import Tenant
from apps.menu.models import Cook, Sweet, RotiPrice, RotiType, DailyLunchEstimate
from apps.tokens.models import LunchToken, TokenStatus
from apps.employees.models import Employee


class DailyCostingTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(title="Test Tenant", short_title="TT", slug="test-tenant")
        self.cook = Cook.objects.create(tenant=self.tenant, name="Chef Aslam")
        self.sweet = Sweet.objects.create(tenant=self.tenant, name="Gulab Jamun", price=Decimal("30.00"))
        RotiPrice.objects.create(tenant=self.tenant, roti_type=RotiType.ROTI, price=Decimal("15.00"))
        RotiPrice.objects.create(tenant=self.tenant, roti_type=RotiType.NAAN, price=Decimal("20.00"))

        self.today = datetime.date.today()

    def test_recalculate_costing(self):
        estimate = DailyLunchEstimate.objects.create(
            tenant=self.tenant,
            date=self.today,
            dish_name="Chicken Karahi",
            cook=self.cook,
            roti_type=RotiType.ROTI,
            sweet=self.sweet,
            planned_count=50,
            total_expense=Decimal("10000.00"),
            adjustment_amount=Decimal("-500.00"),
        )

        # Before tokens issued: actual_tokens_issued = 0, token_expense = 9500, price_per_token = 0
        self.assertEqual(estimate.actual_tokens_issued, 0)
        self.assertEqual(estimate.price_per_token, Decimal("0.00"))

        # Create issued token
        employee = Employee.objects.create(
            tenant=self.tenant,
            full_name="Ali Khan",
            email="ali@test.com",
        )
        LunchToken.objects.create(
            tenant=self.tenant,
            employee=employee,
            date=self.today,
            token_number=1,
            token_qty=2,
            extra_roti_qty=1,
            extra_sweet_qty=1,
            status=TokenStatus.ISSUED,
        )

        # Trigger recalculate
        estimate.recalculate()
        estimate.save()

        self.assertEqual(estimate.actual_tokens_issued, 2)
        self.assertEqual(estimate.actual_extra_roti_issued, 1)
        self.assertEqual(estimate.actual_extra_sweet_issued, 1)

        # Extra Roti Cost = 1 * 15 = 15
        # Extra Sweet Cost = 1 * 30 = 30
        # Token Expense = 10000 - 15 - 30 + (-500) = 9455.00
        # Unit Cost = 9455 / 2 = 4727.50
        self.assertEqual(estimate.token_expense, Decimal("9455.00"))
        self.assertEqual(estimate.price_per_token, Decimal("4727.50"))

    def test_costing_dashboard_view(self):
        from apps.accounts.models import User, UserRole
        user = User.objects.create_user(
            username="staff_user",
            email="staff@test.com",
            password="password123",
            role=UserRole.CAFE_STAFF,
        )
        self.client.force_login(user)
        response = self.client.get("/menu/costing-dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("cooks_count", response.context)

