<div align="center">

# 🍽️ CafeMS
### Multi-Tenant Cafeteria Management System

[![Django](https://img.shields.io/badge/Django-5.2-0C4B33?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![DRF](https://img.shields.io/badge/REST_API-DRF_3.15-a30000?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<p>
  A <strong>production-grade, multi-tenant cafeteria management platform</strong> built for organizations to manage daily lunch menus, token issuance, POS sales, monthly billing, and employee reports — all from a single, role-scoped dashboard.
</p>

---

</div>

## ✨ Feature Highlights

| Module | Description |
|--------|-------------|
| 🏢 **Multi-Tenancy** | Schema-isolated organizations with middleware-based tenant resolution |
| 👥 **Role-Based Access** | 5-tier RBAC: Super Admin → Admin → Cafe Staff → Committee Member → Employee |
| 🍱 **Lunch Menu Planning** | Weekly master menu plan + daily catering entry & smart cost dashboard |
| 🪙 **Token Issuance** | Daily lunch token issuance with extra roti/sweet add-ons and daily close-out |
| 🛒 **POS Counter** | Real-time point-of-sale for tea & snacks with thermal receipt printing |
| 📄 **Monthly Billing** | Automated bill generation with token cost, POS charges, adjustments, carry-forward |
| 📊 **Admin Reports** | 8 comprehensive admin reports with CSV/PDF export |
| 📋 **My Reports** | 4 personal reports for members — tokens, POS, invoices, requests |
| 🔔 **Notifications** | In-app notification feed with real-time badge updates |
| 🌗 **Dark / Light Mode** | Per-user theme preference persisted in the database |
| 🔐 **Secure by Default** | HTTP 403 guards on every view; custom 400/403/404/500 error pages |

---

## 🏗️ Architecture Overview

CafeMS uses a **shared-schema multi-tenancy** model in development (SQLite) and is fully ready for **schema-per-tenant** in production (PostgreSQL via `django-tenants`).

```
Browser Request
     │
     ▼
TenantMiddleware  ──── resolves tenant from session ──────►  request.tenant
     │
     ▼
RoleRequiredMixin ──── RBAC guard per view ───────────────►  403 or proceed
     │
     ▼
View ──────────── tenant-scoped QuerySet ─────────────────►  Template
```

### Application Map

```
cafems/
├── apps/
│   ├── accounts/       # Custom User model (email login, role, dark mode)
│   ├── tenants/        # Multi-tenant setup & middleware
│   ├── employees/      # Employee roster, departments, membership types
│   ├── menu/           # MenuCategory, TeaItem, LunchMenuPlan, DailyLunchEstimate
│   ├── tokens/         # LunchToken issuance, daily closing report
│   ├── pos/            # POS counter, TeaItemSale, thermal receipt
│   ├── requests_app/   # Token open/close request workflow (2 PM PKT cutoff)
│   ├── billing/        # MonthlyBillRun, MonthlyBill, Payment, MiscCharge
│   ├── notifications/  # In-app notification feed
│   ├── reports/        # Admin & member reports hub (CSV export)
│   └── core/           # Dashboard routing, RBAC mixins, base models
├── templates/          # Global base layout, navbar, error pages
├── static/             # Bootstrap 5.3, Bootstrap Icons, Inter font, HTMX
└── cafems/             # Root URL config, settings (dev/prod/base), Celery
```

---

## 🔐 Role-Based Access Control

CafeMS enforces strict server-side authorization via `DispatchMixin` classes:

| Role | Access Scope |
|------|-------------|
| **Super Admin** | Full platform, all tenants |
| **Admin** | All modules within their tenant |
| **Cafe Staff** | Menu, tokens, POS, daily reports |
| **Committee Member** | View billing, approve reports |
| **Employee** | Personal dashboard, token history, my reports, my bills |

> Any attempt by an unauthorized role to access a restricted URL results in a **styled HTTP 403 Forbidden** page — even if the user copies the URL from an admin session.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 5.2, Django REST Framework 3.15 |
| **Task Queue** | Celery 5.4 + Redis, django-celery-beat |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Frontend** | Bootstrap 5.3, Bootstrap Icons, HTMX, Alpine.js |
| **PDF/Excel** | WeasyPrint (PDF), openpyxl (Excel/CSV) |
| **Auth** | Custom AbstractUser (email-based login) |
| **Testing** | pytest-django, factory-boy, pytest-cov |
| **Code Quality** | Black, isort, Ruff |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Redis (for Celery)
- Git

### 1. Clone & Set Up Environment

```bash
git clone https://github.com/zeeshansq/cafems.git
cd cafems

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy the example .env file
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Edit `.env` with your configuration:

```ini
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite by default for development)
DATABASE_URL=sqlite:///db.sqlite3

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 3. Run Migrations & Seed Data

```bash
# Apply database migrations
python manage.py migrate

# Seed realistic demo data (employees, menus, tokens, bills)
python manage.py seed_data

# Optional: Create a Super Admin account
python manage.py createsuperuser
```

> After seeding, credentials for all demo accounts are saved to `SEEDER_SUMMARY_AND_CREDENTIALS.txt` (**this file is git-ignored**).

### 4. Launch the Development Server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000** in your browser.

---

## 🗂️ Key URLs

| URL | Description | Role |
|-----|-------------|------|
| `/` | Role-based dashboard redirect | All |
| `/dashboard/admin/` | Executive KPI Dashboard | Admin+ |
| `/dashboard/me/` | Personal Employee Dashboard | Employee |
| `/tokens/issue/` | Daily Lunch Token Issuance | Staff+ |
| `/pos/` | POS Counter (Tea & Snacks) | Staff+ |
| `/menu/plan/` | Weekly Lunch Menu Plan | Staff+ |
| `/billing/` | Monthly Billing Management | Admin+ |
| `/billing/my/` | My Invoices (Employee) | Employee |
| `/reports/` | Admin Reports Hub | Admin+ |
| `/reports/my/` | Personal Reports Hub | Employee |
| `/employees/` | Employee Roster Management | Admin+ |
| `/requests/` | Token Open/Close Requests | All |

---

## 📊 Reports & Exports

### Admin Reports
- **Monthly Token Summary** — All employees, token qty, attendance, add-ons
- **Employee Issuance Report** — Filterable by date, department, issuance type (Token/POS/All)
- **Employee Deposits Report** — Security deposit tracking
- **POS Collection Report** — Daily/monthly POS revenue
- **Billing Report** — Bill status, outstanding, per-employee breakdown
- **Requests Issuance/Closure** — Token request workflow audit trail

### Employee Personal Reports
- **My Token Summary** — Personal attendance & token log with daily totals
- **My POS Purchases** — Tea & snack purchase history
- **My Invoices** — Monthly bill statements with payment history
- **My Requests** — Token open/close request history

> All reports support **date range filtering**, **department filtering**, **search**, and **CSV export**.

---

## 🏢 Multi-Tenancy

CafeMS supports multiple organizations on a single deployment:

- Each tenant has isolated **employees, menus, tokens, billing, and reports**
- `TenantMiddleware` resolves `request.tenant` automatically
- All models extend `TenantModel` with a `tenant` FK and scoped queries
- Super Admin can create, suspend, and manage tenants from `/tenants/`

### Development (SQLite)
Shared schema with `tenant_id` filtering on every QuerySet.

### Production (PostgreSQL)
Pluggable `django-tenants` for true schema-per-tenant isolation.

---

## 🧪 Running Tests

```bash
# Run full test suite
pytest

# With coverage report
pytest --cov=apps --cov-report=html

# Run specific test file
pytest apps/billing/tests.py -v
```

---

## 📁 Project Structure

```
cafems/
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── manage.py
├── requirements.txt
├── setup.cfg                   # pytest, isort, black configuration
│
├── cafems/                     # Root Django project
│   ├── settings/
│   │   ├── base.py             # Shared settings
│   │   ├── development.py      # Dev overrides (DEBUG=True, SQLite)
│   │   └── production.py       # Prod overrides (PostgreSQL, WhiteNoise)
│   ├── urls.py                 # Root URL conf + custom error handlers
│   ├── celery.py               # Celery application
│   └── api_urls.py             # DRF API routes
│
├── apps/                       # Django applications
│   ├── accounts/               # Custom User, UserRole, login views
│   ├── tenants/                # Tenant model, middleware, context processor
│   ├── employees/              # Employee, Department, AuditLog
│   ├── menu/                   # MenuCategory, TeaItem, LunchMenuPlan, DailyLunchEstimate
│   ├── tokens/                 # LunchToken, daily close-out
│   ├── pos/                    # TeaItemSale, POS counter, receipt
│   ├── requests_app/           # TokenOpenCloseRequest workflow
│   ├── billing/                # MonthlyBillRun, MonthlyBill, Payment, MiscCharge
│   ├── notifications/          # Notification model, feeds
│   ├── reports/                # Admin & member report views
│   └── core/                   # Mixins, TenantModel, dashboard routing
│
├── templates/                  # Global templates
│   ├── base.html               # Main layout with dark/light theme toggle
│   ├── base_minimal.html       # Minimal layout for print/receipt pages
│   ├── 400.html                # Bad Request error page
│   ├── 403.html                # Forbidden error page (with user context)
│   ├── 404.html                # Not Found error page
│   ├── 500.html                # Server Error page
│   └── components/             # Navbar, sidebar, footer partials
│
├── static/                     # Static assets
│   ├── css/bootstrap.min.css
│   ├── css/main.css            # CafeMS theme variables & utilities
│   ├── js/bootstrap.bundle.min.js
│   ├── js/alpine.min.js
│   └── js/app.js               # Theme toggle, navbar, global utilities
│
└── docs/                       # Architecture & developer docs
    ├── architecture.md
    ├── billing-formula.md
    ├── setup.md
    └── decisions.md
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## 👤 Author

**Zeeshan Shabbir Qureshi**
- GitHub: [@zeeshansq](https://github.com/zeeshansq)
- Email: zeeshan.shabbirqureshi@gmail.com

---

<div align="center">

Made with ❤️ and Django

⭐ **Star this project** if it helped you!

</div>
