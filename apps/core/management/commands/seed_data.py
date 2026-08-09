"""
Django Management Command: seed_data
Populates database with realistic, high-quality Pakistani cafeteria data.
Generates complete daily estimates, token issuances, POS sales, and monthly bills for the PREVIOUS MONTH (Mon-Fri only).
Exports comprehensive generation summary and user credentials to SEEDER_SUMMARY_AND_CREDENTIALS.txt at workspace root.
"""

import os
import random
from datetime import timedelta, date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from faker import Faker

fake = Faker()

from apps.tenants.models import Tenant, TenantStatus
from apps.accounts.models import User, UserRole
from apps.employees.models import Employee, Department, MembershipType, EmployeeCategory, AuditLog
from apps.menu.models import MenuCategory, TeaItem, LunchMenuPlan, DailyLunchEstimate, Cook, Sweet, RotiPrice, RotiType
from apps.tokens.models import LunchToken, TokenStatus
from apps.pos.models import TeaItemSale, PaymentMethod
from apps.requests_app.models import TokenOpenCloseRequest, RequestType, RequestStatus
from apps.billing.models import MonthlyBill, BillStatus, Payment, MonthlyBillRun, MonthlyBillRunStatus

# Pakistani Realistic Data Sets
PK_MALE_NAMES = [
    ("Muhammad", "Ali"), ("Usman", "Tariq"), ("Hamza", "Raza"), ("Bilal", "Ahmed"),
    ("Imran", "Khan"), ("Zahid", "Hassan"), ("Saad", "Qureshi"), ("Omer", "Farooq"),
    ("Fahad", "Siddiqui"), ("Shahid", "Malik"), ("Adnan", "Chaudhry"), ("Hassan", "Shah"),
    ("Kashif", "Bhatti"), ("Rizwan", "Sheikh"), ("Kamran", "Mughal"), ("Ahsan", "Niazi"),
    ("Nabeel", "Mirza"), ("Yasir", "Baig"), ("Waqas", "Ghaffar"), ("Farhan", "Mahmood"),
    ("Asad", "Zubair"), ("Danish", "Iqbal"), ("Zubair", "Abbas"), ("Haris", "Mustafa")
]

PK_FEMALE_NAMES = [
    ("Fatima", "Khan"), ("Ayesha", "Siddiqui"), ("Zainab", "Malik"), ("Sana", "Mahmood"),
    ("Mariam", "Shah"), ("Hira", "Raza"), ("Noreen", "Ahmed"), ("Sobia", "Chaudhry"),
    ("Bushra", "Bhatti"), ("Rabia", "Sheikh"), ("Sadia", "Qureshi"), ("Mahnoor", "Farooq"),
    ("Anum", "Zubair"), ("Iqra", "Hassan"), ("Mehwish", "Tariq"), ("Sidra", "Ali")
]

DEPARTMENTS_DATA = [
    ("Engineering & Software", "ENG"),
    ("Human Resources", "HR"),
    ("Finance & Accounts", "FIN"),
    ("Operations & Administration", "OPS"),
    ("IT Infrastructure & Security", "IT"),
    ("Quality Assurance & Audit", "QA"),
    ("Supply Chain & Logistics", "SCM"),
    ("Executive Secretariat", "EXEC")
]

DESIGNATIONS = [
    ("Senior Manager", EmployeeCategory.OFFICER),
    ("Software Engineer", EmployeeCategory.OFFICER),
    ("Assistant Manager", EmployeeCategory.OFFICER),
    ("Senior Accountant", EmployeeCategory.OFFICER),
    ("HR Executive", EmployeeCategory.OFFICER),
    ("System Administrator", EmployeeCategory.OFFICER),
    ("Operations Assistant", EmployeeCategory.STAFF),
    ("Admin Support Specialist", EmployeeCategory.STAFF),
    ("Data Entry Operator", EmployeeCategory.STAFF),
    ("Logistics Associate", EmployeeCategory.STAFF)
]

DISHES_DATA = [
    ("Chicken Biryani", "Fragrant Basmati rice cooked with spiced tender chicken", True, "na"),
    ("Mutton Karahi", "Traditional wok-cooked mutton curry in rich tomato gravy", False, "roghni"),
    ("Chicken Handi & Naan", "Creamy boneless chicken gravy served with fresh tandoori naan", False, "naan"),
    ("Daal Fry & Roti", "Tempered lentils cooked with ghee and aromatic spices served with Roti", False, "roti"),
    ("Chicken Pulao", "Classic Yakhni Pulao prepared with long-grain Basmati rice", True, "na"),
    ("Beef Haleem", "Slow-cooked lentil and meat stew topped with fried onions and lemon", True, "naan"),
    ("Mixed Vegetable Sabzi", "Seasonal fresh vegetables stir-fried with traditional spices", False, "roti"),
    ("Palak Paneer & Roti", "Fresh spinach puree with cottage cheese cubes served with Roti", False, "roti"),
    ("Chicken White Korma", "Mild, creamy white gravy cooked with almonds and chicken", True, "roghni"),
    ("Aloo Gobi & Naan", "Cauliflower and potato curry cooked with cumin and coriander", False, "naan")
]

POS_ITEMS_DATA = [
    ("Beverages", [
        ("Doodh Patti Chai", 40.00, "Special cardamom milk tea"),
        ("Green Tea / Kashmiri Chai", 35.00, "Herbal Kashmiri tea"),
        ("Cold Drink (345ml)", 70.00, "Chilled carbonated soft drink"),
        ("Fresh Mineral Water (500ml)", 40.00, "Purified mineral water")
    ]),
    ("Snacks & Bakery", [
        ("Potato Samosa (2 pcs)", 50.00, "Crispy fried potato samosas"),
        ("Chicken Samosa (2 pcs)", 80.00, "Minced chicken filled samosas"),
        ("Chicken Patties", 90.00, "Flaky puff pastry filled with chicken"),
        ("Egg Sandwich", 120.00, "Classic mayo-egg club sandwich"),
        ("Mix Vegetable Pakoras (Plate)", 70.00, "Crispy fried vegetable fritters"),
        ("Chocolate Chip Cookie", 45.00, "Freshly baked butter cookie")
    ])
]


class Command(BaseCommand):
    help = "Seed database with realistic Pakistani cafeteria data and generate credentials summary report."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("========================================================================="))
        self.stdout.write(self.style.WARNING("                 CAFEMS - PAKISTANI DATA SEEDER RUNNER                  "))
        self.stdout.write(self.style.WARNING("========================================================================="))

        self.stdout.write(self.style.WARNING("\n[STEP 1/14] Applying latest database migrations..."))
        call_command("migrate", interactive=False)
        self.stdout.write(self.style.SUCCESS("  -> Schema migrated successfully."))

        credentials = []

        # ── 1. Tenants ───────────────────────────────────────────────────────
        self.stdout.write(self.style.WARNING("\n[STEP 2/14] Seeding Multi-Tenant Entities..."))
        demo_tenant, _ = Tenant.objects.get_or_create(
            slug="democafe",
            defaults={
                "title": "Demo Cafe Enterprise",
                "short_title": "DemoCafe",
                "contact_email": "contact@democafe.com",
                "currency": "PKR",
                "status": TenantStatus.ACTIVE,
            }
        )

        ent_tenant, _ = Tenant.objects.get_or_create(
            slug="entcafe",
            defaults={
                "title": "National Technical Institute Cafe",
                "short_title": "NTI-Cafe",
                "contact_email": "admin@nticafe.com",
                "currency": "PKR",
                "status": TenantStatus.ACTIVE,
            }
        )
        self.stdout.write(self.style.SUCCESS(f"  -> Tenants active: '{demo_tenant.title}' and '{ent_tenant.title}'."))

        # ── 2. Super Admin User ──────────────────────────────────────────────
        self.stdout.write(self.style.WARNING("\n[STEP 3/14] Provisioning Global Super Administrator..."))
        super_admin, _ = User.objects.get_or_create(
            email="admin@cafems.com",
            defaults={
                "first_name": "Super",
                "last_name": "Admin",
                "role": UserRole.SUPER_ADMIN,
                "is_staff": True,
                "is_superuser": True,
            }
        )
        super_admin.first_name = "Super"
        super_admin.last_name = "Admin"
        super_admin.role = UserRole.SUPER_ADMIN
        super_admin.is_staff = True
        super_admin.is_superuser = True
        super_admin.set_password("admin123!@#")
        super_admin.save()

        credentials.append({
            "email": super_admin.email,
            "password": "admin123!@#",
            "role": "Super Administrator",
            "pno": "SYSTEM-ADMIN",
            "name": "Super Admin",
            "tenant": "Global Platform"
        })
        self.stdout.write(self.style.SUCCESS(f"  -> Super Admin configured: {super_admin.email}."))

        # ── 3. Tenant Admin User ─────────────────────────────────────────────
        self.stdout.write(self.style.WARNING("\n[STEP 4/14] Provisioning Cafe Admin Manager User..."))
        cafe_admin, _ = User.objects.get_or_create(
            email="cafe_admin@democafe.com",
            defaults={
                "first_name": "Muhammad",
                "last_name": "Tariq",
                "role": UserRole.ADMIN,
                "tenant": demo_tenant,
                "is_staff": True,
            }
        )
        cafe_admin.tenant = demo_tenant
        cafe_admin.role = UserRole.ADMIN
        cafe_admin.set_password("admin123!@#")
        cafe_admin.save()

        credentials.append({
            "email": cafe_admin.email,
            "password": "admin123!@#",
            "role": "Cafe Admin / Manager",
            "pno": "P-ADMIN-01",
            "name": "Muhammad Tariq",
            "tenant": demo_tenant.title
        })
        self.stdout.write(self.style.SUCCESS(f"  -> Cafe Admin configured: {cafe_admin.email}."))

        # ── 4. Departments ───────────────────────────────────────────────────
        self.stdout.write(self.style.WARNING("\n[STEP 5/14] Creating Organization Departments..."))
        departments = []
        for name, code in DEPARTMENTS_DATA:
            dept, _ = Department.objects.get_or_create(
                tenant=demo_tenant,
                name=name,
                defaults={"code": code}
            )
            departments.append(dept)
        self.stdout.write(self.style.SUCCESS(f"  -> {len(departments)} Departments created."))

        # ── 5. Committee & Staff Users ───────────────────────────────────────
        self.stdout.write(self.style.WARNING("\n[STEP 6/14] Provisioning Committee & Cafe Counter Staff Users..."))
        committee_user, _ = User.objects.get_or_create(
            email="committee@democafe.com",
            defaults={
                "first_name": "Usman",
                "last_name": "Ghani",
                "role": UserRole.COMMITTEE_MEMBER,
                "tenant": demo_tenant,
            }
        )
        committee_user.tenant = demo_tenant
        committee_user.role = UserRole.COMMITTEE_MEMBER
        committee_user.set_password("admin123!@#")
        committee_user.save()

        credentials.append({
            "email": committee_user.email,
            "password": "admin123!@#",
            "role": "Cafeteria Committee Member",
            "pno": "P-COMM-01",
            "name": "Usman Ghani",
            "tenant": demo_tenant.title
        })

        staff_user, _ = User.objects.get_or_create(
            email="staff@democafe.com",
            defaults={
                "first_name": "Bilal",
                "last_name": "Raza",
                "role": UserRole.CAFE_STAFF,
                "tenant": demo_tenant,
            }
        )
        staff_user.tenant = demo_tenant
        staff_user.role = UserRole.CAFE_STAFF
        staff_user.set_password("admin123!@#")
        staff_user.save()

        credentials.append({
            "email": staff_user.email,
            "password": "admin123!@#",
            "role": "Cafe Counter Staff",
            "pno": "P-STAFF-01",
            "name": "Bilal Raza",
            "tenant": demo_tenant.title
        })
        self.stdout.write(self.style.SUCCESS("  -> Committee and Staff user accounts active."))

        # ── 6. Employees Roster & User Accounts ──────────────────────────────
        self.stdout.write(self.style.WARNING("\n[STEP 7/14] Generating Pakistani Employee Members Roster..."))
        all_pk_names = PK_MALE_NAMES + PK_FEMALE_NAMES

        employees = []
        pno_counter = 1001

        # Unlink old user mappings to allow clean deterministic re-linking
        Employee.objects.filter(tenant=demo_tenant).update(user=None)

        for first_n, last_n in all_pk_names:
            pno_str = f"P-{pno_counter}"
            email_str = f"{first_n.lower()}.{last_n.lower()}@democafe.com"

            user_obj, _ = User.objects.get_or_create(
                email=email_str,
                defaults={
                    "first_name": first_n,
                    "last_name": last_n,
                    "username": email_str,
                    "role": UserRole.EMPLOYEE,
                    "tenant": demo_tenant,
                }
            )
            user_obj.first_name = first_n
            user_obj.last_name = last_n
            user_obj.tenant = demo_tenant
            user_obj.role = UserRole.EMPLOYEE
            user_obj.set_password("user123!@#")
            user_obj.save()

            if pno_counter % 8 == 0:
                mem_status = False
                mem_type = MembershipType.NOT_MEMBER
            elif pno_counter % 6 == 0:
                mem_status = True
                mem_type = MembershipType.TEMP_CLOSE
            elif pno_counter % 4 == 0:
                mem_status = True
                mem_type = MembershipType.ROTI_OPEN
            else:
                mem_status = True
                mem_type = MembershipType.FULL_OPEN

            desig, cat = DESIGNATIONS[pno_counter % len(DESIGNATIONS)]
            dept = departments[pno_counter % len(departments)]

            # Lookup by P-No first to preserve unique tenant_id + pno constraint
            emp_obj = Employee.objects.filter(tenant=demo_tenant, pno=pno_str).first()

            if emp_obj:
                emp_obj.user = user_obj
                emp_obj.pno = pno_str
                emp_obj.full_name = f"{first_n} {last_n}"
                emp_obj.email = email_str
                emp_obj.membership_status = mem_status
                emp_obj.membership_type = mem_type
                emp_obj.designation = desig
                emp_obj.category = cat
                emp_obj.department = dept
                emp_obj.save()
            else:
                emp_obj = Employee.objects.create(
                    tenant=demo_tenant,
                    user=user_obj,
                    pno=pno_str,
                    register_number=f"REG-{pno_counter}",
                    full_name=f"{first_n} {last_n}",
                    email=email_str,
                    mobile=f"+92-300-{1000000 + pno_counter}",
                    telephone_extension=str(100 + (pno_counter % 900)),
                    gender="M" if (first_n, last_n) in PK_MALE_NAMES else "F",
                    designation=desig,
                    category=cat,
                    department=dept,
                    date_joined=timezone.now().date() - timedelta(days=365),
                    membership_status=mem_status,
                    membership_type=mem_type,
                    security_deposit_paid=Decimal("1000.00") if mem_status else Decimal("0.00"),
                    security_deposit_pending=Decimal("0.00"),
                    is_active=True,
                )

            employees.append(emp_obj)

            credentials.append({
                "email": user_obj.email,
                "password": "user123!@#",
                "role": f"Employee ({emp_obj.get_membership_type_display()})",
                "pno": emp_obj.pno,
                "name": emp_obj.full_name,
                "tenant": demo_tenant.title
            })

            pno_counter += 1

        self.stdout.write(self.style.SUCCESS(f"  -> {len(employees)} Employee member accounts & profiles seeded."))

        # ── 7. Setup Auxiliary Data (Cooks, Sweets, RotiPrices) ────────────────
        self.stdout.write(self.style.WARNING("\n[STEP 8/14] Seeding Cafeteria Auxiliary Data (Cooks, Sweets, Roti)..."))
        cook_umer, _ = Cook.objects.get_or_create(tenant=demo_tenant, name="Chef Umer", defaults={"phone": "0300-1112233"})
        cook_rasheed, _ = Cook.objects.get_or_create(tenant=demo_tenant, name="Master Rasheed", defaults={"phone": "0301-4445566"})
        cook_farooq, _ = Cook.objects.get_or_create(tenant=demo_tenant, name="Chef Farooq", defaults={"phone": "0302-7778899"})

        sweet_gulab, _ = Sweet.objects.get_or_create(tenant=demo_tenant, name="Gulab Jamun", defaults={"price": Decimal("30.00")})
        sweet_kheer, _ = Sweet.objects.get_or_create(tenant=demo_tenant, name="Kheer", defaults={"price": Decimal("40.00")})

        roti_std, _ = RotiPrice.objects.get_or_create(tenant=demo_tenant, roti_type="roti", defaults={"name": "Standard Roti", "price": Decimal("15.00"), "is_active": True})
        roti_naan, _ = RotiPrice.objects.get_or_create(tenant=demo_tenant, roti_type="naan", defaults={"name": "Tandoori Naan", "price": Decimal("20.00"), "is_active": True})
        self.stdout.write(self.style.SUCCESS("  -> Cooks, Sweets, and Roti prices configured."))

        # ── 8. Generic Master 5-Week Lunch Menu Plans (Mon-Fri only) ─────────────
        self.stdout.write(self.style.WARNING("\n[STEP 9/14] Seeding Master Weekly 5-Month Lunch Menu Plans (Mon-Fri)..."))
        # Delete any existing weekend master plans (Saturday=5, Sunday=6)
        LunchMenuPlan.objects.filter(tenant=demo_tenant, day_of_week__in=[5, 6]).delete()

        plan_count = 0
        for week_idx in range(1, 6):
            for day_idx in range(5):  # Mon-Fri (0-4) only
                dish_name, desc, has_sweet, r_type = DISHES_DATA[(week_idx * 5 + day_idx) % len(DISHES_DATA)]
                LunchMenuPlan.objects.get_or_create(
                    tenant=demo_tenant,
                    week_of_month=week_idx,
                    day_of_week=day_idx,
                    defaults={
                        "dish_name": dish_name,
                        "description": desc,
                        "cook": random.choice([cook_umer, cook_rasheed, cook_farooq]),
                        "roti_price_obj": roti_naan if r_type == "naan" else roti_std,
                        "sweet": sweet_gulab if has_sweet else None,
                        "contains_sweet": has_sweet,
                        "planned_by": cafe_admin,
                        "is_published": True,
                    }
                )
                plan_count += 1
        self.stdout.write(self.style.SUCCESS(f"  -> {plan_count} Master Lunch Menu Plans active (Mon-Fri)."))

        # ── 9. Tea & Snack POS Items & Counter Sales ─────────────────────────
        self.stdout.write(self.style.WARNING("\n[STEP 10/14] Seeding POS Item Catalog & Counter Sales History..."))
        pos_items = []
        for cat_name, items in POS_ITEMS_DATA:
            cat_obj, _ = MenuCategory.objects.get_or_create(tenant=demo_tenant, name=cat_name)
            for item_name, price, desc in items:
                t_item, _ = TeaItem.objects.get_or_create(
                    tenant=demo_tenant,
                    name=item_name,
                    defaults={"category": cat_obj, "price": Decimal(str(price)), "description": desc, "is_available": True}
                )
                pos_items.append(t_item)

        today_dt = timezone.localdate()
        for i in range(15):
            sale_item = random.choice(pos_items)
            sale_buyer = random.choice(employees)
            qty = random.randint(1, 4)
            tot = Decimal(str(sale_item.price * qty))
            TeaItemSale.objects.create(
                tenant=demo_tenant,
                item=sale_item,
                quantity=qty,
                unit_price=sale_item.price,
                amount_paid=tot,
                date=today_dt,
                buyer=sale_buyer,
                issued_by=cafe_admin,
                is_walk_in=False,
                order_reference=f"POS-{random.randint(1000,9999)}"
            )
        self.stdout.write(self.style.SUCCESS("  -> POS Item Catalog & initial counter sales seeded."))

        # ── 10. Dates Setup for PREVIOUS MONTH (Mon-Fri Only) ──────────────────
        today = timezone.localdate()
        if today.month == 1:
            prev_month_start = date(today.year - 1, 12, 1)
            prev_month_end = date(today.year - 1, 12, 31)
        else:
            prev_month_start = date(today.year, today.month - 1, 1)
            prev_month_end = date(today.year, today.month, 1) - timedelta(days=1)

        self.stdout.write(self.style.WARNING(f"\n[STEP 11/14] Generating Previous Month Mon-Fri Catering Estimates & Tokens ({prev_month_start.strftime('%d-%b-%Y')} to {prev_month_end.strftime('%d-%b-%Y')})..."))

        # Clear previous records for clean re-seeding
        MonthlyBill.objects.filter(tenant=demo_tenant).delete()
        LunchToken.objects.filter(tenant=demo_tenant).delete()
        DailyLunchEstimate.objects.filter(tenant=demo_tenant).delete()
        TeaItemSale.objects.filter(tenant=demo_tenant, date__range=[prev_month_start, prev_month_end]).delete()

        # Generate Daily Estimates for Monday to Friday ONLY
        current_date = prev_month_start
        daily_estimates = {}

        while current_date <= prev_month_end:
            if current_date.weekday() < 5:
                w_idx = (current_date.day - 1) // 7 + 1
                d_idx = current_date.weekday()
                dish_tuple = DISHES_DATA[(w_idx * 7 + d_idx) % len(DISHES_DATA)]

                est, _ = DailyLunchEstimate.objects.get_or_create(
                    tenant=demo_tenant,
                    date=current_date,
                    defaults={
                        "dish_name": dish_tuple[0],
                        "cook": random.choice([cook_umer, cook_rasheed, cook_farooq]),
                        "roti_price_obj": roti_naan if dish_tuple[3] == "naan" else roti_std,
                        "sweet": sweet_gulab if dish_tuple[2] else None,
                        "planned_count": random.randint(45, 65),
                        "estimated_extra_roti": random.randint(8, 15),
                        "estimated_extra_sweet": random.randint(4, 10),
                        "total_expense": Decimal(str(random.randint(6500, 9500))),
                        "adjustment_amount": Decimal("0.00"),
                        "created_by": cafe_admin,
                        "is_locked": True,
                    }
                )
                daily_estimates[current_date] = est
            current_date += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS(f"  -> {len(daily_estimates)} Daily Lunch Estimates generated."))

        # ── 11. Lunch Tokens (Linked 100% to Daily Estimates) ──────────────────
        self.stdout.write(self.style.WARNING("\n[STEP 12/14] Issuing Lunch Tokens & Reconciling Attendance..."))
        tokens_created = 0
        for emp in employees:
            if not emp.membership_status or emp.membership_type == MembershipType.TEMP_CLOSE:
                continue

            for d_date, est in daily_estimates.items():
                if random.random() < 0.85:
                    is_roti = (emp.membership_type == MembershipType.ROTI_OPEN)
                    has_ex_roti = 1 if random.random() < 0.22 else 0
                    has_ex_sweet = 1 if random.random() < 0.18 else 0

                    LunchToken.objects.get_or_create(
                        tenant=demo_tenant,
                        employee=emp,
                        date=d_date,
                        token_number=1,
                        defaults={
                            "token_qty": 1,
                            "extra_roti_qty": has_ex_roti,
                            "extra_sweet_qty": has_ex_sweet,
                            "status": TokenStatus.ISSUED,
                            "issued_by": cafe_admin,
                            "price_snapshot": Decimal("150.00"),
                            "roti_override": is_roti,
                            "is_retroactive": False,
                            "daily_estimate": est,
                        }
                    )
                    tokens_created += 1

        for d_date, est in daily_estimates.items():
            LunchToken.objects.filter(tenant=demo_tenant, date=d_date).update(daily_estimate=est)
            est.recalculate()
            est.save()

        self.stdout.write(self.style.SUCCESS(f"  -> {tokens_created} Lunch Tokens issued & reconciled."))

        # ── 12. Monthly Bills & Payments ─────────────────────────────────────
        self.stdout.write(self.style.WARNING("\n[STEP 13/14] Generating Monthly Bills & Invoice Payments..."))
        bill_run, _ = MonthlyBillRun.objects.get_or_create(
            tenant=demo_tenant,
            period_start=prev_month_start,
            defaults={
                "period_end": prev_month_end,
                "status": MonthlyBillRunStatus.PUBLISHED,
                "published_at": timezone.now(),
                "generated_by": cafe_admin,
            }
        )

        bills_created = 0
        for emp in employees:
            if not emp.membership_status:
                continue

            emp_tokens = LunchToken.objects.filter(
                tenant=demo_tenant,
                employee=emp,
                date__range=[prev_month_start, prev_month_end],
                status=TokenStatus.ISSUED
            )
            token_count = emp_tokens.count()
            if token_count == 0:
                continue

            token_amt = sum(t.price_snapshot for t in emp_tokens)
            total_ex_roti = sum(t.extra_roti_qty for t in emp_tokens)
            total_ex_sweet = sum(t.extra_sweet_qty for t in emp_tokens)

            extra_roti_amt = Decimal(str(total_ex_roti * 15.00))
            extra_sweet_amt = Decimal(str(total_ex_sweet * 35.00))
            misc_charge_amt = Decimal("30.00")
            subtot = token_amt + extra_roti_amt + extra_sweet_amt + misc_charge_amt

            line_items = [
                {"description": f"Lunch Tokens ({token_count} Days)", "quantity": token_count, "unit_price": f"{(token_amt / Decimal(token_count)):,.2f}", "total": f"{token_amt:,.2f}"},
            ]
            if total_ex_roti > 0:
                line_items.append({"description": "Extra Roti Issued", "quantity": total_ex_roti, "unit_price": "15.00", "total": f"{extra_roti_amt:,.2f}"})
            if total_ex_sweet > 0:
                line_items.append({"description": "Extra Sweet Issued", "quantity": total_ex_sweet, "unit_price": "35.00", "total": f"{extra_sweet_amt:,.2f}"})
            
            line_items.append({"description": "Cafeteria Maintenance & Misc", "quantity": 1, "unit_price": "30.00", "total": "30.00"})

            status_choice = random.choice([BillStatus.UNPAID, BillStatus.UNPAID, BillStatus.PAID, BillStatus.PAID, BillStatus.PARTIALLY_PAID])

            bill, created = MonthlyBill.objects.get_or_create(
                tenant=demo_tenant,
                employee=emp,
                period_start=prev_month_start,
                defaults={
                    "period_end": prev_month_end,
                    "line_items": line_items,
                    "total_token_qty": token_count,
                    "total_extra_roti_qty": total_ex_roti,
                    "total_extra_sweet_qty": total_ex_sweet,
                    "token_total": token_amt,
                    "extra_roti_total": extra_roti_amt,
                    "extra_sweet_total": extra_sweet_amt,
                    "misc_charges_total": misc_charge_amt,
                    "security_deposit_pending": Decimal("0.00"),
                    "previous_balance": Decimal("0.00"),
                    "adjustment_total": Decimal("0.00"),
                    "subtotal": subtot,
                    "total": subtot,
                    "status": status_choice,
                    "generated_by": cafe_admin,
                }
            )
            bills_created += 1
            if created and bill.status == BillStatus.PAID:
                Payment.objects.create(
                    tenant=demo_tenant,
                    bill=bill,
                    amount_paid=bill.total,
                    payment_date=prev_month_end,
                    method="cash",
                    received_by=cafe_admin,
                    remaining_balance=Decimal("0.00"),
                    reference=f"PAY-REF-{emp.pno}"
                )

        self.stdout.write(self.style.SUCCESS(f"  -> {bills_created} Monthly Invoices generated & published."))

        # ── 13. Export Summary & Complete Credentials Roster ──────────────────
        self.stdout.write(self.style.WARNING("\n[STEP 14/14] Exporting SEEDER_SUMMARY_AND_CREDENTIALS.txt Report..."))
        from django.conf import settings
        summary_filepath = str(settings.BASE_DIR / "SEEDER_SUMMARY_AND_CREDENTIALS.txt")

        summary_lines = []
        summary_lines.append("====================================================================================================================")
        summary_lines.append("                                      CAFEMS - PAKISTANI DATA SEEDER SUMMARY                                       ")
        summary_lines.append("====================================================================================================================")
        summary_lines.append(f" Generated Date : {timezone.now().strftime('%d-%b-%Y %H:%M:%S PKT')}")
        summary_lines.append(f" Primary Tenant : {demo_tenant.title} (Slug: {demo_tenant.slug})")
        summary_lines.append(f" Billed Period  : {prev_month_start.strftime('%B %Y')} ({prev_month_start.strftime('%d-%b-%Y')} to {prev_month_end.strftime('%d-%b-%Y')})")
        summary_lines.append("--------------------------------------------------------------------------------------------------------------------")
        summary_lines.append(f"  - Tenants Created               : {Tenant.objects.count()}")
        summary_lines.append(f"  - Total User Accounts           : {User.objects.count()}")
        summary_lines.append(f"  - Employee Profiles Roster       : {Employee.objects.count()}")
        summary_lines.append(f"  - Menu Categories               : {MenuCategory.objects.count()}")
        summary_lines.append(f"  - POS Items                     : {TeaItem.objects.count()}")
        summary_lines.append(f"  - Master Menu Plans             : {LunchMenuPlan.objects.count()}")
        summary_lines.append(f"  - Daily Lunch Estimates         : {DailyLunchEstimate.objects.count()}")
        summary_lines.append(f"  - Issued Lunch Tokens           : {LunchToken.objects.count()}")
        summary_lines.append(f"  - POS Sales Transactions        : {TeaItemSale.objects.count()}")
        summary_lines.append(f"  - Monthly Bills                 : {MonthlyBill.objects.count()}")
        summary_lines.append(f"  - Payments Collected            : {Payment.objects.count()}")
        summary_lines.append("====================================================================================================================")
        summary_lines.append("")
        summary_lines.append("====================================================================================================================")
        summary_lines.append("                                            USER ACCOUNTS & LOGIN CREDENTIALS ROSTER                                ")
        summary_lines.append("====================================================================================================================")
        summary_lines.append(f"{'#':<4} {'Full Name':<24} {'P-No':<14} {'Role / Designation':<32} {'Login Email':<32} {'Password':<14}")
        summary_lines.append("--------------------------------------------------------------------------------------------------------------------")

        for idx, cred in enumerate(credentials, 1):
            summary_lines.append(
                f"{idx:<4} {cred['name']:<24} {cred['pno']:<14} {cred['role']:<32} {cred['email']:<32} {cred['password']:<14}"
            )

        summary_lines.append("--------------------------------------------------------------------------------------------------------------------")
        summary_lines.append("Note: All accounts above can be used to log in at http://127.0.0.1:8000/accounts/login/")
        summary_lines.append("====================================================================================================================")

        with open(summary_filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(summary_lines))

        self.stdout.write(self.style.SUCCESS(f"\n========================================================================="))
        self.stdout.write(self.style.SUCCESS(f" SUCCESS: Seeder completed! {len(credentials)} User credentials saved to:"))
        self.stdout.write(self.style.SUCCESS(f" -> {summary_filepath}"))
        self.stdout.write(self.style.SUCCESS(f"=========================================================================\n"))
