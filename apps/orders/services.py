from apps.orders.models import Order
from apps.orders.utils import formatar_valor
from apps.sellers.services import get_seller
from apps.core.integrations.pagarme import PagarMePaymentLink


def create_order(data):
    """
    Cria um pedido e gera um link de pagamento no Pagar.me para teste.
    
    Args:
        data (dict): Dados contendo cliente_nome, valor_produto, valor_frete, parcelas, vendedor
        
    Returns:
        Order: Instância do pedido criado
    """
    order_data = {
        'name': data['cliente_nome'],
        'value': formatar_valor(data['valor_produto']),
        'value_freight': formatar_valor(data['valor_frete']),
        'status': 'pending',
        'installments': data['parcelas'],
        'seller': get_seller(seller_id=data['vendedor'])
    }
    
    # Gerar link de pagamento (será salvo depois em outro model)
    try:
        link = PagarMePaymentLink(
            customer_name=order_data.get('name'), 
            total_amount=int(order_data.get('value') * 100),  # Converter para centavos
            max_installments=order_data.get('installments'), 
            free_installments=order_data.get('installments')
        )
        
        response = link.create_link()
        print(f"✓ Link gerado com sucesso:")
        print(f"URL: {response.get('short_url') or response.get('url')}")
        print(f"ID: {response.get('id')}")
        print(f"Resposta completa: {response}")
        
    except Exception as e:
        print(f"✗ Erro ao gerar link: {str(e)}")
    
    # Criar pedido (o link será salvo depois em outro model conforme necessário)
    order = Order.objects.create(**order_data)
    return order

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
