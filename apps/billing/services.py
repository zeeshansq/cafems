"""Billing App – Business Logic Service."""
import datetime
from decimal import Decimal
from django.db.models import Sum

from apps.employees.models import Employee, MembershipType
from apps.tokens.models import LunchToken, TokenStatus
from .models import MonthlyBill, MiscCharge, BillStatus


class BillingService:
    """
    Encapsulates all monthly billing calculation logic.
    See docs/billing-formula.md for the full formula.
    """

    def __init__(self, tenant, month: datetime.date, actor=None):
        self.tenant = tenant
        # Normalize to first of month
        self.month = month.replace(day=1)
        self.actor = actor
        import calendar
        last_day = calendar.monthrange(month.year, month.month)[1]
        self.period_start = self.month
        self.period_end = self.month.replace(day=last_day)

    def generate_all(self) -> int:
        """Generate draft bills for all eligible employees for the month. Returns count created."""
        from .models import MonthlyBillRun, MonthlyBillRunStatus

        MonthlyBillRun.objects.update_or_create(
            tenant=self.tenant,
            period_start=self.period_start,
            defaults={
                "period_end": self.period_end,
                "status": MonthlyBillRunStatus.DRAFT,
                "generated_by": self.actor,
            }
        )

        eligible = Employee.objects.filter(
            tenant=self.tenant, is_active=True, membership_status=True
        ).exclude(membership_type=MembershipType.TEMP_CLOSE)

        misc_charges = list(MiscCharge.objects.filter(tenant=self.tenant, month=self.month))
        total_misc = sum((c.amount for c in misc_charges), Decimal("0.00"))

        count = 0
        for employee in eligible:
            # Replace existing unapproved/unpaid bill for this period if regenerating
            MonthlyBill.objects.filter(
                tenant=self.tenant,
                employee=employee,
                period_start=self.period_start,
                status=BillStatus.UNPAID,
            ).delete()

            bill = self._build_bill(employee, total_misc, misc_charges)
            if bill:
                bill.save()
                count += 1

        return count

    def _build_bill(self, employee: Employee, total_misc: Decimal, misc_charges) -> MonthlyBill:
        """Build (but don't save) a MonthlyBill for one employee."""
        tokens = LunchToken.objects.filter(
            tenant=self.tenant,
            employee=employee,
            date__range=(self.period_start, self.period_end),
            status=TokenStatus.ISSUED,
        )

        from django.db.models import Sum
        token_count = tokens.aggregate(total=Sum("token_qty"))["total"] or 0

        # Token line items
        token_total = Decimal("0.00")
        extra_roti_total = Decimal("0.00")
        extra_sweet_total = Decimal("0.00")
        adjustment_total = Decimal("0.00")
        line_items = []

        # Calculate totals across tokens
        total_tokens_qty = 0
        total_extra_roti_qty = 0
        total_extra_sweet_qty = 0

        for token in tokens:
            total_tokens_qty += token.token_qty
            total_extra_roti_qty += (token.extra_roti_qty or 0)
            total_extra_sweet_qty += (token.extra_sweet_qty or 0)
            price = (token.price_snapshot or Decimal("0.00"))
            adj = (token.adjustment_amount or Decimal("0.00"))
            token_total += price * token.token_qty
            adjustment_total += adj * token.token_qty

        # Extra Roti & Sweet calculations
        if total_extra_roti_qty > 0:
            extra_roti_total = Decimal(str(total_extra_roti_qty * 15.00))
        if total_extra_sweet_qty > 0:
            extra_sweet_total = Decimal(str(total_extra_sweet_qty * 35.00))

        # Build clean summary line items
        if total_tokens_qty > 0:
            avg_unit_rate = (token_total / Decimal(total_tokens_qty)).quantize(Decimal("0.01")) if total_tokens_qty else token_total
            line_items.append({
                "description": f"Lunch Tokens ({total_tokens_qty} Days)",
                "quantity": total_tokens_qty,
                "unit_price": f"{avg_unit_rate:,.2f}",
                "total": f"{token_total:,.2f}",
            })

        if extra_roti_total > 0:
            line_items.append({
                "description": "Extra Roti Issued",
                "quantity": total_extra_roti_qty or int(extra_roti_total // Decimal("15.00")),
                "unit_price": "15.00",
                "total": f"{extra_roti_total:,.2f}",
            })

        if extra_sweet_total > 0:
            line_items.append({
                "description": "Extra Sweet Issued",
                "quantity": total_extra_sweet_qty or int(extra_sweet_total // Decimal("35.00")),
                "unit_price": "35.00",
                "total": f"{extra_sweet_total:,.2f}",
            })

        # Misc charges eligibility check (spec §4)
        misc_applicable = Decimal("0.00")
        is_roti_pending = (
            employee.membership_type == MembershipType.ROTI_OPEN
            and employee.security_deposit_pending > 0
        )
        if token_count > 0 and not is_roti_pending:
            misc_applicable = total_misc
            for charge in misc_charges:
                line_items.append({
                    "description": f"Misc: {charge.description}",
                    "quantity": 1,
                    "unit_price": f"{charge.amount:,.2f}",
                    "total": f"{charge.amount:,.2f}",
                })

        # Previous balance carryforward
        previous_balance = Decimal("0.00")
        prev_bill = MonthlyBill.objects.filter(
            tenant=self.tenant,
            employee=employee,
            status=BillStatus.PARTIALLY_PAID,
        ).order_by("-period_end").first()
        if prev_bill:
            last_pay = prev_bill.payments.order_by("-payment_date").first()
            if last_pay:
                previous_balance = last_pay.remaining_balance
            else:
                previous_balance = prev_bill.total

        deposit_pending = employee.security_deposit_pending

        bill = MonthlyBill(
            tenant=self.tenant,
            employee=employee,
            period_start=self.period_start,
            period_end=self.period_end,
            line_items=line_items,
            total_token_qty=total_tokens_qty,
            total_extra_roti_qty=total_extra_roti_qty,
            total_extra_sweet_qty=total_extra_sweet_qty,
            token_total=token_total,
            extra_roti_total=extra_roti_total,
            extra_sweet_total=extra_sweet_total,
            misc_charges_total=misc_applicable,
            adjustment_total=adjustment_total,
            security_deposit_pending=deposit_pending,
            previous_balance=previous_balance,
            status=BillStatus.UNPAID,
            generated_by=self.actor,
        )
        bill.calculate_totals()
        return bill
