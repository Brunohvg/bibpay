from django.shortcuts import render
from django.views import View
from apps.orders.services import create_order, list_orders


class DashboardHomeView(View):
    def get(self, request, *args, **kwargs):
        orders = list_orders()
        return render(request, 'dashboard/dashboard.html', {'orders': orders})
