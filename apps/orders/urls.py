from django.urls import path

from apps.orders.web.views import (
    OrderCreateView,
    OrderSuccessView,
    OrderListView,
    OrderFreteView,
)

app_name = "orders"

urlpatterns = [
    path("", OrderCreateView.as_view(), name="order-create"),
    path("success/<int:pk>/", OrderSuccessView.as_view(), name="order-success"),
    path("list/", OrderListView.as_view(), name="order-list"),
    path("frete/", OrderFreteView.as_view(), name="order-frete"),
]
