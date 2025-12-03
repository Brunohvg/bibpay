from django.shortcuts import render
from django.views import View
from apps.orders.services import create_order, list_orders
from apps.sellers.services import list_sellers


class OrderCreateView(View):
    def get(self, request):
        sellers = list_sellers()
        orders = list_orders()
        return render(request, 'orders/order.html', {'sellers': sellers, 'orders': orders})

    def post(self, request):
        order_data = request.POST
        # pegar os dados e montar um dicionario 
        order = create_order(order_data)
        return render(request, 'orders/dashboard.html', {'order': order})


