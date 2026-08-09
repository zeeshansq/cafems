# CafeMS — Multi-Tenant Cafe Management System

A premium Django-based Cafe Management System designed for government/corporate cafeterias with multi-tenant support.

---

## ✨ Features

| Module | Description |
|---|---|
| **Multi-Tenancy** | Each organization (tenant) is fully isolated — separate data via FK-based separation (dev) or schema-per-tenant (prod) |
| **Role-Based Access** | 5 roles: Super Admin, Admin, Cafe Staff, Committee Member, Employee — enforced server-side via mixins |
| **Tea/Snack POS** | Touch-friendly Alpine.js cart, walk-in support, multiple payment methods |
| **Lunch Tokens** | Daily issuance with Roti-Open lock/override, estimate counter, 2PM PKT cutoff enforcement |
| **Open/Close Requests** | Employee self-service with 2PM PKT cutoff validation, staff acknowledge/reject |
| **Monthly Billing** | Token billing with pro-rata adjustment, misc charges, carryforward balance, 4-stage approval workflow |
| **Menu Management** | Weekly lunch plan, tea/snack catalog, daily estimate setter |
| **Notifications** | In-app bell with unread count, notification history |
| **Reports** | Monthly token summary, billing reports |
| **Dark Mode** | Per-user preference, persisted server-side |
| **Audit Logging** | Immutable log for backdated edits and Roti-Open overrides |
| **Celery Tasks** | Daily estimate reminders, price snapshots, bill reminders |

---

## 🚀 Quick Start

```powershell
# 1. Activate virtual environment
C:\venv\envcafe\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
Copy-Item .env.example .env
# Edit .env — at minimum set SECRET_KEY

# 4. Run migrations
python manage.py migrate

# 5. Create initial data (if starting fresh)
python manage.py shell  # paste the shell commands from docs/setup.md

# 6. Start server
python manage.py runserver
```

**Access at:** http://localhost:8000

| URL | Page |
|---|---|
| `/accounts/login/` | Login |
| `/` | Role-based dashboard redirect |
| `/admin/` | Django admin |
| `/tokens/issue/` | Issue lunch tokens |
| `/pos/` | Tea/snack POS |
| `/employees/` | Employee management |
| `/billing/` | Monthly bills |
| `/requests/` | Open/close requests |
| `/menu/` | Menu management |
| `/reports/` | Reports |

**Default dev credentials (seeded):**
- `admin@cafems.com` / `admin123!@#` (Super Admin)
- `cafe_admin@democafe.com` / `admin123!@#` (Tenant Admin)

> ⚠️ Change passwords before going to production.

---

## 🏗️ Architecture

- **Backend:** Django 5.x, Django REST Framework
- **Frontend:** Bootstrap 5.3, Alpine.js, htmx (all self-hosted — no CDN)
- **Typography:** Inter (self-hosted Google Font)
- **Task Queue:** Celery + Redis
- **Dev DB:** SQLite
- **Prod DB:** PostgreSQL (recommended with django-tenants for true schema isolation)

See [`docs/architecture.md`](docs/architecture.md) for the full architecture overview.

---

## 📁 Project Structure

```
c:\cafems\
├── apps/
│   ├── core/            # Mixins, utils, abstract models, dashboard views
│   ├── accounts/        # Custom User (email login, roles, dark mode)
│   ├── tenants/         # Multi-tenant management
│   ├── employees/       # Employee profiles, audit log
│   ├── menu/            # Menu categories, items, lunch plan, estimates
│   ├── pos/             # Tea/Snack POS
│   ├── tokens/          # Lunch token issuance (with Roti-Open lock)
│   ├── requests_app/    # Open/Close requests (2PM PKT cutoff)
│   ├── billing/         # Monthly billing engine + payment workflow
│   ├── notifications/   # In-app notification system
│   └── reports/         # Monthly reports
├── cafems/              # Django project config (settings/, urls, celery)
├── templates/           # Global templates (base, sidebar, navbar, components)
├── static/              # Bootstrap, htmx, Alpine.js, Inter fonts (self-hosted)
├── docs/                # Setup guide, architecture, billing formula
└── requirements.txt
```

---

## 📚 Documentation

| File | Contents |
|---|---|
| [`docs/setup.md`](docs/setup.md) | Installation guide, initial data, Celery setup |
| [`docs/configuration.md`](docs/configuration.md) | Environment variables, PKT timezone rules, email, tenant setup |
| [`docs/testing.md`](docs/testing.md) | Running pytest, coverage reports, testing tenant isolation |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | FAQ & exact diagnostic shell commands for common issues |
| [`docs/architecture.md`](docs/architecture.md) | System architecture, module map, request lifecycle |
| [`docs/billing-formula.md`](docs/billing-formula.md) | Full billing calculation with numeric examples |
| [`docs/decisions.md`](docs/decisions.md) | Running log of architectural & design decisions |
| [`docs/cafems_build_prompt.md`](docs/cafems_build_prompt.md) | Original spec / business requirements |

---

## 🧪 Running Tests

```powershell
pip install pytest-django pytest-cov
pytest --tb=short
```

---

## 📄 License

Internal use only. All rights reserved.
