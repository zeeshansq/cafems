"""POS App – Views (Tea/Snack Point of Sale)."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.shortcuts import get_object_or_404
import json
from decimal import Decimal

from apps.core.mixins import StaffRequiredMixin
from apps.menu.models import TeaItem, MenuCategory
from apps.employees.models import Employee
from .models import TeaItemSale, PaymentMethod
from .forms import SaleForm


class POSView(StaffRequiredMixin, TemplateView):
    """
    Main POS screen — fast, keyboard/touch-friendly.
    Items loaded via htmx; cart managed client-side (Alpine.js).
    """
    template_name = "pos/pos.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        ctx["page_title"] = "Tea & Snack POS"
        ctx["categories"] = MenuCategory.objects.filter(tenant=tenant).prefetch_related(
            "items"
        )
        ctx["items"] = TeaItem.objects.filter(tenant=tenant, is_available=True).select_related("category")
        ctx["payment_methods"] = PaymentMethod.choices
        ctx["today"] = timezone.localdate()
        # Today's summary
        employees = Employee.objects.filter(tenant=tenant, is_active=True).select_related("department").order_by("full_name")
        ctx["employees_json"] = [
            {
                "id": emp.pk,
                "full_name": emp.full_name,
                "pno": emp.pno or "N/A",
                "department": emp.department.name if emp.department else "General",
                "designation": emp.designation or "Staff",
                "initials": emp.full_name[:2].upper() if emp.full_name else "EM",
                "photo_url": emp.photo.url if emp.photo else None,
                "membership_status": emp.membership_status,
            }
            for emp in employees
        ]
        return ctx


class POSEmployeeLookupView(StaffRequiredMixin, View):
    """
    Lookup an active Employee by P-Number (PNO), register number, or name.
    Returns JSON employee profile data for display in POS checkout panel.
    """
    def get(self, request):
        tenant = getattr(request, "tenant", None)
        pno = request.GET.get("pno", "").strip()

        if not pno:
            return JsonResponse({"found": False, "error": "Please enter a P-Number"})

        employee = (
            Employee.objects.filter(tenant=tenant, is_active=True)
            .filter(
                Q(pno__iexact=pno)
                | Q(pno__icontains=pno)
                | Q(register_number__iexact=pno)
                | Q(full_name__icontains=pno)
            )
            .select_related("department", "user")
            .first()
        )

        if not employee:
            return JsonResponse({"found": False, "error": f"No active employee found for '{pno}'"})

        name_parts = employee.full_name.split()
        initials = "".join([p[0].upper() for p in name_parts[:2]]) if name_parts else "EM"

        return JsonResponse({
            "found": True,
            "id": employee.id,
            "pno": employee.pno or "N/A",
            "full_name": employee.full_name,
            "email": employee.email or (employee.user.email if employee.user else ""),
            "designation": employee.designation or "Employee",
            "department": employee.department.name if employee.department else "General",
            "category": employee.get_category_display(),
            "membership_type": employee.get_membership_type_display(),
            "membership_status": employee.membership_status,
            "initials": initials,
            "photo_url": employee.photo.url if employee.photo else None,
        })


class POSSubmitView(StaffRequiredMixin, View):
    """
    Handle POS sale submission via htmx/fetch POST.
    Accepts JSON cart items and processes each as a TeaItemSale.
    """
    def post(self, request):
        tenant = getattr(request, "tenant", None)
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        cart_items = data.get("items", [])
        payment_method = data.get("payment_method", PaymentMethod.CASH)
        amount_paid = data.get("amount_paid", 0)
        buyer_id = data.get("buyer_id")
        is_walk_in = not bool(buyer_id)

        if not cart_items:
            return JsonResponse({"error": "Cart is empty"}, status=400)

        buyer = None
        if buyer_id:
            try:
                buyer = Employee.objects.get(pk=buyer_id, tenant=tenant, is_active=True)
            except Employee.DoesNotExist:
                pass

        import uuid
        order_ref = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        today = timezone.localdate()
        created_sales = []
        total = Decimal("0.00")

        for item_data in cart_items:
            try:
                item = TeaItem.objects.get(pk=item_data["id"], tenant=tenant, is_available=True)
            except TeaItem.DoesNotExist:
                continue

            qty = max(1, int(item_data.get("qty", 1)))
            item_total = item.price * qty
            sale = TeaItemSale.objects.create(
                tenant=tenant,
                date=today,
                item=item,
                quantity=qty,
                unit_price=item.price,
                amount_paid=item_total,
                payment_method=payment_method,
                buyer=buyer,
                is_walk_in=is_walk_in,
                issued_by=request.user,
                order_reference=order_ref,
            )
            total += item_total
            created_sales.append({"id": sale.pk, "item": item.name, "qty": qty})

        try:
            amount_paid_dec = Decimal(str(amount_paid or 0))
        except (ValueError, TypeError):
            amount_paid_dec = Decimal("0.00")

        if amount_paid_dec <= 0 or amount_paid_dec < total:
            return JsonResponse({
                "error": f"Checkout restricted: Amount paid (PKR {amount_paid_dec:.2f}) must be greater than or equal to total bill (PKR {total:.2f})."
            }, status=400)

        change = float(amount_paid_dec - total)

        # Update note on created sales to persist Tendered cash and Change
        for sale_dict in created_sales:
            TeaItemSale.objects.filter(pk=sale_dict["id"]).update(
                note=f"Tendered:{amount_paid_dec:.2f}|Change:{change:.2f}"
            )

        receipt_url = f"{reverse_lazy('pos:receipt', kwargs={'order_ref': order_ref})}?paid={amount_paid_dec:.2f}&change={change:.2f}"

        return JsonResponse({
            "status": "ok",
            "order_reference": order_ref,
            "receipt_url": str(receipt_url),
            "sales_count": len(created_sales),
            "total": float(total),
            "amount_paid": float(amount_paid_dec),
            "change": max(0, change),
            "items": created_sales,
            "buyer": buyer.full_name if buyer else "Walk-in Customer",
        })


def get_order_sales_queryset(tenant, order_ref):
    """
    Finds all TeaItemSale instances corresponding to order_ref.
    Supports exact order_reference matching, numeric ID matching, or ORD-XXXXX parsing.
    """
    from django.db.models import Q

    # 1. Direct match on order_reference
    qs = TeaItemSale.objects.filter(tenant=tenant, order_reference=order_ref)
    if qs.exists():
        return qs

    # 2. Extract numeric ID from ORD-00055 -> 55
    raw_num = str(order_ref).replace("ORD-", "").lstrip("0")
    if raw_num.isdigit():
        target_id = int(raw_num)

        # Check if any sale has order_reference matching ORD-00055 or ORD-55
        qs_formatted = TeaItemSale.objects.filter(
            tenant=tenant
        ).filter(
            Q(order_reference=f"ORD-{target_id:05d}") |
            Q(order_reference=f"ORD-{target_id}") |
            Q(order_reference=str(target_id))
        )
        if qs_formatted.exists():
            return qs_formatted

        # Check sale by primary key ID
        target_sale = TeaItemSale.objects.filter(tenant=tenant, pk=target_id).first()
        if target_sale:
            if target_sale.order_reference:
                return TeaItemSale.objects.filter(tenant=tenant, order_reference=target_sale.order_reference)
            else:
                # Group by date, created_at minute, buyer, and is_walk_in
                return TeaItemSale.objects.filter(
                    tenant=tenant,
                    date=target_sale.date,
                    created_at__year=target_sale.created_at.year,
                    created_at__month=target_sale.created_at.month,
                    created_at__day=target_sale.created_at.day,
                    created_at__hour=target_sale.created_at.hour,
                    created_at__minute=target_sale.created_at.minute,
                    buyer=target_sale.buyer,
                    is_walk_in=target_sale.is_walk_in,
                )

    return TeaItemSale.objects.none()


class POSThermalReceiptView(StaffRequiredMixin, TemplateView):
    """Compact 80mm thermal receipt printer template (opens in new tab)."""
    template_name = "pos/thermal_receipt.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        order_ref = self.kwargs.get("order_ref")

        sales = get_order_sales_queryset(tenant, order_ref).select_related("item", "buyer", "issued_by")
        first_sale = sales.first()
        total_amt = sum(s.quantity * s.unit_price for s in sales) if sales else Decimal("0.00")
        total_qty = sum(s.quantity for s in sales) if sales else 0

        change_return = Decimal("0.00")
        amount_tendered = total_amt

        # 1. Try URL parameters first
        paid_param = self.request.GET.get("paid")
        change_param = self.request.GET.get("change")
        if change_param is not None:
            try:
                change_return = Decimal(str(change_param))
                if paid_param:
                    amount_tendered = Decimal(str(paid_param))
            except (ValueError, TypeError):
                pass
        elif first_sale and first_sale.note and "Change:" in first_sale.note:
            try:
                parts = dict(p.split(":") for p in first_sale.note.split("|") if ":" in p)
                if "Change" in parts:
                    change_return = Decimal(parts["Change"])
                if "Tendered" in parts:
                    amount_tendered = Decimal(parts["Tendered"])
            except Exception:
                pass

        ctx["page_title"] = f"Thermal Receipt – {order_ref}"
        ctx["order_ref"] = order_ref
        ctx["sales"] = sales
        ctx["first_sale"] = first_sale
        ctx["total_amount"] = total_amt
        ctx["total_qty"] = total_qty
        ctx["amount_tendered"] = amount_tendered
        ctx["change_return"] = change_return
        return ctx


class POSEditOrderView(StaffRequiredMixin, TemplateView):
    """Edit or update a previous POS checkout issuance order."""
    template_name = "pos/edit_order.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        order_ref = self.kwargs.get("order_ref")

        sales = get_order_sales_queryset(tenant, order_ref).select_related("item", "buyer")
        first_sale = sales.first()

        ctx["page_title"] = f"Edit POS Order – {order_ref}"
        ctx["order_ref"] = order_ref
        ctx["sales"] = sales
        ctx["first_sale"] = first_sale
        ctx["all_items"] = TeaItem.objects.filter(tenant=tenant, is_available=True)
        ctx["employees"] = Employee.objects.filter(tenant=tenant, is_active=True)
        return ctx

    def post(self, request, *args, **kwargs):
        tenant = getattr(request, "tenant", None)
        order_ref = self.kwargs.get("order_ref")

        sales = get_order_sales_queryset(tenant, order_ref)
        if not sales.exists():
            messages.error(request, f"Order '{order_ref}' not found.")
            return redirect("pos:daily_summary")

        buyer_id = request.POST.get("buyer_id")
        buyer = None
        is_walk_in = True
        if buyer_id:
            try:
                buyer = Employee.objects.get(pk=buyer_id, tenant=tenant)
                is_walk_in = False
            except Employee.DoesNotExist:
                pass

        updated_count = 0
        for sale in sales:
            qty_key = f"qty_{sale.pk}"
            if qty_key in request.POST:
                try:
                    new_qty = int(request.POST.get(qty_key, 0))
                    if new_qty <= 0:
                        sale.delete()
                    else:
                        sale.quantity = new_qty
                        sale.amount_paid = sale.unit_price * new_qty
                        sale.buyer = buyer
                        sale.is_walk_in = is_walk_in
                        sale.save()
                        updated_count += 1
                except ValueError:
                    pass

        add_item_id = request.POST.get("add_item_id")
        add_qty_str = request.POST.get("add_item_qty", "1")
        if add_item_id:
            try:
                item = TeaItem.objects.get(pk=add_item_id, tenant=tenant)
                add_qty = max(1, int(add_qty_str))
                first_s = sales.first()
                target_date = first_s.date if first_s else timezone.localdate()
                TeaItemSale.objects.create(
                    tenant=tenant,
                    date=target_date,
                    item=item,
                    quantity=add_qty,
                    unit_price=item.price,
                    amount_paid=item.price * add_qty,
                    payment_method=PaymentMethod.CASH,
                    buyer=buyer,
                    is_walk_in=is_walk_in,
                    issued_by=request.user,
                    order_reference=order_ref,
                )
                updated_count += 1
            except Exception as e:
                messages.warning(request, f"Could not add item: {e}")

        from apps.employees.models import AuditLog
        AuditLog.objects.create(
            tenant=tenant,
            actor=request.user,
            action="update_pos_order",
            model_name="TeaItemSale",
            object_id=order_ref,
            before_data={"order_ref": order_ref},
            after_data={"order_ref": order_ref, "updated_count": updated_count},
        )

        messages.success(request, f"POS Order '{order_ref}' updated successfully.")
        return redirect("pos:daily_summary")


class POSItemSearchView(StaffRequiredMixin, View):
    """htmx-powered item search — returns HTML partial."""
    def get(self, request):
        tenant = getattr(request, "tenant", None)
        q = request.GET.get("q", "").strip()
        category_id = request.GET.get("category")

        qs = TeaItem.objects.filter(tenant=tenant, is_available=True)
        if q:
            qs = qs.filter(name__icontains=q)
        if category_id:
            qs = qs.filter(category_id=category_id)

        from django.template.loader import render_to_string
        html = render_to_string("pos/partials/item_grid.html", {
            "items": qs.order_by("sort_order", "name"),
        }, request=request)
        return JsonResponse({"html": html})


class POSDailySummaryView(StaffRequiredMixin, TemplateView):
    """End-of-day summary report and transaction breakdown for POS (Cash Sales)."""
    template_name = "pos/daily_summary.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = getattr(self.request, "tenant", None)
        date_str = self.request.GET.get("date")

        import datetime
        try:
            date = datetime.date.fromisoformat(date_str) if date_str else timezone.localdate()
        except ValueError:
            date = timezone.localdate()

        from django.core.paginator import Paginator

        base_sales = TeaItemSale.objects.filter(tenant=tenant, date=date).select_related("item", "buyer", "issued_by")

        # Overall Unfiltered Day Stats (Cash Only Operations)
        total_revenue = base_sales.aggregate(t=Sum("amount_paid"))["t"] or Decimal("0.00")
        total_transactions = base_sales.count()
        total_items_sold = base_sales.aggregate(q=Sum("quantity"))["q"] or 0

        # Filters on Sales List
        qs = base_sales.order_by("-created_at")

        q = self.request.GET.get("q", "").strip()
        walkin = self.request.GET.get("is_walk_in", "").strip()

        if q:
            qs = qs.filter(
                Q(item__name__icontains=q) |
                Q(buyer__full_name__icontains=q) |
                Q(buyer__pno__icontains=q)
            )
        if walkin != "":
            if walkin == "true":
                qs = qs.filter(is_walk_in=True)
            elif walkin == "false":
                qs = qs.filter(is_walk_in=False)

        # Group individual sale items into Single Checkout Orders
        order_dict = {}
        for sale in qs:
            if sale.order_reference:
                key = sale.order_reference
            else:
                ts_str = sale.created_at.strftime("%Y%m%d%H%M") if sale.created_at else str(sale.id)
                b_str = str(sale.buyer_id) if sale.buyer_id else f"walkin-{sale.id}"
                key = f"{ts_str}-{b_str}"

            if key not in order_dict:
                order_dict[key] = {
                    "order_ref": sale.order_reference or f"ORD-{sale.id:05d}",
                    "created_at": sale.created_at,
                    "buyer": sale.buyer,
                    "is_walk_in": sale.is_walk_in,
                    "issued_by": sale.issued_by,
                    "items": [],
                    "total_qty": 0,
                    "total_amount": Decimal("0.00"),
                }

            order_dict[key]["items"].append(sale)
            order_dict[key]["total_qty"] += sale.quantity
            order_dict[key]["total_amount"] += sale.amount_paid

        order_list = list(order_dict.values())

        # Top Selling Items Aggregation
        by_item = base_sales.values("item__name").annotate(
            qty=Sum("quantity"), total=Sum("amount_paid")
        ).order_by("-total")

        # Pagination (20 orders per page)
        paginator = Paginator(order_list, 20)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        ctx["page_title"] = f"POS Daily Summary – {date.strftime('%B %d, %Y')}"
        ctx["date"] = date
        ctx["orders"] = page_obj.object_list
        ctx["page_obj"] = page_obj
        ctx["paginator"] = paginator
        ctx["is_paginated"] = page_obj.has_other_pages()

        ctx["total_revenue"] = total_revenue
        ctx["total_transactions"] = len(order_list)
        ctx["total_items_sold"] = total_items_sold
        ctx["filtered_count"] = len(order_list)
        ctx["by_item"] = by_item

        ctx["current_q"] = q
        ctx["current_walkin"] = walkin
        return ctx
