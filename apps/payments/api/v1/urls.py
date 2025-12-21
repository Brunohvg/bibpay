from django.urls import path
from .views import WebhookAPIView

app_name = "payments_api_v1"

urlpatterns = [
    path("hook/", WebhookAPIView.as_view(), name="webhook"),
]
