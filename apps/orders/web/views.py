from django.shortcuts import render
from django.views import View
from django.views.generic import ListView

from apps.orders.services.order_service import (
    create_order,
    get_order,
    get_latest_payment_link,
)
from apps.orders.services.order_query_service import list_orders_filtered
from apps.orders.services.freight_service import calcular_frete_from_request
from apps.sellers.services import list_sellers


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

        return render(
            request,
            "orders/order_success.html",
            {
                "order": order,
                "payment_link": payment_link,
            }
        )


class OrderSuccessView(View):

    def get(self, request, pk):
        order = get_order(pk)
        payment_link = get_latest_payment_link(order)

        if not payment_link:
            template = "orders/order_success.html"
        elif getattr(payment_link.payment, "status", None) == "paid":
            template = "orders/order_recibo.html"
        elif payment_link.status in {"expired", "canceled"}:
            template = "orders/payment_link_status.html"
        else:
            template = "orders/order_success.html"

        return render(
            request,
            template,
            {
                "order": order,
                "payment": getattr(payment_link, "payment", None),
                "payment_link": payment_link,
            }
        )


class OrderListView(ListView):
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return list_orders_filtered(self.request.GET)

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
