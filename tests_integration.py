"""
Testes de Integração para o projeto BibPay.
Testa o fluxo completo de criação de pedido, link de pagamento e pagamento.
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from apps.orders.models import Order
from apps.sellers.models import Seller
from apps.payments.models import Payment, PaymentLink
from apps.orders.services import create_order
from apps.payments.services import (
    create_payment_link_record,
    process_payment_webhook,
    get_payment_statistics
)


class EndToEndPaymentFlowTestCase(TestCase):
    """Testes do fluxo completo de criação de pedido e pagamento."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.seller = Seller.objects.create(
            name='Vendedor Integração',
            phone='11999999999'
        )

    def test_complete_order_to_payment_flow(self):
        """Testa o fluxo completo: criar pedido -> criar link -> processar pagamento."""
        
        # 1. Criar pedido
        order_data = {
            'cliente_nome': 'Cliente Teste',
            'valor_produto': '100.00',
            'valor_frete': '10.00',
            'vendedor': self.seller.id,
            'parcelas': '3'
        }
        order = create_order(order_data)
        
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.total, Decimal('110.00'))
        self.assertEqual(order.installments, 3)
        
        # 2. Criar link de pagamento
        link_data = {
            'id': 'link_test_123',
            'url': 'https://pagar.me/link/test/123'
        }
        payment_link = create_payment_link_record(order, link_data)
        
        self.assertEqual(payment_link.order, order)
        self.assertEqual(payment_link.status, 'active')
        
        # 3. Simular webhook de pagamento
        webhook_data = {
            'data': {
                'id': 'link_test_123',
                'status': 'paid',
                'amount': 11000,  # 110 reais em centavos
                'paid_at': timezone.now().isoformat()
            }
        }
        payment = process_payment_webhook(webhook_data)
        
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'paid')
        
        # Verificar sincronização de status
        order.refresh_from_db()
        payment_link.refresh_from_db()
        
        self.assertEqual(order.status, 'paid')
        self.assertEqual(payment_link.status, 'paid')

    def test_multiple_orders_same_seller(self):
        """Testa a criação de múltiplos pedidos do mesmo vendedor."""
        
        orders_data = [
            {
                'cliente_nome': 'Cliente 1',
                'valor_produto': '50.00',
                'valor_frete': '5.00',
                'vendedor': self.seller.id,
                'parcelas': '1'
            },
            {
                'cliente_nome': 'Cliente 2',
                'valor_produto': '100.00',
                'valor_frete': '10.00',
                'vendedor': self.seller.id,
                'parcelas': '2'
            },
            {
                'cliente_nome': 'Cliente 3',
                'valor_produto': '200.00',
                'valor_frete': '20.00',
                'vendedor': self.seller.id,
                'parcelas': '12'
            }
        ]
        
        orders = [create_order(data) for data in orders_data]
        
        self.assertEqual(len(orders), 3)
        self.assertTrue(all(order.seller == self.seller for order in orders))
        
        # Verificar totais
        self.assertEqual(orders[0].total, Decimal('55.00'))
        self.assertEqual(orders[1].total, Decimal('110.00'))
        self.assertEqual(orders[2].total, Decimal('220.00'))

    def test_payment_statistics_calculation(self):
        """Testa o cálculo de estatísticas de pagamentos."""
        
        # Criar vários pedidos e pagamentos
        for i in range(3):
            order = Order.objects.create(
                name=f'Pedido {i}',
                value=Decimal('100.00'),
                value_freight=Decimal('10.00'),
                status='pending',
                installments=1,
                seller=self.seller
            )
            
            link = PaymentLink.objects.create(
                order=order,
                url_link=f'https://pagar.me/link/{i}',
                id_link=f'link_{i}',
                amount=order.total,
                status='active'
            )
            
            # Criar alguns pagamentos pagos e alguns pendentes
            status = 'paid' if i % 2 == 0 else 'pending'
            Payment.objects.create(
                payment_link=link,
                status=status,
                payment_date=timezone.now(),
                amount=order.total
            )
        
        # Calcular estatísticas
        stats = get_payment_statistics()
        
        self.assertIsNotNone(stats)
        self.assertGreaterEqual(stats['count_paid'], 1)
        self.assertGreaterEqual(stats['count_pending'], 1)

    def test_order_with_different_sellers(self):
        """Testa pedidos com diferentes vendedores."""
        
        seller2 = Seller.objects.create(
            name='Vendedor 2',
            phone='11988888888'
        )
        
        order1 = Order.objects.create(
            name='Pedido Vendedor 1',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        order2 = Order.objects.create(
            name='Pedido Vendedor 2',
            value=Decimal('200.00'),
            value_freight=Decimal('20.00'),
            status='pending',
            installments=1,
            seller=seller2
        )
        
        self.assertEqual(order1.seller, self.seller)
        self.assertEqual(order2.seller, seller2)
        self.assertNotEqual(order1.seller, order2.seller)

    def test_payment_link_uniqueness_per_order(self):
        """Testa a possibilidade de múltiplos links por pedido."""
        
        order = Order.objects.create(
            name='Pedido Teste Múltiplos Links',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        # O signal cria um link automaticamente, então já teremos 1
        initial_count = PaymentLink.objects.filter(order=order).count()
        self.assertGreater(initial_count, 0)
        
        # Criar mais links para o mesmo pedido
        link1 = PaymentLink.objects.create(
            order=order,
            url_link='https://pagar.me/link/1',
            id_link='link_1',
            amount=order.total,
            status='active'
        )
        
        link2 = PaymentLink.objects.create(
            order=order,
            url_link='https://pagar.me/link/2',
            id_link='link_2',
            amount=order.total,
            status='expired'
        )
        
        links = PaymentLink.objects.filter(order=order)
        # Signal criou 1, + 2 manuais = 3 total
        self.assertEqual(links.count(), 3)

    def test_payment_status_transitions(self):
        """Testa as transições de status de pagamento."""
        
        order = Order.objects.create(
            name='Pedido Status Test',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        link = PaymentLink.objects.create(
            order=order,
            url_link='https://pagar.me/link/status',
            id_link='link_status',
            amount=order.total,
            status='active'
        )
        
        # Simular diferentes status de pagamento
        statuses = ['paid', 'pending', 'failed', 'canceled', 'refunded']
        
        for status in statuses:
            payment = Payment.objects.create(
                payment_link=link if status == statuses[0] else PaymentLink.objects.create(
                    order=order,
                    url_link=f'https://pagar.me/link/{status}',
                    id_link=f'link_{status}',
                    amount=order.total,
                    status='active'
                ),
                status=status,
                payment_date=timezone.now(),
                amount=order.total
            )
            
            self.assertEqual(payment.status, status)
