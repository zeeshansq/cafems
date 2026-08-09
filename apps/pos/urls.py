from django.urls import path
from . import views

app_name = "pos"

urlpatterns = [
    path("", views.POSView.as_view(), name="index"),
    path("submit/", views.POSSubmitView.as_view(), name="submit"),
    path("employee-lookup/", views.POSEmployeeLookupView.as_view(), name="employee_lookup"),
    path("search/", views.POSItemSearchView.as_view(), name="item_search"),
    path("summary/", views.POSDailySummaryView.as_view(), name="daily_summary"),
    path("receipt/<str:order_ref>/", views.POSThermalReceiptView.as_view(), name="receipt"),
    path("order/<str:order_ref>/edit/", views.POSEditOrderView.as_view(), name="edit_order"),
]
