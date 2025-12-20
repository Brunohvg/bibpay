from django.shortcuts import get_object_or_404

from apps.orders.models import Order
from apps.orders.domain.order import build_order
from apps.orders.utils import formatar_valor
from apps.sellers.services.queries import get_seller


def create_order(data: dict) -> Order:
    order_data = build_order(
        name=data.get("cliente_nome"),
        value=formatar_valor(data.get("valor_produto", "0")),
        freight=formatar_valor(data.get("valor_frete", "0")),
        installments=int(data.get("parcelas", 1)),
        seller=get_seller(seller_id=data.get("vendedor")),
    )

    return Order.objects.create(**order_data)


def update_order(order_id: int, data: dict) -> Order:
    order = get_object_or_404(Order, id=order_id)

    allowed_fields = {
        "name",
        "value",
        "value_freight",
        "status",
        "installments",
        "seller",
    }

    for field, value in data.items():
        if field in allowed_fields:
            setattr(order, field, value)

    order.save()
    return order


def delete_order(order_id: int) -> bool:
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return True


def get_order(pk: int) -> Order:
    return get_object_or_404(Order, pk=pk)


def get_latest_payment_link(order):
    return order.payment_links.order_by("-created_at").first()
