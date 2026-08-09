from django.urls import path
from . import views

app_name = "requests_app"

urlpatterns = [
    # Staff views
    path("", views.RequestListView.as_view(), name="list"),
    path("<int:pk>/", views.RequestDetailView.as_view(), name="detail"),
    path("<int:pk>/acknowledge/", views.RequestAcknowledgeView.as_view(), name="acknowledge"),
    path("<int:pk>/reject/", views.RequestRejectView.as_view(), name="reject"),
    # Employee self-service
    path("my/", views.MyRequestListView.as_view(), name="my_requests"),
    path("my/new/", views.MyRequestCreateView.as_view(), name="my_request_create"),
    path("my/<int:pk>/cancel/", views.MyRequestCancelView.as_view(), name="my_request_cancel"),
]
