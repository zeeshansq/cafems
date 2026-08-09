# CafeMS — Configuration Guide

This document explains all environment variables, timezone configurations, email setup, tenant onboarding, and offline static assets configuration.

---

## 1. Environment Variables (`.env`)

Every environment setting is managed via `django-environ`. Below is a reference of all available variables:

| Variable | Type | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | String | *Required* | Django secret key for cryptographic signing |
| `DEBUG` | Boolean | `False` | Enable/disable debug mode (MUST be False in prod) |
| `ALLOWED_HOSTS` | List | `localhost,127.0.0.1` | Comma-separated list of allowed hostnames/domains |
| `DATABASE_URL` | String | `sqlite:///db.sqlite3` | Database connection URL |
| `CELERY_BROKER_URL` | String | `redis://localhost:6379/0` | Redis broker URL for Celery |
| `CELERY_RESULT_BACKEND` | String | `redis://localhost:6379/0` | Redis result backend for Celery |
| `EMAIL_BACKEND` | String | `django.core.mail.backends.console.EmailBackend` | Email backend class |
| `EMAIL_HOST` | String | `smtp.gmail.com` | SMTP host for outgoing email |
| `EMAIL_PORT` | Integer | `585` | SMTP port |
| `EMAIL_HOST_USER` | String | `""` | SMTP username |
| `EMAIL_HOST_PASSWORD` | String | `""` | SMTP password |
| `TIME_ZONE` | String | `Asia/Karachi` | Default system timezone |

---

## 2. Timezone Specifics (Pakistan PKT)

CafeMS enforces Pakistan Standard Time (`Asia/Karachi`) for all business rules:
- `TIME_ZONE = "Asia/Karachi"` set in `cafems/settings/base.py`.
- `USE_TZ = True`.
- **Cutoff logic**: Open/Close requests must be submitted at least 1 day prior by **2:00 PM PKT**.
- Cutoff evaluation uses `zoneinfo.ZoneInfo("Asia/Karachi")` to guarantee correct timezone offset regardless of host OS timezone.

---

## 3. Email Backend Setup

### Development Mode
By default, `EMAIL_BACKEND` is set to console mode. All sent emails are printed directly to standard output:
```dotenv
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Production SMTP Mode
To send actual emails when monthly bills are published:
```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_api_key
DEFAULT_FROM_EMAIL=CafeMS Notifications <noreply@yourdomain.com>
```

---

## 4. Tenant Provisioning

To register a new organization (tenant):
1. Log in as Super Admin (`super_admin` role).
2. Navigate to **Tenant Control Center** (`/tenants/new/`).
3. Fill in organization title, slug, and primary contact email.
4. Primary domain will automatically map to `slug.yourdomain.com` or custom hostname.

---

## 5. Offline Assets (Fonts & Icons)

CafeMS operates 100% offline without CDN dependencies:
- **Inter Font**: Self-hosted WOFF2 files stored in `static/fonts/inter/`.
- **Bootstrap Icons**: Self-hosted WOFF/WOFF2 font files stored in `static/icons/`.
- CSS font-face declarations reference local paths (`/static/fonts/` and `/static/icons/`).
