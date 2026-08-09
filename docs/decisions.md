# CafeMS — Architectural & Design Decisions Log

A running log of design decisions, trade-offs, and resolutions adopted during development.

---

## Decision 1: Shared Schema with Tenant FK for Development, Schema-Per-Tenant Architecture Ready for Production

- **Context**: Spec §1 specifies schema-based multi-tenancy (`django-tenants`) for PostgreSQL prod while supporting local development.
- **Resolution**: Models inherit from abstract base `TenantModel` containing `tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)`. In production PostgreSQL, `django-tenants` isolates schemas; in SQLite development, tenant middleware automatically injects `request.tenant` into context and filters queries.
- **Rationale**: Guarantees fast, dependency-free local development with SQLite while maintaining zero-leak tenant isolation.

---

## Decision 2: In-App Notifications with htmx Polling

- **Context**: Spec §1 & §5.6 allows either WebSockets (`django-channels`) or htmx polling.
- **Resolution**: Selected **htmx polling** every 15 seconds for unread count badge and live dashboard counters (`/api/v1/notifications/unread-count/`).
- **Rationale**: Simpler deployment infrastructure (no ASGI/channel layer requirement), highly resilient, zero browser compatibility issues.

---

## Decision 3: Timezone Handling via `zoneinfo` (Python Standard Library)

- **Context**: Spec §1 & §5.3 requires strict `Asia/Karachi` 2:00 PM PKT cutoff logic.
- **Resolution**: Used Python 3.9+ standard library `zoneinfo.ZoneInfo("Asia/Karachi")` instead of external `pytz`.
- **Rationale**: `zoneinfo` is PEP 615 standard in Python 3.9+, handles daylight savings transparently, and avoids deprecated `pytz` `.localize()` methods.

---

## Decision 4: Per-Template CSS/JS Isolation Pattern

- **Context**: System guidelines require distinct styling and separate CSS/JS files per template.
- **Resolution**: Enforced strict per-template static structure:
  `templates/<app>/<page>.html` maps to `static/<app>/css/<page>.css` and `static/<app>/js/<page>.js`. Loaded via `{% block extra_css %}` and `{% block extra_js %}`.
- **Rationale**: Eliminates CSS specificity leakage between pages, improves page load speeds, and maintains strict modularity.

---

## Decision 5: Price Snapshotting & Employee Billing Privacy

- **Context**: Spec §5.7 requires that employee portal displays token history and attendance, but hides prices until bills are published.
- **Resolution**: `LunchToken.price_snapshot` remains nullable until price is finalized or bill is published. Employee views (`my_bills`, `employee_dashboard`) display item quantities and status, hiding individual token price snapshots until the bill reaches `PUBLISHED` status.
- **Rationale**: Protects employee trust and enforces administrative billing privacy rules.
