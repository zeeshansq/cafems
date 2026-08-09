"""Menu Admin."""
from django.contrib import admin
from .models import (
    MenuCategory, TeaItem, LunchMenuPlan, DailyLunchEstimate,
    Cook, Sweet, RotiPrice
)


@admin.register(Cook)
class CookAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "is_active", "tenant"]
    list_filter = ["is_active", "tenant"]
    search_fields = ["name"]


@admin.register(Sweet)
class SweetAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "is_active", "tenant"]
    list_filter = ["is_active", "tenant"]
    search_fields = ["name"]


@admin.register(RotiPrice)
class RotiPriceAdmin(admin.ModelAdmin):
    list_display = ["roti_type", "price", "tenant"]
    list_filter = ["tenant"]


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "sort_order", "tenant"]


@admin.register(TeaItem)
class TeaItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "is_available", "tenant"]
    list_filter = ["is_available", "category", "tenant"]
    search_fields = ["name"]


@admin.register(LunchMenuPlan)
class LunchMenuPlanAdmin(admin.ModelAdmin):
    list_display = ["month", "week_of_month", "day_of_week", "dish_name", "contains_sweet", "is_published", "tenant"]
    list_filter = ["month", "is_published", "contains_sweet", "tenant"]


@admin.register(DailyLunchEstimate)
class DailyLunchEstimateAdmin(admin.ModelAdmin):
    list_display = [
        "date", "dish_name", "cook", "roti_type", "sweet",
        "planned_count", "actual_tokens_issued",
        "total_expense", "token_expense", "price_per_token", "tenant"
    ]
    list_filter = ["date", "roti_type", "cook", "tenant"]
    search_fields = ["dish_name"]

