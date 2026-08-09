from django.urls import path
from . import views

app_name = "menu"

urlpatterns = [
    path("", views.MenuIndexView.as_view(), name="index"),
    path("items/new/", views.TeaItemCreateView.as_view(), name="item_create"),
    path("items/<int:pk>/edit/", views.TeaItemUpdateView.as_view(), name="item_update"),
    path("items/<int:pk>/toggle/", views.TeaItemToggleView.as_view(), name="item_toggle"),
    path("lunch-plan/", views.LunchPlanView.as_view(), name="lunch_plan"),
    path("lunch-plan/new/", views.LunchPlanCreateView.as_view(), name="lunch_plan_create"),
    path("lunch-plan/<int:pk>/edit/", views.LunchPlanUpdateView.as_view(), name="lunch_plan_update"),
    path("lunch-plan/<int:pk>/delete/", views.LunchPlanDeleteView.as_view(), name="lunch_plan_delete"),
    path("costing-dashboard/", views.CostingDashboardView.as_view(), name="costing_dashboard"),
    path("daily-estimate/", views.DailyEstimateView.as_view(), name="daily_estimate"),
    path("daily-estimate/new/", views.DailyEstimateCreateView.as_view(), name="daily_estimate_create"),
    path("daily-estimate/<int:pk>/edit/", views.DailyEstimateUpdateView.as_view(), name="daily_estimate_update"),
    path("daily-estimate/<int:pk>/lock/", views.DailyEstimateToggleLockView.as_view(), name="daily_estimate_toggle_lock"),
    path("daily-estimate/recalculate/", views.DailyEstimateRecalculateView.as_view(), name="daily_estimate_recalculate"),
    path("daily-estimate/<int:pk>/report/", views.DailyEstimateReportView.as_view(), name="daily_estimate_report"),
    path("daily-estimate/range-report/", views.DailyEstimateRangeReportView.as_view(), name="daily_estimate_range_report"),
    path("monthly/", views.MonthlyMenuView.as_view(), name="monthly"),
    # Setup Hub Routes
    path("setup/", views.SetupIndexView.as_view(), name="setup_index"),
    path("setup/cooks/new/", views.CookCreateView.as_view(), name="cook_create"),
    path("setup/cooks/<int:pk>/edit/", views.CookUpdateView.as_view(), name="cook_update"),
    path("setup/cooks/<int:pk>/toggle/", views.CookToggleView.as_view(), name="cook_toggle"),
    path("setup/sweets/new/", views.SweetCreateView.as_view(), name="sweet_create"),
    path("setup/sweets/<int:pk>/edit/", views.SweetUpdateView.as_view(), name="sweet_update"),
    path("setup/sweets/<int:pk>/toggle/", views.SweetToggleView.as_view(), name="sweet_toggle"),
    path("setup/roti/new/", views.RotiPriceCreateView.as_view(), name="roti_price_create"),
    path("setup/roti/<int:pk>/edit/", views.RotiPriceUpdateView.as_view(), name="roti_price_update"),
    path("setup/roti/<int:pk>/delete/", views.RotiPriceDeleteView.as_view(), name="roti_price_delete"),
]

