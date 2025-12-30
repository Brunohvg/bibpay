from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import ListView

from apps.orders.services.commands import (
    create_order,
    get_order,
    get_latest_payment_link,
)
from apps.orders.services.queries import list_orders_filtered
from apps.orders.services.freight_calculator import calcular_frete_from_request
from apps.sellers.services.queries import list_sellers


def post_redirect_get(request, payment_link, order):
    """Helper para implementar POST-Redirect-GET no formulário de pedido"""
    return redirect("orders:order-success", pk=order.pk)


class OrderCreateView(View):

    def get(self, request):
        return render(
            request,
            "orders/order.html",
            {
                "sellers": list_sellers(),
            }
        )

    def post(self, request):
        order = create_order(request.POST.dict())
        payment_link = get_latest_payment_link(order)
        return redirect("orders:order-success", pk=order.pk)


class OrderSuccessView(View):

    def get(self, request, pk):
        order = get_order(pk)
        payment_link = get_latest_payment_link(order)

        payment = None
        template = "orders/order_success.html"

        if payment_link:
            payment = getattr(payment_link, "payment", None)

            if payment and payment.status == "paid":
                template = "orders/order_recibo.html"

            elif payment_link.status in {"expired", "canceled"}:
                template = "orders/payment_link_status.html"

        return render(
            request,
            template,
            {
                "order": order,
                "payment": payment,
                "payment_link": payment_link,
            }
        )

class OrderListView(LoginRequiredMixin, ListView):
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        # Captura os parâmetros originais
        filters = self.request.GET.copy()
        
        # Se não for admin, FORÇA o filtro pelo próprio vendedor
        if not self.request.user.is_superuser:
            if hasattr(self.request.user, 'seller_profile'):
                filters['seller'] = str(self.request.user.seller_profile.id)
            else:
                # Se não é seller nem admin, não vê nada (ou tratar diferente)
                return []
                
        return list_orders_filtered(filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sellers"] = list_sellers()
        return context


class OrderFreteView(View):

    def get(self, request):
        return render(request, "orders/order_frete.html")

    def post(self, request):
        try:
            freight = calcular_frete_from_request(request.POST)
            return render(request, "orders/order_frete.html", {"freight": freight})
        except Exception:
            return render(
                request,
                "orders/order_frete.html",
                {"error": "Preencha todos os campos corretamente."},
            )