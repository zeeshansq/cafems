"""Menu App – Views."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, View, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from apps.core.mixins import StaffRequiredMixin, AdminRequiredMixin
from .models import (
    TeaItem, MenuCategory, LunchMenuPlan, DailyLunchEstimate,
    Cook, Sweet, RotiPrice, RotiType
)
from .forms import (
    TeaItemForm, LunchMenuPlanForm, DailyLunchEstimateForm,
    CookForm, SweetForm, RotiPriceForm
)


# ── Tea/Snack Item Management ────────────────────────────────────────────────

class MenuIndexView(StaffRequiredMixin, ListView):
    model = TeaItem
    template_name = "menu/menu_index.html"
    context_object_name = "items"

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        return TeaItem.objects.filter(tenant=tenant).select_related("category").order_by("category", "sort_order", "name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        ctx["page_title"] = "Menu Management"
        ctx["categories"] = MenuCategory.objects.filter(tenant=tenant)
        return ctx


class TeaItemCreateView(StaffRequiredMixin, CreateView):
    model = TeaItem
    form_class = TeaItemForm
    template_name = "menu/tea_item_form.html"
    success_url = reverse_lazy("menu:index")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = getattr(self.request, "tenant", None)
        return kwargs

    def form_valid(self, form):
        form.instance.tenant = getattr(self.request, "tenant", None)
        messages.success(self.request, f"'{form.instance.name}' added to menu.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Add Menu Item"
        ctx["action"] = "Create"
        return ctx


class TeaItemUpdateView(StaffRequiredMixin, UpdateView):
    model = TeaItem
    form_class = TeaItemForm
    template_name = "menu/tea_item_form.html"
    success_url = reverse_lazy("menu:index")

    def get_queryset(self):
        return TeaItem.objects.filter(tenant=getattr(self.request, "tenant", None))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = getattr(self.request, "tenant", None)
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"Edit {self.object.name}"
        ctx["action"] = "Update"
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Menu item updated.")
        return super().form_valid(form)


class TeaItemToggleView(StaffRequiredMixin, View):
    """Toggle item availability via htmx."""
    def post(self, request, pk):
        item = get_object_or_404(TeaItem, pk=pk, tenant=getattr(request, "tenant", None))
        item.is_available = not item.is_available
        item.save(update_fields=["is_available"])
        return JsonResponse({"is_available": item.is_available, "name": item.name})


# ── Lunch Menu Plan ──────────────────────────────────────────────────────────

class LunchPlanView(LoginRequiredMixin, ListView):
    model = LunchMenuPlan
    template_name = "menu/lunch_plan.html"
    context_object_name = "plans"

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        return LunchMenuPlan.objects.filter(tenant=tenant).select_related("cook", "roti_price_obj", "sweet").order_by("week_of_month", "day_of_week")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        plans = list(self.get_queryset())
        
        # Build 5-week 7-day matrix
        days_names = [(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday")]
        weeks_matrix = {}
        
        for w in range(1, 6):
            weeks_matrix[w] = []
            for d_val, d_name in days_names:
                p = next((x for x in plans if x.week_of_month == w and x.day_of_week == d_val), None)
                weeks_matrix[w].append({
                    "day_val": d_val,
                    "day_name": d_name,
                    "week_num": w,
                    "plan": p
                })

        ctx["page_title"] = "Generic Master Lunch Menu Plan (5-Week Roster)"
        ctx["weeks_matrix"] = weeks_matrix
        ctx["total_configured"] = len(plans)
        return ctx


class LunchPlanCreateView(StaffRequiredMixin, CreateView):
    model = LunchMenuPlan
    form_class = LunchMenuPlanForm
    template_name = "menu/lunch_plan_form.html"
    success_url = reverse_lazy("menu:lunch_plan")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        w = self.request.GET.get("week")
        d = self.request.GET.get("day")
        if w:
            initial["week_of_month"] = w
        if d:
            initial["day_of_week"] = d
        return initial

    def form_valid(self, form):
        tenant = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        form.instance.tenant = tenant
        form.instance.planned_by = self.request.user
        messages.success(self.request, f"Master Menu Plan entry for Week {form.instance.week_of_month} {form.instance.get_day_of_week_display()} created.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Add Master Lunch Menu Plan Item"
        return ctx


class LunchPlanUpdateView(StaffRequiredMixin, UpdateView):
    model = LunchMenuPlan
    form_class = LunchMenuPlanForm
    template_name = "menu/lunch_plan_form.html"
    success_url = reverse_lazy("menu:lunch_plan")

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        return LunchMenuPlan.objects.filter(tenant=tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Master Menu Plan for Week {form.instance.week_of_month} {form.instance.get_day_of_week_display()} updated.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"Edit Master Lunch Menu Plan ({self.object.dish_name})"
        ctx["is_edit"] = True
        return ctx


class LunchPlanDeleteView(StaffRequiredMixin, View):
    def post(self, request, pk):
        plan = get_object_or_404(LunchMenuPlan, pk=pk, tenant=getattr(request, "tenant", None))
        dish = plan.dish_name
        plan.delete()
        messages.success(request, f"Lunch menu plan '{dish}' deleted.")
        from django.shortcuts import redirect
        return redirect("menu:lunch_plan")


# ── Daily Estimate ───────────────────────────────────────────────────────────

# ── Daily Estimate & Menu Entry Costing ──────────────────────────────────────

class DailyEstimateView(StaffRequiredMixin, ListView):
    model = DailyLunchEstimate
    template_name = "menu/daily_estimate.html"
    context_object_name = "estimates"
    paginate_by = 15

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        qs = DailyLunchEstimate.objects.filter(tenant=tenant).select_related("cook", "sweet", "roti_price_obj").order_by("-date")

        # Auto recalculate recent estimates to ensure live actuals and costing are updated
        for est in list(qs[:50]):
            est.recalculate()
            est.save()

        # Filtering
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        cook_id = self.request.GET.get("cook")
        search = self.request.GET.get("q")

        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        if cook_id:
            qs = qs.filter(cook_id=cook_id)
        if search:
            qs = qs.filter(dish_name__icontains=search)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        qs = self.get_queryset()

        from django.db.models import Sum
        from decimal import Decimal

        total_tokens = qs.aggregate(t=Sum("actual_tokens_issued"))["t"] or 0
        total_expense = qs.aggregate(t=Sum("total_expense"))["t"] or Decimal("0.00")
        total_token_expense = qs.aggregate(t=Sum("token_expense"))["t"] or Decimal("0.00")
        avg_unit_cost = (total_token_expense / Decimal(total_tokens)).quantize(Decimal("0.01")) if total_tokens > 0 else Decimal("0.00")

        ctx["page_title"] = "Daily Menu Entries & Costing"
        ctx["cooks"] = Cook.objects.filter(tenant=tenant, is_active=True)
        ctx["start_date"] = self.request.GET.get("start_date", "")
        ctx["end_date"] = self.request.GET.get("end_date", "")
        ctx["selected_cook"] = self.request.GET.get("cook", "")
        ctx["search_q"] = self.request.GET.get("q", "")

        ctx["summary_total_tokens"] = total_tokens
        ctx["summary_total_expense"] = total_expense
        ctx["summary_net_expense"] = total_token_expense
        ctx["summary_avg_unit_cost"] = avg_unit_cost
        return ctx


class DailyEstimateCreateView(StaffRequiredMixin, CreateView):
    model = DailyLunchEstimate
    form_class = DailyLunchEstimateForm
    template_name = "menu/daily_estimate_form.html"
    success_url = reverse_lazy("menu:daily_estimate")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        import datetime
        tenant = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        today = datetime.date.today()
        initial["date"] = today.strftime("%Y-%m-%d")

        # Calculate week_of_month (1-5) and day_of_week (0-6)
        w = (today.day - 1) // 7 + 1
        d = today.weekday()

        master_plan = LunchMenuPlan.objects.filter(tenant=tenant, week_of_month=w, day_of_week=d).first()
        if master_plan:
            if master_plan.dish_name:
                initial["dish_name"] = master_plan.dish_name
            if master_plan.cook:
                initial["cook"] = master_plan.cook.pk
            if master_plan.roti_price_obj:
                initial["roti_price_obj"] = master_plan.roti_price_obj.pk
            if master_plan.sweet:
                initial["sweet"] = master_plan.sweet.pk

        return initial

    def form_valid(self, form):
        form.instance.tenant = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        form.instance.created_by = self.request.user
        form.instance.recalculate()
        messages.success(self.request, f"Daily Menu Entry for {form.instance.date} saved successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "Set Daily Menu Entry & Estimate"
        ctx["is_create"] = True
        return ctx


class DailyEstimateUpdateView(StaffRequiredMixin, UpdateView):
    model = DailyLunchEstimate
    form_class = DailyLunchEstimateForm
    template_name = "menu/daily_estimate_form.html"
    success_url = reverse_lazy("menu:daily_estimate")

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        return DailyLunchEstimate.objects.filter(tenant=tenant)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.recalculate()
        obj.save()
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        return kwargs

    def form_valid(self, form):
        form.instance.recalculate()
        messages.success(self.request, f"Daily Menu Entry for {form.instance.date} updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"Edit Daily Menu Entry ({self.object.date})"
        ctx["is_create"] = False
        return ctx


class DailyEstimateToggleLockView(StaffRequiredMixin, View):
    """
    Toggles the Kitchen Control Status (is_locked) for a daily estimate record.
    """
    def post(self, request, pk):
        tenant = getattr(request, "tenant", None) or (request.user.tenant if request.user.is_authenticated else None)
        estimate = get_object_or_404(DailyLunchEstimate, pk=pk, tenant=tenant)
        estimate.is_locked = not estimate.is_locked
        estimate.save()
        status_label = "Locked & Audited" if estimate.is_locked else "Unlocked & Open"
        messages.success(request, f"Daily entry for {estimate.date} Kitchen Control Status is now {status_label}.")
        from django.shortcuts import redirect
        return redirect("menu:daily_estimate")


class DailyEstimateRecalculateView(StaffRequiredMixin, View):
    """
    HTMX / AJAX endpoint to trigger recalculation of issued tokens and rates for a given entry form.
    """
    def post(self, request):
        from decimal import Decimal
        from django.db.models import Sum
        from apps.tokens.models import LunchToken, TokenStatus
        import datetime

        tenant = getattr(request, "tenant", None) or (request.user.tenant if request.user.is_authenticated else None)
        date_str = request.POST.get("date")
        roti_price_id = request.POST.get("roti_price_obj")
        roti_type = request.POST.get("roti_type", RotiType.ROTI)
        sweet_id = request.POST.get("sweet")
        total_expense_str = request.POST.get("total_expense", "0")
        adj_str = request.POST.get("adjustment_amount", "0")

        try:
            target_date = datetime.date.fromisoformat(date_str) if date_str else datetime.date.today()
        except ValueError:
            target_date = datetime.date.today()

        try:
            total_expense = Decimal(total_expense_str)
        except Exception:
            total_expense = Decimal("0.00")

        try:
            adj = Decimal(adj_str)
        except Exception:
            adj = Decimal("0.00")

        tokens = LunchToken.objects.filter(tenant=tenant, date=target_date, status=TokenStatus.ISSUED)
        agg = tokens.aggregate(
            tot_tokens=Sum("token_qty"),
            tot_roti=Sum("extra_roti_qty"),
            tot_sweet=Sum("extra_sweet_qty"),
        )
        actual_tokens = agg["tot_tokens"] or 0
        actual_extra_roti = agg["tot_roti"] or 0
        actual_extra_sweet = agg["tot_sweet"] or 0

        # Roti price
        roti_price = Decimal("0.00")
        if roti_price_id:
            roti_obj = RotiPrice.objects.filter(tenant=tenant, pk=roti_price_id).first()
            if roti_obj:
                roti_price = roti_obj.price

        if roti_price == Decimal("0.00") and roti_type:
            roti_obj = RotiPrice.objects.filter(tenant=tenant, roti_type=roti_type).first()
            if not roti_obj:
                roti_obj = RotiPrice.objects.filter(tenant=tenant, name__icontains=roti_type).first()
            if roti_obj:
                roti_price = roti_obj.price
            elif roti_type == RotiType.ROTI:
                roti_price = Decimal("15.00")
            elif roti_type == RotiType.NAAN:
                roti_price = Decimal("20.00")
            elif roti_type == RotiType.ROGHNI:
                roti_price = Decimal("40.00")

        # Sweet price
        sweet_price = Decimal("0.00")
        if sweet_id:
            sweet = Sweet.objects.filter(tenant=tenant, id=sweet_id).first()
            if sweet:
                sweet_price = sweet.price

        extra_roti_cost = Decimal(actual_extra_roti) * roti_price
        extra_sweet_cost = Decimal(actual_extra_sweet) * sweet_price

        token_expense = total_expense - extra_roti_cost - extra_sweet_cost + adj
        price_per_token = (token_expense / Decimal(actual_tokens)).quantize(Decimal("0.01")) if actual_tokens > 0 else Decimal("0.00")

        return JsonResponse({
            "status": "success",
            "actual_tokens_issued": actual_tokens,
            "actual_extra_roti_issued": actual_extra_roti,
            "roti_unit_price": str(roti_price),
            "actual_extra_sweet_issued": actual_extra_sweet,
            "sweet_unit_price": str(sweet_price),
            "extra_roti_cost": str(extra_roti_cost),
            "extra_sweet_cost": str(extra_sweet_cost),
            "token_expense": str(token_expense),
            "price_per_token": str(price_per_token),
        })


class CostingDashboardView(StaffRequiredMixin, TemplateView):
    """
    Special Premium Dashboard for Lunch Menu Costing & Estimate.
    """
    template_name = "menu/costing_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.utils import timezone
        from django.db.models import Sum, Avg
        from decimal import Decimal

        tenant = getattr(self.request, "tenant", None)
        today = timezone.localdate()
        first_of_month = today.replace(day=1)

        today_entry = DailyLunchEstimate.objects.filter(tenant=tenant, date=today).select_related("cook", "sweet").first()
        recent_entries = DailyLunchEstimate.objects.filter(tenant=tenant).select_related("cook", "sweet").order_by("-date")[:10]
        month_entries = DailyLunchEstimate.objects.filter(tenant=tenant, date__gte=first_of_month)

        tot_month_tokens = month_entries.aggregate(t=Sum("actual_tokens_issued"))["t"] or 0
        tot_month_expense = month_entries.aggregate(t=Sum("total_expense"))["t"] or Decimal("0.00")
        tot_month_token_exp = month_entries.aggregate(t=Sum("token_expense"))["t"] or Decimal("0.00")
        month_avg_cost = (tot_month_token_exp / Decimal(tot_month_tokens)).quantize(Decimal("0.01")) if tot_month_tokens > 0 else Decimal("0.00")

        ctx["page_title"] = "Lunch Costing & Estimate Dashboard"
        ctx["today"] = today
        ctx["today_entry"] = today_entry
        ctx["recent_entries"] = recent_entries
        ctx["tot_month_tokens"] = tot_month_tokens
        ctx["tot_month_expense"] = tot_month_expense
        ctx["tot_month_token_exp"] = tot_month_token_exp
        ctx["month_avg_cost"] = month_avg_cost
        ctx["cooks_count"] = Cook.objects.filter(tenant=tenant, is_active=True).count()
        ctx["sweets_count"] = Sweet.objects.filter(tenant=tenant, is_active=True).count()
        return ctx


class DailyEstimateReportView(LoginRequiredMixin, TemplateView):
    """
    A4 print-optimized summary report for a single daily lunch menu entry.
    """
    template_name = "menu/daily_summary_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        pk = kwargs.get("pk")
        estimate = get_object_or_404(DailyLunchEstimate, pk=pk, tenant=tenant)
        estimate.recalculate()
        estimate.save()

        from decimal import Decimal
        extra_roti_cost = Decimal(estimate.actual_extra_roti_issued) * Decimal(estimate.roti_unit_price or 0)
        extra_sweet_cost = Decimal(estimate.actual_extra_sweet_issued) * Decimal(estimate.sweet_unit_price or 0)
        total_recoveries = extra_roti_cost + extra_sweet_cost
        net_subtotal = max(Decimal("0.00"), Decimal(estimate.total_expense or 0) - total_recoveries)

        token_variance = estimate.actual_tokens_issued - estimate.planned_count
        extra_roti_variance = estimate.actual_extra_roti_issued - estimate.estimated_extra_roti
        extra_sweet_variance = estimate.actual_extra_sweet_issued - estimate.estimated_extra_sweet

        ctx["page_title"] = f"Daily Costing Summary — {estimate.date}"
        ctx["estimate"] = estimate
        ctx["tenant"] = tenant
        ctx["extra_roti_cost"] = extra_roti_cost
        ctx["extra_sweet_cost"] = extra_sweet_cost
        ctx["total_recoveries"] = total_recoveries
        ctx["net_subtotal"] = net_subtotal
        ctx["token_variance"] = token_variance
        ctx["extra_roti_variance"] = extra_roti_variance
        ctx["extra_sweet_variance"] = extra_sweet_variance
        return ctx


class DailyEstimateRangeReportView(LoginRequiredMixin, TemplateView):
    """
    A4 print-optimized summary report for a selected date range with period stats and average unit cost.
    """
    template_name = "menu/daily_range_summary_report.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.db.models import Sum
        from decimal import Decimal

        tenant = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        start_date_str = self.request.GET.get("start_date", "").strip()
        end_date_str = self.request.GET.get("end_date", "").strip()
        cook_id = self.request.GET.get("cook", "").strip()

        qs = DailyLunchEstimate.objects.filter(tenant=tenant).select_related("cook", "sweet", "roti_price_obj").order_by("date")

        for est in qs:
            est.recalculate()
            est.save()

        if start_date_str:
            qs = qs.filter(date__gte=start_date_str)
        if end_date_str:
            qs = qs.filter(date__lte=end_date_str)
        if cook_id:
            qs = qs.filter(cook_id=cook_id)

        first_entry = qs.first()
        last_entry = qs.last()
        display_start = start_date_str if start_date_str else (first_entry.date.strftime("%Y-%m-%d") if first_entry else "All Time")
        display_end = end_date_str if end_date_str else (last_entry.date.strftime("%Y-%m-%d") if last_entry else "Present")

        tot_tokens = qs.aggregate(t=Sum("actual_tokens_issued"))["t"] or 0
        tot_expense = qs.aggregate(t=Sum("total_expense"))["t"] or Decimal("0.00")
        tot_token_exp = qs.aggregate(t=Sum("token_expense"))["t"] or Decimal("0.00")

        tot_extra_roti_qty = qs.aggregate(t=Sum("actual_extra_roti_issued"))["t"] or 0
        tot_extra_sweet_qty = qs.aggregate(t=Sum("actual_extra_sweet_issued"))["t"] or 0

        avg_unit_cost = (tot_token_exp / Decimal(tot_tokens)).quantize(Decimal("0.01")) if tot_tokens > 0 else Decimal("0.00")

        ctx["page_title"] = "Period Costing Summary Report"
        ctx["tenant"] = tenant
        ctx["estimates"] = qs
        ctx["start_date"] = display_start
        ctx["end_date"] = display_end
        ctx["tot_tokens"] = tot_tokens
        ctx["tot_expense"] = tot_expense
        ctx["tot_token_exp"] = tot_token_exp
        ctx["tot_extra_roti_qty"] = tot_extra_roti_qty
        ctx["tot_extra_sweet_qty"] = tot_extra_sweet_qty
        ctx["avg_unit_cost"] = avg_unit_cost
        return ctx


# ── Monthly Menu (Employee-facing) ───────────────────────────────────────────

class MonthlyMenuView(LoginRequiredMixin, TemplateView):
    template_name = "menu/monthly_menu.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        import datetime
        from django.db.models.functions import ExtractMonth, ExtractYear

        tenant = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)
        month_str = self.request.GET.get("month")
        
        if month_str:
            try:
                month = datetime.date.fromisoformat(month_str + "-01")
            except ValueError:
                month = datetime.date.today().replace(day=1)
        else:
            month = datetime.date.today().replace(day=1)

        # Previous and Next Month strings for navigation
        if month.month == 1:
            prev_month = month.replace(year=month.year - 1, month=12)
        else:
            prev_month = month.replace(month=month.month - 1)

        if month.month == 12:
            next_month = month.replace(year=month.year + 1, month=1)
        else:
            next_month = month.replace(month=month.month + 1)

        plans = list(LunchMenuPlan.objects.filter(tenant=tenant).select_related("cook", "roti_price_obj", "sweet").order_by("week_of_month", "day_of_week"))
        
        # Group plans into 5 master weeks
        weeks = {}
        for w in range(1, 6):
            w_plans = [p for p in plans if p.week_of_month == w]
            if w_plans:
                weeks[w] = w_plans

        # Fetch DailyLunchEstimates for this active calendar month
        estimates = list(DailyLunchEstimate.objects.filter(
            tenant=tenant,
            date__year=month.year,
            date__month=month.month
        ).order_by("date"))

        # Check if month's billing entry has been published
        from apps.billing.models import MonthlyBillRun, MonthlyBillRunStatus
        is_month_billed = MonthlyBillRun.objects.filter(
            tenant=tenant,
            period_start__year=month.year,
            period_start__month=month.month,
            status=MonthlyBillRunStatus.PUBLISHED
        ).exists()

        # Smart Interactive Calendar Grid Mapping
        import calendar
        cal = calendar.Calendar(firstweekday=0)  # Starts Monday
        month_weeks = cal.monthdatescalendar(month.year, month.month)
        
        calendar_grid = []
        for week_days in month_weeks:
            grid_week = []
            for d_date in week_days:
                is_this_month = (d_date.month == month.month)
                w_num = min(5, (d_date.day - 1) // 7 + 1)
                d_weekday = d_date.weekday()  # 0=Mon ... 6=Sun
                
                # Match Master Plan
                master_dish = next((p for p in plans if p.week_of_month == w_num and p.day_of_week == d_weekday), None)
                # Match Daily Estimate (if recorded)
                daily_est = next((e for e in estimates if e.date == d_date), None)
                
                show_unit_cost = False
                if daily_est and daily_est.price_per_token > 0:
                    if is_month_billed or daily_est.is_locked:
                        show_unit_cost = True

                grid_week.append({
                    "date": d_date,
                    "day_num": d_date.day,
                    "is_current_month": is_this_month,
                    "is_today": (d_date == datetime.date.today()),
                    "week_num": w_num,
                    "day_weekday": d_weekday,
                    "master_dish": master_dish,
                    "daily_est": daily_est,
                    "show_unit_cost": show_unit_cost,
                })
            calendar_grid.append(grid_week)

        ctx["page_title"] = f"Master Lunch Menu Roster & Calendar — {month.strftime('%B %Y')}"
        ctx["current_month"] = month
        ctx["prev_month_str"] = prev_month.strftime("%Y-%m")
        ctx["next_month_str"] = next_month.strftime("%Y-%m")
        ctx["plans"] = plans
        ctx["estimates"] = estimates
        ctx["weeks"] = weeks
        ctx["calendar_grid"] = calendar_grid
        ctx["is_month_billed"] = is_month_billed
        ctx["total_dishes"] = len(plans)
        ctx["sweets_count"] = sum(1 for p in plans if p.sweet or p.contains_sweet)
        return ctx


# ── Cafeteria Setup & Catalog Management ────────────────────────────────────

class SetupIndexView(StaffRequiredMixin, TemplateView):
    """
    Unified Setup Hub for Cafe Admin to manage Cooks, Sweets with prices, Roti prices, and Dishes catalog.
    """
    template_name = "menu/setup_index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None) or (self.request.user.tenant if self.request.user.is_authenticated else None)

        ctx["page_title"] = "Cafeteria Setup & Catalog Management"

        if tenant:
            default_rotis = [
                ("Standard Roti", "roti", "15.00"),
                ("Tandoori Naan", "naan", "20.00"),
                ("Roghni Naan", "roghni", "40.00"),
                ("Khamiri Roti", "khamiri", "25.00"),
                ("Puri", "puri", "30.00"),
            ]
            for r_name, r_code, default_p in default_rotis:
                if not RotiPrice.objects.filter(tenant=tenant, roti_type=r_code).exists() and not RotiPrice.objects.filter(tenant=tenant, name=r_name).exists():
                    RotiPrice.objects.create(tenant=tenant, name=r_name, roti_type=r_code, price=default_p, is_active=True)

            if not Cook.objects.filter(tenant=tenant).exists():
                Cook.objects.create(tenant=tenant, name="Chef Umer", phone="0300-1112233", is_active=True)
                Cook.objects.create(tenant=tenant, name="Master Rasheed", phone="0301-4445566", is_active=True)

            if not Sweet.objects.filter(tenant=tenant).exists():
                Sweet.objects.create(tenant=tenant, name="Gulab Jamun", price="30.00", is_active=True)
                Sweet.objects.create(tenant=tenant, name="Kheer", price="40.00", is_active=True)

        ctx["cooks"] = Cook.objects.filter(tenant=tenant).order_by("-is_active", "name")
        ctx["sweets"] = Sweet.objects.filter(tenant=tenant).order_by("-is_active", "name")
        ctx["roti_prices"] = RotiPrice.objects.filter(tenant=tenant).order_by("name")
        ctx["active_tab"] = self.request.GET.get("tab", "cooks")
        return ctx


class CookCreateView(StaffRequiredMixin, CreateView):
    model = Cook
    form_class = CookForm
    template_name = "menu/cook_form.html"
    success_url = reverse_lazy("menu:setup_index")

    def form_valid(self, form):
        form.instance.tenant = getattr(self.request, "tenant", None)
        messages.success(self.request, f"Cook '{form.instance.name}' added successfully.")
        return super().form_valid(form)


class CookUpdateView(StaffRequiredMixin, UpdateView):
    model = Cook
    form_class = CookForm
    template_name = "menu/cook_form.html"
    success_url = reverse_lazy("menu:setup_index")

    def get_queryset(self):
        return Cook.objects.filter(tenant=getattr(self.request, "tenant", None))

    def form_valid(self, form):
        messages.success(self.request, f"Cook '{form.instance.name}' updated successfully.")
        return super().form_valid(form)


class CookToggleView(StaffRequiredMixin, View):
    def post(self, request, pk):
        cook = get_object_or_404(Cook, pk=pk, tenant=getattr(request, "tenant", None))
        cook.is_active = not cook.is_active
        cook.save(update_fields=["is_active"])
        messages.success(request, f"Status for '{cook.name}' updated.")
        from django.shortcuts import redirect
        return redirect("menu:setup_index")


class SweetCreateView(StaffRequiredMixin, CreateView):
    model = Sweet
    form_class = SweetForm
    template_name = "menu/sweet_form.html"
    success_url = reverse_lazy("menu:setup_index")

    def form_valid(self, form):
        form.instance.tenant = getattr(self.request, "tenant", None)
        messages.success(self.request, f"Sweet '{form.instance.name}' added at PKR {form.instance.price}.")
        return super().form_valid(form)


class SweetUpdateView(StaffRequiredMixin, UpdateView):
    model = Sweet
    form_class = SweetForm
    template_name = "menu/sweet_form.html"
    success_url = reverse_lazy("menu:setup_index")

    def get_queryset(self):
        return Sweet.objects.filter(tenant=getattr(self.request, "tenant", None))

    def form_valid(self, form):
        messages.success(self.request, f"Sweet '{form.instance.name}' updated successfully.")
        return super().form_valid(form)


class SweetToggleView(StaffRequiredMixin, View):
    def post(self, request, pk):
        sweet = get_object_or_404(Sweet, pk=pk, tenant=getattr(request, "tenant", None))
        sweet.is_active = not sweet.is_active
        sweet.save(update_fields=["is_active"])
        messages.success(request, f"Status for '{sweet.name}' updated.")
        from django.shortcuts import redirect
        return redirect("menu:setup_index")


class RotiPriceCreateView(StaffRequiredMixin, CreateView):
    model = RotiPrice
    form_class = RotiPriceForm
    template_name = "menu/roti_price_form.html"
    success_url = reverse_lazy("menu:setup_index")

    def form_valid(self, form):
        form.instance.tenant = getattr(self.request, "tenant", None)
        messages.success(self.request, f"Roti type '{form.instance.name}' added at PKR {form.instance.price}.")
        return super().form_valid(form)


class RotiPriceUpdateView(StaffRequiredMixin, UpdateView):
    model = RotiPrice
    form_class = RotiPriceForm
    template_name = "menu/roti_price_form.html"
    success_url = reverse_lazy("menu:setup_index")

    def get_queryset(self):
        return RotiPrice.objects.filter(tenant=getattr(self.request, "tenant", None))

    def form_valid(self, form):
        messages.success(self.request, f"Roti price for '{form.instance.name}' set to PKR {form.instance.price}.")
        return super().form_valid(form)


class RotiPriceDeleteView(StaffRequiredMixin, View):
    def post(self, request, pk):
        roti = get_object_or_404(RotiPrice, pk=pk, tenant=getattr(request, "tenant", None))
        name = roti.name
        roti.delete()
        messages.success(request, f"Roti type '{name}' deleted.")
        from django.shortcuts import redirect
        return redirect("menu:setup_index")



