from django.shortcuts import render
from django.views.generic import View, UpdateView, ListView
from apps.orders.models import Order
from apps.orders.services import create_order, list_orders
from apps.sellers.services import list_sellers
from apps.payments.services import list_active_payment_links, calculate_total_from_links, list_payments
class OrderCreateView(View):
    def get(self, request):
        sellers = list_sellers()
        orders = list_orders()
        return render(request, 'orders/order.html', {'sellers': sellers, 'orders': orders})

    def post(self, request):
        order = create_order(request.POST.dict())  # transforma em dict normal
        payment_link = order.payment_links.first()  # pega o primeiro link (ou None)

        return render(request, 'orders/order_success.html', {'order': order, 'payment_link': payment_link,})
"""
class OrderListView(ListView):
    model = Order
    template_name = 'orders/dashboard.html'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders'] = list_payments()
        context['total_received'] = calculate_total_from_links(context['orders'])
        return context"""