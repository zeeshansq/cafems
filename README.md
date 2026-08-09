<div align="center">

# 🍽️ CafeMS
### Enterprise-Grade Multi-Tenant Cafeteria Management System

[![Django](https://img.shields.io/badge/Django-5.2-092e20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![DRF](https://img.shields.io/badge/REST_API-DRF_3.15-a30000?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![HTMX](https://img.shields.io/badge/HTMX-1.21-blue?style=for-the-badge)](https://htmx.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

---

> **CafeMS** is a **production-ready, multi-tenant cafeteria management platform** built for corporate organizations.
> It automates daily lunch token issuance, POS counter sales, monthly billing, employee management, and financial reporting — all under a single smart dashboard with role-scoped access and dark mode support.

---

### ✅ Who Is This For?

| 🏢 Corporate Cafeterias | 🏫 Institute Canteens | 🏥 Hospital Food Courts | 🏗️ Factory Messes |
|:---:|:---:|:---:|:---:|
| Multi-department token systems | Student & staff meal plans | Shift-based meal tracking | Worker shift meals & billing |

---

### 🌟 Key Highlights at a Glance

```
🏢 Multi-Tenant    →  Each org is fully isolated — menus, employees, bills, reports
👥 5-Tier RBAC     →  Super Admin → Admin → Cafe Staff → Committee → Employee
🪙 Token Engine    →  Daily lunch token issuance with extra roti / sweet add-ons
🛒 POS Counter     →  Tea & snack sales with thermal receipt printing
📊 Billing Engine  →  Automated monthly bills with carry-forward & adjustments
📋 Smart Reports   →  8 admin + 4 employee personal reports with CSV export
🌗 Dark/Light Mode →  Per-user theme preference persisted in the database
🔐 Secure by Default → 403 guards on every view; styled custom error pages
```

</div>

---

## 📋 Table of Contents

- [Feature Highlights](#-feature-highlights)
- [Architecture Overview](#-architecture-overview)
- [Role-Based Access Control](#-role-based-access-control)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation Guide](#-installation-guide)
- [Environment Variables](#-environment-variables-reference)
- [Database Setup & Migrations](#-database-setup--migrations)
- [Seeder — Faker Demo Data](#-seeder--faker-demo-data)
- [Seeded Demo Credentials](#-seeded-demo-credentials)
- [Running the Application](#-running-the-application)
- [Running Background Workers](#-running-background-workers-celery)
- [Workflow Scenarios](#-workflow-scenarios--usage-examples)
- [Key URLs Reference](#-key-urls-reference)
- [Reports & Exports](#-reports--exports)
- [Multi-Tenancy Details](#-multi-tenancy-details)
- [Running Tests](#-running-tests)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)

---

## ✨ Feature Highlights

| Module | What It Does |
|--------|-------------|
| 🏢 **Multi-Tenancy** | Schema-isolated organizations; tenant resolved via session middleware |
| 👥 **RBAC (5 Roles)** | Server-side role enforcement via composable `DispatchMixin` classes |
| 🍱 **Lunch Menu Planning** | Weekly master plan + daily catering entry with smart cost dashboard |
| 🪙 **Token Issuance** | Lunch token issuance with extra roti/sweet add-ons, daily close-out report |
| 🛒 **POS Counter** | Real-time point-of-sale for tea & snacks with thermal receipt printing |
| ⏱️ **Token Requests** | Employee open/close token requests with 2 PM PKT cutoff enforcement |
| 📄 **Monthly Billing** | Automated bill generation — tokens + POS + misc charges + carry-forward dues |
| 💳 **Payment Tracking** | Multi-installment payments with running balance history |
| 📊 **Admin Reports** | 8 comprehensive admin reports with date/department filters and CSV export |
| 📋 **My Reports** | 4 personal reports for members — tokens, POS, invoices, requests |
| 🔔 **Notifications** | In-app notification feed with real-time unread badge |
| 🌗 **Dark / Light Mode** | Per-user theme persisted in DB; smooth CSS variable-based toggle |
| 🔐 **Auth Guards** | HTTP 403 on every sensitive view; custom styled 400/403/404/500 error pages |

---

## 🏗️ Architecture Overview

CafeMS uses a **shared-schema multi-tenancy** model in development (SQLite) with a clean migration path to **schema-per-tenant** in production (PostgreSQL via `django-tenants`).

### Request Lifecycle

```
┌─────────┐    HTTP Request    ┌──────────────────┐
│ Browser │ ────────────────► │ TenantMiddleware  │  resolves request.tenant
└─────────┘                   └────────┬─────────┘
                                        │
                              ┌─────────▼──────────┐
                              │  RoleRequiredMixin  │  RBAC guard (403 or proceed)
                              └─────────┬──────────┘
                                        │
                              ┌─────────▼──────────┐
                              │       View          │  tenant-scoped QuerySets
                              └─────────┬──────────┘
                                        │
                              ┌─────────▼──────────┐
                              │  Template + Context │  Bootstrap 5.3 + HTMX
                              └─────────┬──────────┘
                                        │
                              ┌─────────▼──────────┐
                              │ HTML Response (SPA) │
                              └────────────────────┘
```

### Module Dependency Map

```
┌────────────────────────────────────────────────────────────┐
│                      CafeMS Platform                        │
├────────────────┬───────────────────────────────────────────┤
│  Super Admin   │  Tenant CRUD • Platform Health Dashboard   │
│  (Global Scope)│  All Tenants • User Provisioning          │
├────────────────┴───────────────────────────────────────────┤
│                   Per-Tenant Scope                          │
│                                                             │
│  ┌────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Accounts  │  │  Employees  │  │        Menu          │ │
│  │  User+Role │  │  Employee   │  │  MenuCategory        │ │
│  │  5 Roles   │  │  Department │  │  TeaItem / POS Items │ │
│  │  Dark Mode │  │  MemberType │  │  LunchMenuPlan       │ │
│  └────────────┘  └─────────────┘  │  DailyLunchEstimate  │ │
│                                   └─────────────────────┘ │
│  ┌────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │    POS     │  │   Tokens    │  │   Requests App       │ │
│  │ TeaItemSale│  │ LunchToken  │  │ TokenOpenCloseRequest│ │
│  │ Thermal    │  │ DailyClose  │  │ 2 PM PKT cutoff      │ │
│  │ Receipt    │  │ Report      │  │ Approval Workflow     │ │
│  └────────────┘  └─────────────┘  └─────────────────────┘ │
│  ┌────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Billing   │  │  Notifs     │  │    Reports           │ │
│  │ BillRun    │  │ In-App Feed │  │  Admin: 8 Reports    │ │
│  │ MonthlyBill│  │ Badge Count │  │  Member: 4 Reports   │ │
│  │ Payment    │  │             │  │  CSV / PDF Export    │ │
│  │ MiscCharge │  └─────────────┘  └─────────────────────┘ │
│  └────────────┘                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 🔐 Role-Based Access Control

CafeMS enforces **strict server-side authorization** via composable `DispatchMixin` classes in `apps/core/mixins.py`:

| Role | Login As | Access Scope |
|------|----------|-------------|
| **Super Admin** | Platform-level | All tenants, platform health, user provisioning |
| **Admin** | Cafe Manager | All modules within their tenant |
| **Cafe Staff** | Counter Staff | Menu, token issuance, POS, daily reports |
| **Committee Member** | Oversight | View billing, approve bills, view reports |
| **Employee** | Member | Personal dashboard, my tokens, my bills, my reports |

> 🛡️ **Zero trust by default** — every view class explicitly declares its `DispatchMixin`. Any unauthorized user copying an admin URL receives a **styled HTTP 403 Forbidden** page with their role and a redirect button.

### Security Guards Applied

```python
# Admin-only view example
class BillingListView(StaffRequiredMixin, TemplateView): ...

# Employee-only view example
class MyBillDetailView(EmployeeRequiredMixin, DetailView): ...

# Admin redirected away from member pages
class EmployeeDashboardView(EmployeeRequiredMixin, TemplateView):
    # If admin visits /dashboard/me/ → redirected to /dashboard/admin/
```

---

## 🛠️ Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Framework** | Django | ≥ 5.2 |
| **REST API** | Django REST Framework | ≥ 3.15 |
| **Database (dev)** | SQLite | Built-in |
| **Database (prod)** | PostgreSQL + django-tenants | — |
| **Task Queue** | Celery + Redis | ≥ 5.4 |
| **Scheduled Tasks** | django-celery-beat | ≥ 2.7 |
| **Frontend** | Bootstrap 5.3 + Bootstrap Icons | — |
| **Interactivity** | HTMX + Alpine.js | 1.21 / 3.x |
| **PDF Export** | WeasyPrint | ≥ 62.0 |
| **Excel / CSV** | openpyxl | ≥ 3.1 |
| **Image Handling** | Pillow | ≥ 10.4 |
| **Environment** | django-environ | ≥ 0.11 |
| **Testing** | pytest-django + factory-boy | ≥ 4.9 |
| **Code Quality** | Black + isort + Ruff | Latest |
| **Fake Data** | Faker (Pakistani locale) | Built-in seeder |

---

## ✅ Prerequisites

Before you begin, ensure you have the following installed:

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.12+ | [Download](https://www.python.org/downloads/) |
| **pip** | Latest | Comes with Python |
| **Git** | Any | [Download](https://git-scm.com/) |
| **Redis** | 5.0+ | Required for Celery tasks |
| **WeasyPrint deps** | — | See [WeasyPrint Docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation) |
| **PostgreSQL** (prod) | 14+ | Only needed for production |

### Install Redis (Windows)

```bash
# Option 1: WSL2 (recommended)
wsl --install
sudo apt install redis-server
sudo service redis-server start

# Option 2: Memurai (Windows native Redis fork)
# https://www.memurai.com/
```

### Install WeasyPrint GTK Dependencies (Windows)

```bash
# Install MSYS2, then inside MSYS2:
pacman -S mingw-w64-x86_64-pango
# Add C:\msys64\mingw64\bin to PATH
```

---

## 🚀 Installation Guide

### Step 1 — Clone the Repository

```bash
git clone https://github.com/zeeshansq/cafems.git
cd cafems
```

### Step 2 — Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4 — Configure Environment Variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and fill in your values (see [Environment Variables Reference](#-environment-variables-reference) below).

### Step 5 — Run Migrations

```bash
python manage.py migrate
```

### Step 6 — Seed Demo Data

```bash
python manage.py seed_data
```

### Step 7 — Launch the Server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000** 🎉

---

## ⚙️ Environment Variables Reference

Copy `.env.example` to `.env`. All variables and their descriptions:

```ini
# ── Django Core ───────────────────────────────────────────────
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*

# ── Database ──────────────────────────────────────────────────
# Development (SQLite — default, no extra setup needed)
DATABASE_URL=sqlite:///db.sqlite3

# Production (PostgreSQL)
# DATABASE_URL=postgresql://cafems_user:cafems_pass@localhost:5432/cafems_db

# ── Redis & Celery ────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# ── Email ─────────────────────────────────────────────────────
# Console backend (dev — prints emails to terminal)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# SMTP (production)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=CafeMS <noreply@cafems.com>

# ── Timezone ──────────────────────────────────────────────────
TIME_ZONE=Asia/Karachi

# ── File Uploads ──────────────────────────────────────────────
MAX_UPLOAD_SIZE=5242880   # 5 MB

# ── Site Info ─────────────────────────────────────────────────
SITE_NAME=CafeMS
SITE_DOMAIN=localhost
```

> ⚠️ **Never commit your `.env` file.** It is listed in `.gitignore`. Use `.env.example` as the committed template.

---

## 🗃️ Database Setup & Migrations

```bash
# Apply all migrations (creates all tables)
python manage.py migrate

# Check for unapplied migrations
python manage.py showmigrations

# Create new migrations after model changes
python manage.py makemigrations

# Reset development database (WARNING: deletes all data)
del db.sqlite3          # Windows
python manage.py migrate
python manage.py seed_data
```

---

## 🌱 Seeder — Faker Demo Data

CafeMS ships with a powerful built-in seeder that uses the **Faker** library to generate realistic **Pakistani cafeteria data** across all modules.

### Run the Seeder

```bash
python manage.py seed_data
```

### What the Seeder Creates

The seeder runs **14 sequential steps** with live console output:

```
=========================================================================
                 CAFEMS - PAKISTANI DATA SEEDER RUNNER
=========================================================================

[STEP  1/14] Applying latest database migrations...
[STEP  2/14] Seeding Multi-Tenant Entities...          → 2 tenants
[STEP  3/14] Provisioning Global Super Administrator... → admin@cafems.com
[STEP  4/14] Provisioning Cafe Admin Manager User...   → cafe_admin@democafe.com
[STEP  5/14] Creating Organization Departments...      → 8 departments
[STEP  6/14] Provisioning Committee & Cafe Staff...    → committee + staff users
[STEP  7/14] Generating Employee Profiles & Users...   → 24 realistic employees
[STEP  8/14] Seeding POS Menu Categories & Items...   → Beverages, Snacks & Bakery
[STEP  9/14] Building Weekly Master Lunch Menu Plan... → Mon–Fri × 4 weeks
[STEP 10/14] Creating Daily Catering Estimates...      → Previous month, Mon–Fri
[STEP 11/14] Issuing Daily Lunch Tokens...             → All employees, all days
[STEP 12/14] Recording POS Tea & Snack Sales...        → Random sales per day
[STEP 13/14] Generating Monthly Bills & Payments...    → Auto-calculated totals
[STEP 14/14] Exporting Credentials Summary Report...   → SEEDER_SUMMARY_AND_CREDENTIALS.txt
```

### Seeded Data Volume

| Entity | Count |
|--------|-------|
| Tenants | 2 (Demo Cafe, NTI-Cafe) |
| Departments | 8 (Engineering, HR, Finance, Operations, IT, QA, SCM, Executive) |
| Employees | 24 realistic Pakistani-named employees |
| POS Menu Items | ~10 items (Beverages + Snacks) |
| Lunch Menu Plans | 20 plans (5 days × 4 weeks) |
| Daily Catering Estimates | ~22 (entire previous month, Mon–Fri) |
| Lunch Tokens Issued | ~22 × 24 = ~528 tokens |
| POS Sales | Random daily sales for all employees |
| Monthly Bills | 24 (one per employee) |

### Pakistani Lunch Menu Data Included

```
Dishes Generated:
  • Chicken Biryani    • Mutton Karahi      • Chicken Handi & Naan
  • Daal Fry & Roti    • Chicken Pulao      • Beef Haleem
  • Palak Paneer       • Aloo Gobi & Naan   • Mixed Vegetable Sabzi
  • Chicken White Korma

POS Items:
  Beverages:  Doodh Patti Chai · Green Tea · Cold Drink · Mineral Water
  Snacks:     Potato Samosa · Chicken Samosa · Chicken Patties
              Egg Sandwich · Vegetable Pakoras · Chocolate Chip Cookie
```

### After Seeding

All credentials are saved to `SEEDER_SUMMARY_AND_CREDENTIALS.txt` (git-ignored):

```bash
# View credentials file
type SEEDER_SUMMARY_AND_CREDENTIALS.txt    # Windows
cat SEEDER_SUMMARY_AND_CREDENTIALS.txt     # macOS/Linux
```

> 💡 **Tip**: Re-run `seed_data` at any time. It uses `get_or_create` so it will not create duplicates — it will update existing records and add any missing ones.

---

## 🔑 Seeded Demo Credentials

After running `python manage.py seed_data`, use these accounts to explore the system:

| Role | Email | Password | Access |
|------|-------|----------|--------|
| **Super Admin** | `admin@cafems.com` | `admin123!@#` | Full platform, all tenants |
| **Cafe Admin** | `cafe_admin@democafe.com` | `admin123!@#` | Full tenant management |
| **Committee Member** | `committee@democafe.com` | `admin123!@#` | Billing & reports oversight |
| **Cafe Staff** | `staff@democafe.com` | `admin123!@#` | Menu, tokens, POS counter |
| **Employee** | _(see credentials file)_ | `emp123!@#` | Personal dashboard & reports |

> 📄 Employee-specific email addresses are printed in `SEEDER_SUMMARY_AND_CREDENTIALS.txt` after the seeder runs.

---

## ▶️ Running the Application

```bash
# Start the Django development server
python manage.py runserver

# Run on a specific port
python manage.py runserver 8080

# Accessible from LAN (e.g., for mobile testing)
python manage.py runserver 0.0.0.0:8000
```

Visit: **http://127.0.0.1:8000**

---

## ⚙️ Running Background Workers (Celery)

CafeMS uses **Celery** for background tasks (email notifications, bill generation, scheduled reports). You need Redis running first.

```bash
# Terminal 1 — Start Redis
redis-server

# Terminal 2 — Start Celery Worker
celery -A cafems worker --loglevel=info

# Terminal 3 — Start Celery Beat (scheduler)
celery -A cafems beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Terminal 4 — Django server
python manage.py runserver
```

---

## 🎬 Workflow Scenarios & Usage Examples

### Scenario 1 — Admin Sets Up a New Month

```
1. LOGIN as Cafe Admin → http://127.0.0.1:8000/
   ✦ Dashboard shows monthly KPIs, today's menu, recent activity

2. PLAN WEEKLY MENU → /menu/plan/
   ✦ Set dish, cook, sweet, roti type for each day of each week

3. CONFIGURE DAILY ESTIMATE → /menu/daily/ (each working day at start)
   ✦ Enter today's dish, expected headcount, per-head price

4. ISSUE LUNCH TOKENS → /tokens/issue/
   ✦ Select employees, confirm quantities, issue tokens
   ✦ Print token receipt (thermal format)

5. OPERATE POS COUNTER → /pos/
   ✦ Add tea/snack items to cart, process sale
   ✦ Print thermal receipt for employee

6. DAILY CLOSE-OUT → /tokens/daily-closing/
   ✦ Review token totals, close the day
   ✦ Print daily summary report

7. GENERATE MONTHLY BILLS → /billing/generate/
   ✦ System calculates token cost + POS spend + misc charges
   ✦ Review, adjust, then PUBLISH bills to employees
```

---

### Scenario 2 — Employee Views Their Account

```
1. LOGIN as Employee → http://127.0.0.1:8000/
   ✦ Personal dashboard shows: tokens this month, POS spend,
     pending requests, today's lunch menu

2. VIEW MY BILL → /billing/my/
   ✦ List of all monthly invoices with status (Paid/Unpaid)
   ✦ Click any bill to see detailed breakdown:
     - Line items (tokens, extra roti, extra sweet)
     - Day-by-day attendance log
     - Payment history

3. SUBMIT TOKEN REQUEST → /requests/submit/
   ✦ Request to OPEN (start token) or CLOSE (stop token) service
   ✦ Admin reviews and approves/declines

4. VIEW MY REPORTS → /reports/my/
   ✦ My Token Summary — monthly attendance & token log
   ✦ My POS Purchases — tea & snack history
   ✦ My Invoices — financial statement
   ✦ My Requests — open/close request history
```

---

### Scenario 3 — Admin Reviews Financials & Exports Reports

```
1. ADMIN REPORTS HUB → /reports/
   ✦ Monthly Token Summary — all employees, filter by dept/month
   ✦ Employee Issuance Report — filter by Token / POS / All
   ✦ POS Collection Report — daily/monthly revenue
   ✦ Billing Report — outstanding bills, payment status

2. EXPORT CSV → Click "Export CSV" on any report
   ✦ Downloads filtered data as .csv

3. BILLING MANAGEMENT → /billing/
   ✦ Review all bills for the month
   ✦ Record payment against an employee's bill
   ✦ Add misc charges (maintenance, utilities)
```

---

### Scenario 4 — Multi-Tenant Super Admin

```
1. LOGIN as Super Admin → /tenants/
   ✦ Platform dashboard: all tenants, active/inactive status

2. CREATE TENANT → /tenants/create/
   ✦ Name, slug, contact email, currency

3. SWITCH TENANT CONTEXT → /tenants/<id>/activate/
   ✦ All subsequent requests scoped to that tenant

4. MANAGE USERS GLOBALLY
   ✦ Create/edit users across any tenant
   ✦ Assign tenant-level admin role
```

---

## 🗂️ Key URLs Reference

| URL | Description | Required Role |
|-----|-------------|:---:|
| `/` | Role-based dashboard redirect | All |
| `/accounts/login/` | Email login | Public |
| `/dashboard/admin/` | Executive KPI Dashboard | Staff+ |
| `/dashboard/me/` | Personal Employee Dashboard | Employee |
| `/employees/` | Employee Roster & CRUD | Admin+ |
| `/menu/plan/` | Weekly Lunch Menu Plan | Staff+ |
| `/menu/daily/` | Daily Catering Entry | Staff+ |
| `/menu/costing/` | Food Cost Dashboard | Admin+ |
| `/tokens/issue/` | Daily Token Issuance | Staff+ |
| `/tokens/daily-closing/` | Daily Close-Out Report | Staff+ |
| `/tokens/history/` | All Token History | Staff+ / Own for Employee |
| `/pos/` | POS Counter (Tea & Snacks) | Staff+ |
| `/requests/` | Token Requests List | Staff+ |
| `/requests/my/` | My Token Requests | Employee |
| `/billing/` | Monthly Billing Management | Admin+ |
| `/billing/my/` | My Monthly Bills | Employee |
| `/billing/generate/` | Generate Monthly Bills | Admin+ |
| `/reports/` | Admin Reports Hub | Staff+ |
| `/reports/tokens/monthly/` | Monthly Token Summary | Admin+ |
| `/reports/employees/issuance/` | Employee Issuance Report | Admin+ |
| `/reports/pos/collection/` | POS Collection Report | Admin+ |
| `/reports/billing/` | Billing Status Report | Admin+ |
| `/reports/my/` | My Personal Reports Hub | Employee |
| `/reports/my/tokens/` | My Token Summary Report | Employee |
| `/reports/my/pos/` | My POS Purchase History | Employee |
| `/reports/my/billing/` | My Invoice Statement | Employee |
| `/reports/my/requests/` | My Requests History | Employee |
| `/notifications/` | Notification Feed | All |
| `/tenants/` | Tenant Management | Super Admin |
| `/admin/` | Django Admin Panel | Super Admin |

---

## 📊 Reports & Exports

### Admin Reports (8 Total)

| Report | Filters | CSV Export |
|--------|---------|:---:|
| Monthly Token Summary | Date range, Department | ✅ |
| Employee Issuance | Date range, Dept, Type (Token/POS/All) | ✅ |
| Employee Deposits | Date range, Department | ✅ |
| POS Collection Report | Date range, Item | ✅ |
| Billing Status Report | Month, Status, Department | ✅ |
| Requests Issuance Report | Date range, Type | ✅ |
| Requests Closure Report | Date range, Status | ✅ |
| Bill Run Summary | Month, Bill Run | ✅ |

### Employee Personal Reports (4 Total)

| Report | What It Shows | Filters |
|--------|--------------|---------|
| My Token Summary | Daily attendance, token qty, add-ons | Date range |
| My POS Purchases | Tea & snack purchase history | Date range, item search |
| My Invoices | Monthly bill statements + payment history | Date range |
| My Requests | Open/close request workflow log | Date range |

---

## 🏢 Multi-Tenancy Details

### How It Works

Every model in CafeMS extends `TenantModel`:

```python
class TenantModel(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

The `TenantMiddleware` sets `request.tenant` on every request. All views scope their QuerySets by `tenant=request.tenant`.

### Development vs Production

| | Development | Production |
|-|-------------|------------|
| **Database** | SQLite | PostgreSQL |
| **Isolation** | `tenant_id` FK filter | Schema-per-tenant (`django-tenants`) |
| **Setup** | Zero config | Uncomment `django-tenants` in `requirements.txt` |

### Creating a New Tenant

```bash
# Via Django Admin → Tenants → Add Tenant

# Or via management command (custom)
python manage.py shell
>>> from apps.tenants.models import Tenant
>>> Tenant.objects.create(title="My Org Cafe", slug="myorg", currency="PKR")
```

---

## 🧪 Running Tests

```bash
# Run full test suite
pytest

# With coverage report in terminal
pytest --cov=apps --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=apps --cov-report=html
# Open htmlcov/index.html in your browser

# Run tests for a specific app only
pytest apps/billing/ -v
pytest apps/tokens/ -v

# Run a specific test function
pytest apps/billing/tests.py::test_bill_total_calculation -v

# Run with print/stdout output visible
pytest -s -v
```

---

## 📁 Project Structure

```
cafems/
├── .env.example                    # ← Copy to .env before running
├── .gitignore
├── manage.py
├── requirements.txt
├── setup.cfg                       # pytest + isort + black configuration
│
├── cafems/                         # Root Django project config
│   ├── settings/
│   │   ├── base.py                 # Shared settings (apps, middleware, auth)
│   │   ├── development.py          # DEBUG=True, SQLite, console email
│   │   └── production.py           # PostgreSQL, WhiteNoise, HTTPS
│   ├── urls.py                     # Root URL conf + custom error handlers
│   ├── celery.py                   # Celery application definition
│   └── api_urls.py                 # DRF REST API routes
│
├── apps/                           # Django application modules
│   ├── accounts/                   # Custom User model, email login, UserRole
│   ├── tenants/                    # Tenant model, middleware, context processor
│   ├── employees/                  # Employee, Department, MembershipType, AuditLog
│   ├── menu/                       # MenuCategory, TeaItem, LunchMenuPlan, DailyEstimate
│   ├── tokens/                     # LunchToken issuance, daily closing report
│   ├── pos/                        # POS counter, TeaItemSale, thermal receipt
│   ├── requests_app/               # TokenOpenCloseRequest, 2 PM cutoff workflow
│   ├── billing/                    # BillRun, MonthlyBill, Payment, MiscCharge
│   ├── notifications/              # In-app notification model and feeds
│   ├── reports/                    # Admin & member report views + CSV export
│   └── core/                       # RBAC mixins, TenantModel, dashboard routing
│       ├── mixins.py               # StaffRequiredMixin, EmployeeRequiredMixin, etc.
│       ├── models.py               # TenantModel base
│       ├── views.py                # Dashboard views + custom error handlers
│       └── management/
│           └── commands/
│               └── seed_data.py   # Faker-based Pakistani data seeder
│
├── templates/                      # Global Django templates
│   ├── base.html                   # Main layout (navbar, sidebar, dark mode toggle)
│   ├── base_minimal.html           # Print/receipt layout
│   ├── 400.html                    # Bad Request error page
│   ├── 403.html                    # Forbidden (shows user role + redirect)
│   ├── 404.html                    # Not Found error page
│   ├── 500.html                    # Server Error page
│   └── components/
│       ├── navbar.html             # Role-scoped navigation
│       ├── sidebar.html            # Sidebar with active link detection
│       └── footer.html
│
├── static/                         # Static assets (committed, served in dev)
│   ├── css/
│   │   ├── bootstrap.min.css       # Bootstrap 5.3
│   │   ├── bootstrap-icons.min.css # Bootstrap Icons
│   │   └── main.css                # CafeMS theme variables & utilities
│   ├── js/
│   │   ├── bootstrap.bundle.min.js
│   │   ├── alpine.min.js           # Alpine.js 3.x
│   │   ├── htmx.min.js             # HTMX 1.21
│   │   └── app.js                  # Theme toggle, navbar, global utils
│   └── fonts/
│       └── inter/                  # Inter typeface (woff2)
│
└── docs/                           # Developer documentation
    ├── architecture.md             # System architecture & request lifecycle
    ├── billing-formula.md          # Bill calculation formula & examples
    ├── setup.md                    # Detailed setup instructions
    ├── decisions.md                # Architectural decision records
    └── troubleshooting.md          # Common issues & solutions
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/cafems.git
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** and write tests
5. **Run the test suite**:
   ```bash
   pytest --cov=apps
   ```
6. **Format your code**:
   ```bash
   black .
   isort .
   ruff check .
   ```
7. **Commit** with a descriptive message:
   ```bash
   git commit -m "feat: add weekly menu export to PDF"
   ```
8. **Push** and open a **Pull Request**:
   ```bash
   git push origin feature/your-feature-name
   ```

---

## 📝 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

## 👤 Author

<div align="center">

**Zeeshan Shabbir Qureshi**

[![GitHub](https://img.shields.io/badge/GitHub-zeeshansq-181717?style=for-the-badge&logo=github)](https://github.com/zeeshansq)
[![Email](https://img.shields.io/badge/Email-Contact-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:zeeshan.shabbirqureshi@gmail.com)

</div>

---

<div align="center">

### Built with ❤️ using Django 5.2

*If CafeMS saved you time, please consider giving it a ⭐ — it helps others discover the project!*

[![Star on GitHub](https://img.shields.io/github/stars/zeeshansq/cafems?style=social)](https://github.com/zeeshansq/cafems/stargazers)

</div>
