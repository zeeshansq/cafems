"""POS Admin."""
from django.contrib import admin
from .models import TeaItemSale


@admin.register(TeaItemSale)
class TeaItemSaleAdmin(admin.ModelAdmin):
    list_display = ["date", "item", "quantity", "unit_price", "amount_paid", "payment_method", "buyer", "is_walk_in", "tenant"]
    list_filter = ["date", "payment_method", "is_walk_in", "tenant"]
    search_fields = ["item__name", "buyer__full_name"]
