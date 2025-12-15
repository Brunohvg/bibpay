from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.db.models import Q, Prefetch # Adicionado Prefetch
from apps.orders.models import Order
from apps.orders.services import create_order, list_orders
from apps.sellers.services import list_sellers
from apps.payments.models import Payment, PaymentLink


class OrderCreateView(View):
    """
    View para exibir o formulário de criação de pedidos (GET) 
    e processar a criação do pedido e do link de pagamento (POST).
    """
    def get(self, request):
        """Exibe a página de criação de pedido com a lista de vendedores."""
        sellers = list_sellers()
        orders = list_orders()
        return render(
            request,
            'orders/order.html',
            {
                'sellers': sellers,
                'orders': orders,
            }
        )

    def post(self, request):
        """Cria o pedido e gera o link de pagamento, redirecionando para a página de sucesso."""
        order = create_order(request.POST.dict())

        # Busca o PaymentLink mais recente
        payment_link = (
            order.payment_links
            .order_by('-created_at')
            .first()
        )

        return render(
            request,
            'orders/order_success.html',
            {
                'order': order,
                'payment_link': payment_link,
            }
        )


class OrderSuccessView(View):
    """
    Exibe o status do link de pagamento após a criação do pedido.
    Verifica o status do Payment real para decidir se exibe o recibo ou a página de sucesso.
    """
    def get(self, request, pk):
        """
        Busca o pedido, o link de pagamento principal e o pagamento associado.
        Decide qual template renderizar (recibo ou sucesso).
        """
        order = get_object_or_404(Order, pk=pk)

        # Buscar o link de pagamento mais recente/principal (o que tem o Payment)
        payment_link = (
            order.payment_links
            .order_by('-created_at')
            .first()
        )

        # Acessa o Payment via related_name='payment' (OneToOneField)
        payment = getattr(payment_link, 'payment', None) 
        
        if payment and payment.status == 'paid':
            print("Pagamento confirmado")
            return render(
                request,
                'orders/order_recibo.html',
                {
                    'order': order,
                    'payment': payment,
                    'payment_link': payment_link,
                }
            )

        print("Pagamento não confirmado")
        return render(
            request,
            'orders/order_success.html',
            {
                'order': order,
                'payment_link': payment_link,
            }
        )


class OrderListView(ListView):
    """
    View que exibe uma lista paginada de pedidos com opções de filtro 
    por vendedor e período de criação. Usa Prefetch para otimizar o acesso 
    ao link de pagamento e status.
    """
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10 # Limite de 10 exibições por página

    def get_queryset(self):
        
        # 1. Preparação do Prefetch para buscar o PaymentLink e o Payment dele (eficiente)
        # Assumindo que PaymentLink.payment é o OneToOneField
        payment_link_queryset = PaymentLink.objects.all().select_related('payment')
        
        prefetch_links = Prefetch(
            'payment_links', 
            queryset=payment_link_queryset,
            to_attr='prefetched_payment_links'
        )

        # 2. Query Principal: Traz Orders e Seller, e executa o Prefetch
        queryset = (
            Order.objects.all()
            .select_related('seller')
            .prefetch_related(prefetch_links) # Adiciona a consulta otimizada
            .order_by('-created_at')
        )
        
        # --- Lógica de Filtros ---
        seller_id = self.request.GET.get('seller')
        date_start_str = self.request.GET.get('date_start')
        date_end_str = self.request.GET.get('date_end')

        if seller_id:
            try:
                queryset = queryset.filter(seller_id=int(seller_id))
            except ValueError:
                pass

        if date_start_str:
            try:
                date_start = datetime.strptime(date_start_str, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=date_start)
            except ValueError:
                pass

        if date_end_str:
            try:
                date_end = datetime.strptime(date_end_str, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=date_end)
            except ValueError:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        """Adiciona a lista de vendedores e os parâmetros GET para a paginação."""
        context = super().get_context_data(**kwargs)
        
        context['sellers'] = list_sellers()
        
        # Prepara os parâmetros GET para serem usados na Paginação (sem o 'page')
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        
        context['query_params'] = query_params.urlencode()

        return context