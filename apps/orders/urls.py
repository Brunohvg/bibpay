from django.urls import path
from apps.orders.views import OrderCreateView

app_name = 'orders'

urlpatterns = [
    path('', OrderCreateView.as_view(), name='order-create'),
]
