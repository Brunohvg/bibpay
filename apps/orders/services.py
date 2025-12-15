from django.shortcuts import get_object_or_404
from apps.orders.models import Order
from apps.orders.utils import formatar_valor
from apps.sellers.services import get_seller
from apps.core.integrations.pagarme import PagarMePaymentLink
from apps.core.integrations.sgpweb import CorreiosAPI   



def create_order(data):
    try:
        order_data = {
            "name": data.get("cliente_nome", "").strip(),
            "value": formatar_valor(data.get("valor_produto", "0")),
            "value_freight": formatar_valor(data.get("valor_frete", "0")),
            "status": "pending",
            "installments": int(data.get("parcelas", 1)),
            "seller": get_seller(seller_id=data.get("vendedor")),
        }
    except Exception as e:
        raise ValueError(f"Erro ao criar pedido: {e}")

    return Order.objects.create(**order_data)


# Atualizar um pedido
def update_order(order_id, data):
    order = get_object_or_404(Order, id=order_id)

    for field, value in data.items():
        setattr(order, field, value)

    order.save()
    return order


# Deletar um pedido
def delete_order(order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return True


# Listar tudo
def list_orders():
    return Order.objects.all()


# Buscar um único pedido
def get_order(order_id):
    return get_object_or_404(Order, id=order_id)


# Filtros genéricos
def filter_orders(**filters):
    return Order.objects.filter(**filters)


def calcular_frete(data: dict):
    api = CorreiosAPI()
    return api.calcular(
        produtos=["03220", "03298"],
        cep_origem="30170903",
        cep_destino=data.get("cep_destino", ""),
        peso=data.get("peso", 0),
        comprimento=data.get("comprimento", 0),
        largura=data.get("largura", 0),
        altura=data.get("altura", 0),
        formato=data.get("formato", 1),
    )
    