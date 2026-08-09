# PROJECT BUILD PROMPT: Multi-Tenant Cafe Management System (CafeMS)

## ROLE & OBJECTIVE

You are a senior full-stack Django engineer. Build a **production-grade, multi-tenant Cafe/Cafeteria Management System** that can be sold/deployed to multiple organizations (each an isolated "tenant" — a company cafe, canteen, or mess). Follow this document as the single source of truth. Where a decision isn't specified, choose the most robust, secure, and maintainable option consistent with the patterns below, and document that decision in `docs/decisions.md`.

Work iteratively: scaffold the project, implement app-by-app, write tests as you go, and keep `docs/` updated continuously — not as a final step.

---

## 1. TECH STACK

- **Backend:** Python 3.12+, Django 5.x (latest stable), Django REST Framework (for the employee-portal/API and any AJAX-heavy POS screens)
- **Multi-tenancy:** `django-tenants` (schema-based, Postgres) — preferred over shared-table tenancy for data isolation and billing safety. If schema-based is rejected, fall back to a shared-schema `Tenant` FK-on-every-model approach with a middleware-enforced tenant scoping manager — but schema-based is strongly preferred for a billing-sensitive product.
- **Database:** PostgreSQL 16+
- **Async/scheduled jobs:** Celery + Redis (broker & result backend) — required for: daily closing-report generation, reminder notifications, monthly bill scheduling, email dispatch, the 2:00 PM cutoff enforcement job
- **Timezone:** `Asia/Karachi` set at the Django settings level (`TIME_ZONE`), `USE_TZ = True`, and Celery beat schedule must be timezone-aware. All "1 day before by 2:00 PM" cutoff logic must be computed in Pakistan time regardless of server locale.
- **Frontend:** Server-rendered Django templates + Bootstrap 5.3 (latest), vanilla JS / htmx or Alpine.js for POS-page interactivity (no heavy SPA framework needed — POS screen must feel instant, so use htmx/Alpine + minimal fetch calls, not full page reloads)
- **Fonts/Icons:** Must work fully offline — self-host Google Fonts (e.g., Inter/Poppins) and an icon set (Bootstrap Icons or Font Awesome Free) as static files. No CDN dependency at runtime.
- **PDF/Excel export:** `WeasyPrint` or `reportlab` for bill PDFs, `openpyxl` for Excel exports
- **Email:** Django email backend with HTML templates (`django-templated-mail` or custom), premium responsive HTML email for monthly bills
- **Auth:** Django's built-in auth extended with a `role` field / groups; consider `django-allauth` only if social login is needed (not required here)
- **Notifications:** In-app notification model + `django-channels`/websockets OPTIONAL for live push; polling via htmx every N seconds is an acceptable simpler alternative — pick one and document it
- **Environment/config:** `django-environ` or `python-decouple`, `.env` file, never commit secrets
- **Testing:** `pytest-django`, `factory_boy` for fixtures, `coverage.py`
- **Code quality:** `black`, `isort`, `flake8`/`ruff`, pre-commit hooks

---

## 2. MULTI-TENANCY REQUIREMENTS

- Each tenant (organization) has: `title`, `short_title`, `logo` (image upload), `status` (active/inactive), `domain`/`subdomain` or `slug` for routing, `created_at`, `contact_email`, `currency` (default PKR), `timezone` (default Asia/Karachi, but allow override per tenant for future-proofing).
- Tenant's `title`, `short_title`, and `logo` must be dynamically injected into: browser tab title, navbar/sidebar, login page, all generated PDFs, and all outgoing emails — via a context processor, not hardcoded.
- Public schema hosts: tenant registration/onboarding (super-admin only), a landing/marketing page, and the tenant-picker/login routing.
- Each tenant schema is fully isolated: employees, tokens, bills, menus, notifications never leak across tenants.
- Build a **Super Admin** (platform owner) role above the four in-tenant roles, who can create/suspend/delete tenants and view platform-wide health — but cannot see tenant business data.

---

## 3. USER ROLES & PERMISSIONS

| Role | Data Entry | Date Restriction | Reports | Admin Actions |
|---|---|---|---|---|
| **Admin** | Full | Any date (past/present) | All | Manage tenant settings, users, menu, bill generation/publish, override everything |
| **Cafe Staff** | Full | **Current date only** | Daily/own-shift reports | Issue tokens/tea items, review generated bills, acknowledge member requests, case-by-case override of Roti-Open token lock |
| **Committee Member** | None | N/A | All reports (read-only) | Approve monthly bills only |
| **Employee** | Self-service only | N/A | Own data only | View own dashboard, submit open/close token requests, view menu, view bills, make/track payments if online payment is added |
| **Super Admin** (platform) | N/A | N/A | Platform-level | Tenant provisioning/suspension |

Implement this via Django Groups + Permissions, and additionally enforce role checks in views/mixins (`RoleRequiredMixin`) — don't rely on template hiding alone; enforce server-side.

---

## 4. CORE DATA MODELS (minimum set — expand as needed)

- **Tenant** (see §2)
- **Employee/Profile**: `system_id`, `PNO`, `register_number`, `full_name`, `email`, `mobile`, `telephone_extension`, `gender`, `designation`, `category` (Officer/Staff), `membership_status` (Yes/No), `membership_type` (Full Open / Roti Open / Temp Close), `security_deposit_paid`, `security_deposit_pending`, `is_active`, linked `User` account, `department`(optional), `date_joined`
  - Business rule: when `security_deposit_pending` is paid, it auto-zeroes and reflects in next bill; if pending, it auto-appends into the generated monthly bill.
- **MenuCategory / TeaItem**: name, fixed price, category (tea/snack), availability toggle, image (optional)
- **LunchMenuPlan**: month, week-of-month (1–5), day (Mon–Fri only, exclude Sat/Sun), dish name, description, contains sweet (bool), planned by/approved by, published flag
- **DailyLunchEstimate**: date, planned token count, dish (FK to that day's LunchMenuPlan entry), price-per-token for the day (can be finalized later), created_by, locked flag once issuance starts
- **LunchToken (Issuance)**: date, employee (FK), token_number (1–3 per day), issued_by (staff), issue_time, extra_roti_qty, extra_sweet_qty, status (issued/cancelled), price snapshot at issuance (nullable until finalized), month-end adjustment amount (nullable)
- **TeaItemSale**: date, item, quantity, unit_price, buyer (employee FK nullable for walk-in), amount_paid, payment_method, issued_by, timestamp — this is the POS transaction log
- **TokenOpenCloseRequest**: employee, request_type (open/close), date_range_start, date_range_end, reason, submitted_at, status (pending/acknowledged/rejected), acknowledged_by, acknowledged_at — enforce the "must be submitted ≥1 day before 2:00 PM PKT" rule at the model/serializer level with a clear validation error, and make it **immutable once submitted** (no edits by the employee, per spec — cancellation by staff/admin only).
- **MonthlyBill**: tenant, employee, period_start, period_end, line items (tokens, extra roti/sweet, misc charges, adjustment cost, previous pending carryforward, security deposit pending), subtotal, total, status (draft/reviewed/approved/published/paid/partially_paid), generated_by, reviewed_by, approved_by, published_at
- **MiscCharge**: tenant, month, amount, description, rule: only applied to members with ≥1 token in that period AND not (pending-amount-with-roti-only) — implement the exact exclusion rule from spec.
- **Payment**: bill FK, amount_paid, payment_date, method, received_by, remaining_balance (auto carried to next bill if partial)
- **Notification**: tenant, recipient(s), type (request_submitted, request_acknowledged, bill_generated, bill_pending, bill_published), message, is_read, created_at, link/target
- **AuditLog**: actor, action, model, object_id, before/after snapshot (JSON), timestamp — required since Admin can edit past dates; every backdated edit must be logged.

---

## 5. KEY FUNCTIONAL MODULES

### 5.1 Tea/Snack POS
- Fast, keyboard/touch-friendly POS screen (htmx/Alpine, no full reloads)
- Quick-amount buttons (e.g., exact/50/100/500/1000), auto-calculated change/remaining amount
- Item grid with images/prices, cart-style running total
- Works for both walk-in customers (no employee link) and employees
- End-of-day summary: items sold, quantities, total collected, by payment method
- Smart behaviors to add: recently-bought quick-repeat, low-stock/sold-out flag if inventory is tracked (optional inventory module — flag as a future enhancement if out of scope), duplicate-transaction guard

### 5.2 Lunch Token System
- Admin/staff sets `DailyLunchEstimate` (planned tokens) each morning; this **must be visible on the issuance page** as a live counter: `Issued X / Estimated Y` with remaining count, color-coded (green/amber/red as it approaches zero)
- Enforce: 1 token/day per member, max 3/day (business must clarify whether "max 3" means 3 tokens in one transaction or across the day — default to: max 3 tokens total per member per day, configurable per tenant)
- Roti-Open members: token field disabled by default in the POS UI; staff has an explicit "Override for today" action, logged in AuditLog
- Temp-Close members: excluded from the daily "pending token" list entirely unless they have an active date-range Open request
- Extra roti/extra sweet purchasable alongside a token by members — captured as separate line items tied to the token, billed monthly

### 5.3 Open/Close Requests & Cutoff Enforcement
- Employee portal form: choose Open or Close, date range, optional reason
- Server-side validation: reject if submission is after 2:00 PM PKT on the day before the range start (use `zoneinfo`/`pytz` with `Asia/Karachi`, never naive datetime)
- Immutable after submission (employee cannot edit; only cancel-and-resubmit if still before cutoff, or staff/admin can override)
- Cafe Staff dashboard shows pending requests with an **Acknowledge** button → fires in-app notification to the employee

### 5.4 Daily Closing Report
- End-of-day report listing: all "expected" members (Full Open + any temp-open-for-today Roti-Open/Temp-Close members) who neither issued a token nor submitted a close request for that date
- Quick inline action per row: "Charge Token" (creates a token retroactively for billing) — Admin only for past dates, Staff for current date
- Report must be filterable by date, membership type, department

### 5.5 Monthly Billing Engine
- Admin selects employee(s) + date range (defaults to calendar month) → system aggregates: tokens (at finalized daily price + month-end adjustment), extra roti/sweet, misc charges (per §4 rule), pending security deposit, previous partial-payment carryforward
- **Adjustment cost**: at month-end, admin enters actual total purchase cost vs. sum of daily estimated prices; system computes per-token adjustment and applies pro-rata across that month's tokens (document the exact formula used in `docs/billing-formula.md`)
- Workflow states: `Draft` (Admin generates) → `Reviewed` (Cafe Staff) → `Approved` (Committee Member) → `Published/Dispatched` (Admin emails it out)
- Only after Approved can Admin Publish; Publish triggers the premium HTML email + in-app notification
- Payment recording: full or partial; partial remainder auto-flows into next month's bill as a carryforward line item
- On full payment receipt: auto-send a "payment received" confirmation email/notification

### 5.6 Notifications
- In-app notification center (bell icon, unread count) for: new open/close request (→ Staff/Admin), request acknowledged (→ Employee), bill generated/pending/published (→ relevant roles)
- Admin can manually trigger email + in-app "reminder" blast for unpaid bills
- Notification preferences per user (optional nice-to-have — flag if implemented)

### 5.7 Employee Self-Service Portal
- Dashboard: today's status (token issued? open/close status), quick links
- View published/approved monthly menu (read-only, current + past months)
- View bill history (only billed/finalized amounts are shown — never show token prices before the bill is finalized/published, per spec)
- View current month's attendance: tokens, extra roti, extra sweet, date+time — but price hidden until billed
- Submit/view open-close requests and their status
- View security deposit status (paid/pending)

### 5.8 Reports (Committee + Admin)
- Monthly consumption report, revenue report (tea + lunch), outstanding dues report, membership status report, audit/backdated-edit report
- Export to PDF and Excel from every report screen

---

## 6. UI/UX REQUIREMENTS

- Premium, modern, advanced-looking login page as the system's main/first page — glassmorphism or soft-gradient card, tenant logo/title dynamically rendered, subtle motion (CSS transitions only, no heavy JS animation libraries)
- Consistent Bootstrap 5.3 design system: define a custom SCSS/CSS theme (color tokens, spacing, shadows) rather than default Bootstrap look — this must NOT look like a stock Bootstrap template
- Light/dark theme toggle (persisted per user)
- All fonts and icons self-hosted/offline-capable — verify with network disabled
- Responsive: POS screens optimized for tablet/desktop; employee portal optimized for mobile too
- Empty states, loading states, and toast-style success/error feedback throughout (no jarring Django default messages framework styling — restyle it)

---

## 7. SECURITY & DATA INTEGRITY

- Enforce role-based access at the view/serializer layer, not just UI
- Rate-limit login and POS endpoints against abuse
- CSRF protection on all forms; CSRF-safe htmx setup
- Every backdated (past-date) edit by Admin must write an AuditLog entry with before/after diff
- Tenant isolation must be tested explicitly (a test that proves tenant A cannot query tenant B's data even via direct ORM misuse)
- Sensitive fields (security deposit amounts, personal contact info) restricted appropriately per role
- File upload validation for logos/images (type, size limits)

---

## 8. DOCUMENTATION REQUIREMENTS (MANDATORY — build this alongside the code, not at the end)

Create and continuously update a `docs/` folder at the project root with at least:

- `docs/setup.md` — full local dev setup: prerequisites, `.env` template, Postgres + Redis setup, `django-tenants` schema creation commands, `python manage.py migrate_schemas`, creating the first tenant, creating a superuser per tenant, running Celery worker + beat, running the dev server
- `docs/configuration.md` — every environment variable explained, timezone/Celery configuration specifics for Pakistan, email backend configuration (SMTP settings), how to add a new tenant, how to configure the offline fonts/icons build step
- `docs/testing.md` — how to run the test suite (`pytest`), how to run with coverage, how tenant-isolation tests work, how to seed test data/fixtures, how to test the Celery beat cutoff-enforcement job
- `docs/troubleshooting.md` — a running list of common issues and their fix commands, e.g.:
  - Celery worker not picking up tasks → check commands
  - Redis connection refused → check commands
  - `django-tenants` schema migration errors → check commands
  - Timezone mismatch symptoms and how to verify `TIME_ZONE`/PKT cutoff behavior
  - Static/offline font 404s → collectstatic commands
  - Email not sending in dev (console backend) vs prod (SMTP) checklist
  Every entry should include the actual shell/manage.py command to diagnose and fix, not just prose.
- `docs/architecture.md` — high-level module map, model relationships (ERD or Mermaid diagram), request lifecycle for tenant resolution
- `docs/billing-formula.md` — the exact monthly adjustment-cost and misc-charge calculation logic, with a worked numeric example
- `docs/decisions.md` — a running log of any place you (the agent) had to make a judgment call where the spec was ambiguous, and what you chose and why

Keep a `README.md` at the root that links to all of the above.

---

## 9. DELIVERY EXPECTATIONS

- Build incrementally: (1) project scaffold + multi-tenancy + auth/roles, (2) employee & menu models + admin, (3) POS/tea module, (4) lunch token module + estimates, (5) open/close requests + cutoff job, (6) daily closing report, (7) monthly billing engine + workflow, (8) notifications, (9) employee portal, (10) reports/exports, (11) premium UI pass, (12) docs polish + test coverage pass.
- Write tests alongside each module, not at the end.
- Flag any requirement above that conflicts with Django/`django-tenants` best practices and propose the resolution in `docs/decisions.md` rather than silently deviating.
- Do not stub critical business logic (billing math, cutoff enforcement, tenant isolation) — these must be fully implemented and tested, since they are the core value of the product.
