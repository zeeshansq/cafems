# CafeMS — Billing Formula

## Monthly Bill Calculation

### 1. Token Cost

For each lunch token issued to an employee in the billing period:

```
token_cost = price_snapshot + adjustment_amount
```

Where:
- `price_snapshot` = estimated price at time of issuance (from `DailyLunchEstimate.price_per_token`)
- `adjustment_amount` = pro-rata month-end adjustment (see §3 below)

### 2. Extra Items

```
extra_roti_cost  = extra_roti_qty  × roti_unit_price
extra_sweet_cost = extra_sweet_qty × sweet_unit_price
```

### 3. Month-End Adjustment (Pro-Rata)

At month end, Admin enters:
- `actual_total_cost` — total actual cost of meals for the month (supplier invoice)
- `estimated_total_cost` — sum of all `price_snapshot × 1` for the month

```python
total_tokens = LunchToken.objects.filter(period, status="issued").count()
per_token_estimate = estimated_total_cost / total_tokens  # if total_tokens > 0

actual_per_token = actual_total_cost / total_tokens
per_token_adjustment = actual_per_token - per_token_estimate

# For each employee:
employee_token_count = employee's tokens in period
employee_adjustment = per_token_adjustment × employee_token_count
```

**Numeric Example:**

| Item | Value |
|---|---|
| Total tokens issued (all employees) | 200 |
| Estimated total cost | PKR 40,000 (PKR 200/token average) |
| Actual total cost (supplier) | PKR 44,000 |
| Per-token adjustment | PKR 44,000/200 - PKR 200 = PKR 20 |
| Employee with 15 tokens | PKR 20 × 15 = PKR 300 adjustment |

### 4. Misc Charge Eligibility

A misc charge applies to an employee **only if**:
1. They have ≥ 1 issued token in the billing period, **AND**
2. They are **NOT** a Roti-Open member with a pending security deposit

```python
def is_misc_eligible(employee, period_start, period_end):
    has_tokens = LunchToken.objects.filter(
        employee=employee,
        date__range=(period_start, period_end),
        status="issued"
    ).exists()
    
    is_roti_pending = (
        employee.membership_type == "roti_open"
        and employee.security_deposit_pending > 0
    )
    
    return has_tokens and not is_roti_pending
```

### 5. Security Deposit Carryforward

```python
if employee.security_deposit_pending > 0:
    bill.security_deposit_pending = employee.security_deposit_pending
    # On payment: if paid, zero out employee.security_deposit_pending
```

### 6. Previous Balance Carryforward

```python
last_bill = MonthlyBill.objects.filter(
    employee=employee, status__in=["published", "partially_paid"]
).order_by("-period_end").first()

if last_bill and last_bill.status == "partially_paid":
    last_payment = last_bill.payments.order_by("-payment_date").first()
    bill.previous_balance = last_payment.remaining_balance if last_payment else last_bill.total
```

### 7. Final Bill Total

```
bill.subtotal = token_total + extra_roti_total + extra_sweet_total
              + misc_charges_total + adjustment_total

bill.total = subtotal + security_deposit_pending + previous_balance
```

---

## Bill Workflow States

```
Draft → Reviewed → Approved → Published → Paid (or Partially Paid)
         (Staff)   (Committee)  (Admin)
```

- Only **Admin** can generate Draft or Publish
- Only **Committee** can Approve
- Publishing triggers HTML email to employee + in-app notification
- Partial payment: remaining balance auto-flows to next bill as `previous_balance`
