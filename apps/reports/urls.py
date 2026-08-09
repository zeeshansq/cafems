from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    # Admin / Staff Analytical Reports
    path("", views.ReportsIndexView.as_view(), name="index"),
    path("export/", views.ExportReportCSVView.as_view(), name="export_csv"),
    path("tokens/monthly/", views.MonthlyTokenReportView.as_view(), name="monthly_tokens"),
    path("pos/collection/", views.POSCollectionReportView.as_view(), name="pos_collection"),
    path("employees/issuance/", views.EmployeeIssuanceReportView.as_view(), name="employee_issuance"),
    path("employees/deposits/", views.EmployeeDepositsReportView.as_view(), name="employee_deposits"),
    path("requests/issuance/", views.IssuanceRequestsReportView.as_view(), name="issuance_requests"),
    path("requests/closure/", views.ClosureRequestsReportView.as_view(), name="closure_requests"),
    path("billing/", views.BillingReportView.as_view(), name="billing"),

    # Member Authorized Reports
    path("my/", views.MyReportsIndexView.as_view(), name="my_reports_index"),
    path("my/tokens/", views.MyTokenReportView.as_view(), name="my_token_report"),
    path("my/pos/", views.MyPOSReportView.as_view(), name="my_pos_report"),
    path("my/billing/", views.MyBillingReportView.as_view(), name="my_billing_report"),
    path("my/requests/", views.MyRequestsReportView.as_view(), name="my_requests_report"),
]
