# CafeMS — Testing Guide

This document explains how to execute the automated test suite, generate coverage reports, and test business logic.

---

## 1. Running Tests with Pytest

To run the entire test suite:

```powershell
# Activate environment
C:\venv\envcafe\Scripts\Activate.ps1

# Run tests
pytest
```

---

## 2. Test Coverage

To run tests and view code coverage:

```powershell
pytest --cov=apps --cov-report=term-missing
```

Coverage configuration is defined in `setup.cfg`:
```ini
[coverage:run]
source = apps
omit =
    */migrations/*
    */tests/*
    */admin.py
```

---

## 3. Test Modules Structure

| Test Path | Scope |
|---|---|
| `apps/accounts/tests/test_models.py` | Custom User model, email uniqueness, role predicate methods |
| `apps/accounts/tests/test_views.py` | Login view, authenticated redirects, logout, profile view |
| `apps/billing/tests/test_billing.py` | `BillingService` draft generation, calculation logic |
| `apps/core/tests/test_utils.py` | 2:00 PM PKT cutoff logic (`is_before_cutoff`) |

---

## 4. Testing Tenant Data Isolation

Tenant isolation is verified via ORM unit tests:
```python
def test_tenant_isolation():
    tenant1 = Tenant.objects.create(title="Cafe A", slug="cafe-a")
    tenant2 = Tenant.objects.create(title="Cafe B", slug="cafe-b")
    
    emp1 = Employee.objects.create(tenant=tenant1, full_name="Alice", pno="101")
    emp2 = Employee.objects.create(tenant=tenant2, full_name="Bob", pno="102")
    
    # Querying tenant 1 employees must never leak tenant 2 data
    qs = Employee.objects.filter(tenant=tenant1)
    assert emp1 in qs
    assert emp2 not in qs
```

---

## 5. Testing Celery Tasks & Cutoff Logic

To run Celery tasks synchronously during tests:
```python
from apps.tokens.tasks import snapshot_daily_price, remind_estimate_not_set

# Tasks execute inline when called directly in tests
snapshot_daily_price()
```
