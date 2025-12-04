from apps.orders.models import Order
from django.shortcuts import get_object_or_404
from apps.orders.utils import formatar_valor
from apps.sellers.services import get_seller



# Criar um pedido
def create_order(data):
    order_data = {
        'name': data['cliente_nome'],
        'value': formatar_valor(data['valor_produto']),
        'status': 'paid',
        'value_freight': formatar_valor(data['valor_frete']),
        'installments': data['parcelas'],
        'seller': get_seller(seller_id=data['vendedor'])
    }
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
