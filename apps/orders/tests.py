from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from apps.orders.models import Order
from apps.sellers.models import Seller
from apps.orders.services import (
    create_order, 
    update_order, 
    delete_order, 
    list_orders, 
    get_order, 
    filter_orders
)
from apps.orders.utils import formatar_valor


class SellerSetupMixin:
    """Mixin para setup de vendedor."""
    
    def setUp(self):
        """Configuração inicial com vendedor."""
        super().setUp()
        self.seller = Seller.objects.create(
            name='João Silva',
            phone='11999999999'
        )


class OrderModelTestCase(SellerSetupMixin, TestCase):
    """Testes do modelo Order."""

    def test_order_creation(self):
        """Testa a criação de um pedido."""
        order = Order.objects.create(
            name='Pedido #001',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        self.assertEqual(order.name, 'Pedido #001')
        self.assertEqual(order.value, Decimal('100.00'))
        self.assertEqual(order.value_freight, Decimal('10.00'))
        self.assertEqual(order.total, Decimal('110.00'))

    def test_order_total_calculation(self):
        """Testa o cálculo automático do total."""
        order = Order.objects.create(
            name='Pedido #002',
            value=Decimal('150.00'),
            value_freight=Decimal('20.00'),
            status='pending',
            installments=2,
            seller=self.seller
        )
        self.assertEqual(order.total, Decimal('170.00'))

    def test_order_status_choices(self):
        """Testa os valores válidos para status."""
        for status, _ in [('paid', 'Pago'), ('pending', 'Pendente'), ('canceled', 'Cancelado')]:
            order = Order.objects.create(
                name=f'Pedido {status}',
                value=Decimal('100.00'),
                value_freight=Decimal('10.00'),
                status=status,
                installments=1,
                seller=self.seller
            )
            self.assertEqual(order.status, status)

    def test_order_string_representation(self):
        """Testa a representação em string do pedido."""
        order = Order.objects.create(
            name='Pedido #003',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        self.assertEqual(str(order), 'Pedido #003')

    def test_order_with_installments(self):
        """Testa pedido com múltiplas parcelas."""
        order = Order.objects.create(
            name='Pedido #004',
            value=Decimal('300.00'),
            value_freight=Decimal('15.00'),
            status='pending',
            installments=12,
            seller=self.seller
        )
        self.assertEqual(order.installments, 12)
        self.assertEqual(order.total, Decimal('315.00'))

    def test_order_seller_relationship(self):
        """Testa a relação entre Order e Seller."""
        order = Order.objects.create(
            name='Pedido #005',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        self.assertEqual(order.seller, self.seller)
        self.assertIn(order, self.seller.order_set.all())

    def test_order_ordering(self):
        """Testa a ordenação dos pedidos por data de criação (descendente)."""
        order1 = Order.objects.create(
            name='Pedido #001',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        order2 = Order.objects.create(
            name='Pedido #002',
            value=Decimal('200.00'),
            value_freight=Decimal('20.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        orders = list(Order.objects.all())
        self.assertEqual(orders[0], order2)  # Mais recente primeiro
        self.assertEqual(orders[1], order1)


class OrderServiceTestCase(SellerSetupMixin, TestCase):
    """Testes das funções de serviço do Order."""

    def test_create_order_service(self):
        """Testa a criação de pedido via serviço."""
        data = {
            'cliente_nome': 'João Silva',
            'valor_produto': '100.00',
            'valor_frete': '10.00',
            'vendedor': self.seller.id,
            'parcelas': '1'
        }
        order = create_order(data)
        
        self.assertEqual(order.name, 'João Silva')
        self.assertEqual(order.value, Decimal('100.00'))
        self.assertEqual(order.value_freight, Decimal('10.00'))

    def test_create_order_service_with_empty_values(self):
        """Testa a criação de pedido com valores vazios."""
        data = {
            'cliente_nome': '',
            'valor_produto': '',
            'valor_frete': '',
            'vendedor': self.seller.id,
            'parcelas': '1'
        }
        order = create_order(data)
        
        self.assertEqual(order.name, '')
        self.assertEqual(order.value, Decimal('0.00'))

    def test_update_order_service(self):
        """Testa a atualização de pedido via serviço."""
        order = Order.objects.create(
            name='Pedido Original',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        updated_order = update_order(order.id, {'status': 'paid'})
        self.assertEqual(updated_order.status, 'paid')

    def test_delete_order_service(self):
        """Testa a deleção de pedido via serviço."""
        order = Order.objects.create(
            name='Pedido para Deletar',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        order_id = order.id
        
        result = delete_order(order_id)
        self.assertTrue(result)
        
        with self.assertRaises(Order.DoesNotExist):
            Order.objects.get(id=order_id)

    def test_list_orders_service(self):
        """Testa a listagem de pedidos via serviço."""
        Order.objects.create(
            name='Pedido #1',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        Order.objects.create(
            name='Pedido #2',
            value=Decimal('200.00'),
            value_freight=Decimal('20.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        orders = list_orders()
        self.assertEqual(len(orders), 2)

    def test_get_order_service(self):
        """Testa a busca de um pedido específico via serviço."""
        order = Order.objects.create(
            name='Pedido Específico',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        fetched_order = get_order(order.id)
        self.assertEqual(fetched_order.id, order.id)

    def test_filter_orders_service(self):
        """Testa a filtragem de pedidos via serviço."""
        paid_order = Order.objects.create(
            name='Pedido Pago',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='paid',
            installments=1,
            seller=self.seller
        )
        pending_order = Order.objects.create(
            name='Pedido Pendente',
            value=Decimal('200.00'),
            value_freight=Decimal('20.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        filtered = filter_orders(status='paid')
        self.assertEqual(len(filtered), 1)
        self.assertEqual(list(filtered)[0], paid_order)


class OrderUtilsTestCase(TestCase):
    """Testes das funções utilitárias de Order."""

    def test_formatar_valor_string(self):
        """Testa a formatação de valor em string."""
        result = formatar_valor('100.50')
        self.assertEqual(result, Decimal('100.50'))

    def test_formatar_valor_integer(self):
        """Testa a formatação de valor em inteiro."""
        result = formatar_valor(100)
        self.assertEqual(result, Decimal('100.00'))

    def test_formatar_valor_decimal(self):
        """Testa a formatação de valor em Decimal."""
        result = formatar_valor(Decimal('100.50'))
        self.assertEqual(result, Decimal('100.50'))

    def test_formatar_valor_zero(self):
        """Testa a formatação de zero."""
        result = formatar_valor('0')
        self.assertEqual(result, Decimal('0.00'))
