from django.urls import path
from . import views

app_name = "tokens"

urlpatterns = [
    path("issue/", views.TokenIssueView.as_view(), name="issue"),
    path("estimate-counter/", views.EstimateCounterView.as_view(), name="estimate_counter"),
    path("recent-activity/", views.RecentActivityView.as_view(), name="recent_activity"),
    path("daily-report/", views.DailyClosingReportView.as_view(), name="daily_report"),
    path("charge/<int:employee_id>/", views.ChargeTokenView.as_view(), name="charge_token"),
    path("receipt/<int:pk>/", views.LunchTokenReceiptView.as_view(), name="token_receipt"),
    path("history/", views.EmployeeTokenHistoryView.as_view(), name="employee_history"),
]
