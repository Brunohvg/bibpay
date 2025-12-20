from django.urls import path
from .views import OrderListCreateAPIView, OrderDetailAPIView

app_name = "orders_api_v1"

urlpatterns = [
    path("", OrderListCreateAPIView.as_view(), name="order-list-create"),
    path("<int:pk>/", OrderDetailAPIView.as_view(), name="order-detail"),
]
