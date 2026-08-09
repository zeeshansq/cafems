# CafeMS — Setup Guide

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.12+ | Python 3.14 works (installed) |
| pip | Latest | Run `python -m pip install --upgrade pip` |
| Redis | 6+ | Required for Celery tasks |
| PostgreSQL | 16+ | **Production only** (SQLite used for dev) |

---

## 1. Virtual Environment

The project uses `C:\venv\envcafe\`:

```powershell
# Activate
C:\venv\envcafe\Scripts\Activate.ps1

# Verify
python --version  # 3.12+
```

---

## 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## 3. Environment Configuration

Copy `.env.example` to `.env` and configure:

```powershell
Copy-Item .env.example .env
```

**Minimum required values:**
```dotenv
SECRET_KEY=your-secure-random-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
CELERY_BROKER_URL=redis://localhost:6379/0
```

Generate a secret key:
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 4. Database Setup

### Development (SQLite)
```powershell
python manage.py migrate
```

### Production (PostgreSQL)
```sql
-- In psql:
CREATE DATABASE cafems_db;
CREATE USER cafems_user WITH PASSWORD 'cafems_pass';
GRANT ALL PRIVILEGES ON DATABASE cafems_db TO cafems_user;
ALTER USER cafems_user CREATEDB;
```

Update `.env`:
```dotenv
DATABASE_URL=postgresql://cafems_user:cafems_pass@localhost:5432/cafems_db
```

Run migrations:
```powershell
python manage.py migrate
```

---

## 5. Create Initial Data

```powershell
# Using Django shell
python manage.py shell

# Then in the shell:
from apps.tenants.models import Tenant, Domain
from apps.accounts.models import User, UserRole

tenant = Tenant.objects.create(
    title="My Cafe",
    short_title="MC",
    slug="my-cafe",
    contact_email="admin@mycafe.com",
    status="active",
)
Domain.objects.create(tenant=tenant, domain="localhost", is_primary=True)
User.objects.create_superuser(
    email="admin@cafems.com",
    username="admin@cafems.com",
    password="YourSecurePassword123!",
    role=UserRole.SUPER_ADMIN,
    first_name="Super", last_name="Admin",
)
```

---

## 6. Start the Development Server

```powershell
python manage.py runserver
```

Access at: **http://localhost:8000**

| URL | Description |
|---|---|
| `/accounts/login/` | Login page |
| `/admin/` | Django admin |
| `/dashboard/` | Role-based dashboard redirect |

**Default test credentials (dev seed):**
| Email | Password | Role |
|---|---|---|
| admin@cafems.com | admin123!@# | Super Admin |
| cafe_admin@democafe.com | admin123!@# | Admin |

> ⚠️ **Change these passwords immediately in any shared or production environment.**

---

## 7. Start Celery Worker

Open a second terminal:

```powershell
# Activate venv first
C:\venv\envcafe\Scripts\Activate.ps1

# Start worker
celery -A cafems worker -l info

# Start beat scheduler (separate terminal)
celery -A cafems beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## 8. Static Files

For development (served automatically by Django):
```powershell
python manage.py collectstatic --noinput
```

All fonts, Bootstrap, htmx, Alpine.js are **pre-downloaded** to `static/` — **no CDN required**.

---

## 9. Project Structure

```
c:\cafems\
├── cafems/                    # Django project config
│   ├── settings/
│   │   ├── base.py            # Shared settings
│   │   ├── development.py     # SQLite dev
│   │   └── production.py      # PostgreSQL prod
│   ├── urls.py                # Main URL config
│   ├── celery.py              # Celery app
│   └── wsgi.py
├── apps/
│   ├── core/                  # Mixins, utils, abstract models
│   ├── accounts/              # Custom User model, login
│   ├── tenants/               # Multi-tenant management
│   ├── employees/             # Employee profiles
│   ├── menu/                  # Menu categories, items, lunch plan
│   ├── pos/                   # Tea/Snack POS
│   ├── tokens/                # Lunch token issuance
│   ├── requests_app/          # Open/Close requests
│   ├── billing/               # Monthly billing engine
│   ├── notifications/         # In-app notifications
│   └── reports/               # Reports & exports
├── templates/                 # Global templates
│   ├── base.html              # Authenticated layout
│   ├── base_minimal.html      # Unauthenticated layout
│   └── components/            # sidebar, navbar, footer
├── static/
│   ├── css/                   # Bootstrap, main.css
│   ├── js/                    # Bootstrap, htmx, Alpine, app.js
│   ├── fonts/inter/           # Self-hosted Inter font
│   └── icons/                 # Bootstrap Icons woff2
├── docs/                      # Documentation
├── .env                       # Environment variables (not committed)
├── .env.example               # Template
├── manage.py
├── requirements.txt
└── setup.cfg                  # pytest, coverage, isort, flake8
```

---

## 10. Per-Page CSS/JS Pattern

Each template has companion static files:

```
apps/<app>/templates/<app>/<page>.html
apps/<app>/static/<app>/css/<page>.css
apps/<app>/static/<app>/js/<page>.js
```

Templates use `{% block extra_css %}` and `{% block extra_js %}` to load page-specific files:

```html
{% block extra_css %}
  <link rel="stylesheet" href="{% static 'accounts/css/login.css' %}">
{% endblock %}

{% block extra_js %}
  <script src="{% static 'accounts/js/login.js' %}"></script>
{% endblock %}
```
