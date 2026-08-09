import datetime
from decimal import Decimal
from django.test import TestCase
from apps.tenants.models import Tenant
from apps.accounts.models import User, UserRole
from apps.menu.models import Cook, Sweet, RotiPrice, LunchMenuPlan, RotiType


class SetupManagementTestCase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(title="Test Tenant", short_title="TT", slug="test-tenant")
        self.user = User.objects.create_user(
            username="staff_user_setup",
            email="staff_setup@test.com",
            password="password123",
            role=UserRole.CAFE_STAFF,
        )
        self.client.force_login(self.user)

    def test_setup_index_renders(self):
        response = self.client.get("/menu/setup/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("cooks", response.context)
        self.assertIn("sweets", response.context)
        self.assertIn("roti_prices", response.context)

    def test_cook_creation_and_toggle(self):
        response = self.client.post("/menu/setup/cooks/new/", {
            "name": "Chef Tariq",
            "phone": "0300-1122334",
            "is_active": True,
        })
        self.assertEqual(response.status_code, 302)
        cook = Cook.objects.get(name="Chef Tariq")
        self.assertTrue(cook.is_active)

        # Toggle cook
        toggle_resp = self.client.post(f"/menu/setup/cooks/{cook.pk}/toggle/")
        self.assertEqual(toggle_resp.status_code, 302)
        cook.refresh_from_db()
        self.assertFalse(cook.is_active)

    def test_sweet_creation_and_editing(self):
        response = self.client.post("/menu/setup/sweets/new/", {
            "name": "Jalebi",
            "price": "25.00",
            "is_active": True,
        })
        self.assertEqual(response.status_code, 302)
        sweet = Sweet.objects.get(name="Jalebi")
        self.assertEqual(sweet.price, Decimal("25.00"))

        # Update sweet price
        update_resp = self.client.post(f"/menu/setup/sweets/{sweet.pk}/edit/", {
            "name": "Jalebi Special",
            "price": "35.00",
            "is_active": True,
        })
        self.assertEqual(update_resp.status_code, 302)
        sweet.refresh_from_db()
        self.assertEqual(sweet.name, "Jalebi Special")
        self.assertEqual(sweet.price, Decimal("35.00"))

    def test_roti_creation_update_and_delete(self):
        # Create new custom Roti type
        response = self.client.post("/menu/setup/roti/new/", {
            "name": "Khamiri Naan",
            "price": "28.00",
            "is_active": True,
        })
        self.assertEqual(response.status_code, 302)
        rp = RotiPrice.objects.get(name="Khamiri Naan")
        self.assertEqual(rp.price, Decimal("28.00"))

        # Edit price
        edit_resp = self.client.post(f"/menu/setup/roti/{rp.pk}/edit/", {
            "name": "Khamiri Naan Special",
            "price": "32.00",
            "is_active": True,
        })
        self.assertEqual(edit_resp.status_code, 302)
        rp.refresh_from_db()
        self.assertEqual(rp.name, "Khamiri Naan Special")
        self.assertEqual(rp.price, Decimal("32.00"))

        # Delete custom Roti
        del_resp = self.client.post(f"/menu/setup/roti/{rp.pk}/delete/")
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(RotiPrice.objects.filter(pk=rp.pk).exists())

    def test_lunch_plan_update_and_delete(self):
        plan = LunchMenuPlan.objects.create(
            tenant=self.tenant,
            month=datetime.date(2026, 8, 1),
            week_of_month=1,
            day_of_week=0,
            dish_name="Chicken Biryani",
            roti_type=RotiType.ROTI,
            is_published=True,
        )
        # Edit plan
        edit_resp = self.client.post(f"/menu/lunch-plan/{plan.pk}/edit/", {
            "month": "2026-08-01",
            "week_of_month": 1,
            "day_of_week": 0,
            "dish_name": "Chicken Biryani Special",
            "roti_type": RotiType.NAAN,
            "contains_sweet": True,
            "is_published": True,
        })
        self.assertEqual(edit_resp.status_code, 302)
        plan.refresh_from_db()
        self.assertEqual(plan.dish_name, "Chicken Biryani Special")

        # Delete plan
        del_resp = self.client.post(f"/menu/lunch-plan/{plan.pk}/delete/")
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(LunchMenuPlan.objects.filter(pk=plan.pk).exists())
