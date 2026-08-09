from django.urls import path
from . import views

app_name = "billing"

urlpatterns = [
    # Admin/Staff
    path("", views.BillListView.as_view(), name="list"),
    path("<int:pk>/", views.BillDetailView.as_view(), name="detail"),
    path("generate/", views.GenerateBillsView.as_view(), name="generate"),
    path("run/<int:pk>/publish/", views.PublishBillRunView.as_view(), name="publish_run"),
    path("report/<str:month_str>/", views.BillRunReportView.as_view(), name="run_report"),
    path("report/<str:month_str>/print/", views.BillRunPrintView.as_view(), name="run_print"),
    path("<int:pk>/payment/", views.RecordPaymentView.as_view(), name="record_payment"),
    path("misc-charge/", views.AddMiscChargeView.as_view(), name="add_misc_charge"),
    # Employee
    path("my/", views.MyBillsView.as_view(), name="my_bills"),
    path("my/<int:pk>/", views.MyBillDetailView.as_view(), name="my_bill_detail"),
]
