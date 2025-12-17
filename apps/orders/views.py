from datetime import datetime, timedelta

from django.shortcuts import render
from django.views import View
from django.views.generic import ListView
from django.db.models import Prefetch

from apps.orders.models import Order
from apps.orders.services import (
    create_order,
    list_orders,
    calcular_frete,
    get_order,
    get_latest_payment_link,
)
from apps.sellers.services import list_sellers
from apps.payments.models import PaymentLink



class OrderCreateView(View):

    def get(self, request):
        return render(
            request,
            'orders/order.html',
            {
                'sellers': list_sellers(),
                'orders': list_orders(),
            }
        )

    def post(self, request):
        order = create_order(request.POST.dict())
        payment_link = get_latest_payment_link(order)

        return render(
            request,
            'orders/order_success.html',
            {
                'order': order,
                'payment_link': payment_link,
            }
        )

class OrderSuccessView(View):

    def get(self, request, pk):
        order = get_order(pk)
        payment_link = get_latest_payment_link(order)

        if not payment_link:
            return render(
                request,
                'orders/order_success.html',
                {
                    'order': order,
                    'payment_link': None,
                }
            )

        payment = getattr(payment_link, 'payment', None)

        if payment and payment.status == 'paid':
            return render(
                request,
                'orders/order_recibo.html',
                {
                    'order': order,
                    'payment': payment,
                    'payment_link': payment_link,
                }
            )

        match payment_link.status:
            case 'expired' | 'canceled':
                template = 'orders/payment_link_status.html'
            case _:
                template = 'orders/order_success.html'

        return render(
            request,
            template,
            {
                'order': order,
                'payment_link': payment_link,
            }
        )


class OrderListView(ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        payment_links_qs = PaymentLink.objects.select_related('payment')

        prefetch_links = Prefetch(
            'payment_links',
            queryset=payment_links_qs,
            to_attr='prefetched_payment_links'
        )

        queryset = (
            Order.objects
            .select_related('seller')
            .prefetch_related(prefetch_links)
            .order_by('-created_at')
        )

        seller_id = self.request.GET.get('seller')
        date_start = self.request.GET.get('date_start')
        date_end = self.request.GET.get('date_end')

        if seller_id and seller_id.isdigit():
            queryset = queryset.filter(seller_id=seller_id)

        if date_start:
            try:
                queryset = queryset.filter(
                    created_at__gte=datetime.strptime(date_start, '%Y-%m-%d')
                )
            except ValueError:
                pass

        if date_end:
            try:
                queryset = queryset.filter(
                    created_at__lt=datetime.strptime(date_end, '%Y-%m-%d') + timedelta(days=1)
                )
            except ValueError:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['sellers'] = list_sellers()

        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context['query_params'] = query_params.urlencode()

        return context


class OrderFreteView(View):

    def get(self, request):
        return render(request, 'orders/order_frete.html')

    def post(self, request):
        try:
            data = {
                'cep_destino': request.POST.get('cep', '').replace('-', ''),
                'peso': float(request.POST.get('weight')) * 1000,
                'comprimento': int(request.POST.get('length')),
                'largura': int(request.POST.get('width')),
                'altura': int(request.POST.get('height')),
            }

            freight = calcular_frete(**data)

            return render(
                request,
                'orders/order_frete.html',
                {'freight': freight}
            )

        except (TypeError, ValueError):
            return render(
                request,
                'orders/order_frete.html',
                {'error': 'Preencha todos os campos corretamente.'}
            )
