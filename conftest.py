"""
Fixtures e configurações para testes com pytest.
Este arquivo é opcional e pode ser usado com pytest-django.
"""

import pytest
from decimal import Decimal
from django.utils import timezone
from apps.sellers.models import Seller
from apps.orders.models import Order
from apps.payments.models import PaymentLink, Payment


@pytest.fixture
def seller():
    """Fixture para criar um vendedor de teste."""
    return Seller.objects.create(
        name='Vendedor Fixture',
        phone='11999999999'
    )


@pytest.fixture
def order(seller):
    """Fixture para criar um pedido de teste."""
    return Order.objects.create(
        name='Pedido Fixture',
        value=Decimal('100.00'),
        value_freight=Decimal('10.00'),
        status='pending',
        installments=1,
        seller=seller
    )


@pytest.fixture
def payment_link(order):
    """Fixture para criar um link de pagamento de teste."""
    return PaymentLink.objects.create(
        order=order,
        url_link='https://pagar.me/link/fixture',
        id_link='link_fixture',
        amount=order.total,
        status='active'
    )


@pytest.fixture
def payment(payment_link):
    """Fixture para criar um pagamento de teste."""
    return Payment.objects.create(
        payment_link=payment_link,
        status='paid',
        payment_date=timezone.now(),
        amount=payment_link.amount
    )


@pytest.fixture
def multiple_sellers():
    """Fixture para criar múltiplos vendedores de teste."""
    return [
        Seller.objects.create(name=f'Vendedor {i}', phone=f'119999999{i}0')
        for i in range(1, 4)
    ]


@pytest.fixture
def multiple_orders(multiple_sellers):
    """Fixture para criar múltiplos pedidos de teste."""
    orders = []
    for i, seller in enumerate(multiple_sellers):
        for j in range(2):
            order = Order.objects.create(
                name=f'Pedido {seller.name} {j+1}',
                value=Decimal(f'{100 * (j+1)}.00'),
                value_freight=Decimal(f'{10 * (j+1)}.00'),
                status='pending',
                installments=1,
                seller=seller
            )
            orders.append(order)
    return orders


@pytest.fixture
def complete_payment_flow(order):
    """Fixture para criar um fluxo completo de pagamento."""
    link = PaymentLink.objects.create(
        order=order,
        url_link='https://pagar.me/link/complete',
        id_link='link_complete',
        amount=order.total,
        status='active'
    )
    
    payment = Payment.objects.create(
        payment_link=link,
        status='paid',
        payment_date=timezone.now(),
        amount=order.total
    )
    
    return {
        'order': order,
        'link': link,
        'payment': payment
    }


# Marcadores customizados para testes
def pytest_configure(config):
    """Registra marcadores customizados para testes."""
    config.addinivalue_line(
        "markers", "slow: marca teste como lento"
    )
    config.addinivalue_line(
        "markers", "integration: marca teste como teste de integração"
    )
    config.addinivalue_line(
        "markers", "unit: marca teste como teste unitário"
    )
    config.addinivalue_line(
        "markers", "api: marca teste como teste de API"
    )
