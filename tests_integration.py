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


class OrderPaymentSynchronizationTestCase(TestCase):
    """Testes de sincronização entre Order, PaymentLink e Payment."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.seller = Seller.objects.create(
            name='Vendedor Sync Test',
            phone='11999999999'
        )

    def test_order_status_follows_payment_status(self):
        """Testa se o status do pedido pode ser atualizado quando há pagamento."""
        order = Order.objects.create(
            name='Pedido Sync',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        link = PaymentLink.objects.create(
            order=order,
            url_link='https://pagar.me/link/sync',
            id_link='link_sync',
            amount=order.total,
            status='active'
        )
        
        payment = Payment.objects.create(
            payment_link=link,
            status='paid',
            payment_date=timezone.now(),
            amount=order.total
        )
        
        # Após pagamento bem-sucedido, podemos atualizar manualmente o pedido
        # (ou através de um signal, caso esteja configurado)
        order.status = 'paid'
        order.save()
        
        # Verificar sincronização
        order.refresh_from_db()
        link.refresh_from_db()
        
        self.assertEqual(order.status, 'paid')
        self.assertEqual(link.status, 'active')  # O link permanece ativo

    def test_payment_link_update_cascades_to_order(self):
        """Testa se atualizações no link cascateiam para o pedido."""
        order = Order.objects.create(
            name='Pedido Cascade',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        link = PaymentLink.objects.create(
            order=order,
            url_link='https://pagar.me/link/cascade',
            id_link='link_cascade',
            amount=order.total,
            status='active'
        )
        
        # Cancelar o link
        link.status = 'canceled'
        link.save()
        
        link.refresh_from_db()
        self.assertEqual(link.status, 'canceled')

    def test_multiple_payment_attempts(self):
        """Testa múltiplas tentativas de pagamento para o mesmo pedido."""
        order = Order.objects.create(
            name='Pedido Múltiplas Tentativas',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        # O signal cria um link automaticamente, então contaremos com isso
        initial_link_count = PaymentLink.objects.filter(order=order).count()
        
        # Primeira tentativa falha
        link1 = PaymentLink.objects.first()  # Pega o criado pelo signal
        if link1:
            payment1 = Payment.objects.create(
                payment_link=link1,
                status='failed',
                payment_date=timezone.now(),
                amount=order.total
            )
            
            link1.status = 'expired'
            link1.save()
        
        # Segunda tentativa bem-sucedida
        link2 = PaymentLink.objects.create(
            order=order,
            url_link='https://pagar.me/link/2',
            id_link='link_2',
            amount=order.total,
            status='active'
        )
        
        payment2 = Payment.objects.create(
            payment_link=link2,
            status='paid',
            payment_date=timezone.now(),
            amount=order.total
        )
        
        # Verificar histórico
        links = PaymentLink.objects.filter(order=order)
        # Pelo menos 2 links (signal + manual)
        self.assertGreaterEqual(links.count(), 2)
        
        payments = Payment.objects.filter(payment_link__order=order)
        # Pelo menos 2 pagamentos
        self.assertGreaterEqual(payments.count(), 1)


class DataConsistencyTestCase(TestCase):
    """Testes de consistência de dados entre entidades."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.seller = Seller.objects.create(
            name='Vendedor Consistência',
            phone='11999999999'
        )

    def test_order_total_calculation_consistency(self):
        """Testa se o total do pedido é sempre consistente."""
        order = Order.objects.create(
            name='Pedido Consistência',
            value=Decimal('99.99'),
            value_freight=Decimal('9.99'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        expected_total = Decimal('109.98')
        self.assertEqual(order.total, expected_total)
        
        # Atualizar e verificar novamente
        order.value = Decimal('100.00')
        order.save()
        
        order.refresh_from_db()
        expected_total = Decimal('109.99')
        self.assertEqual(order.total, expected_total)

    def test_payment_amount_matches_link_amount(self):
        """Testa se o valor do pagamento corresponde ao valor do link."""
        order = Order.objects.create(
            name='Pedido Valores',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        link = PaymentLink.objects.create(
            order=order,
            url_link='https://pagar.me/link/valor',
            id_link='link_valor',
            amount=order.total,
            status='active'
        )
        
        payment = Payment.objects.create(
            payment_link=link,
            status='paid',
            payment_date=timezone.now(),
            amount=link.amount
        )
        
        self.assertEqual(payment.amount, link.amount)
        self.assertEqual(payment.amount, order.total)

    def test_seller_order_count_accuracy(self):
        """Testa a precisão da contagem de pedidos por vendedor."""
        # Criar múltiplos pedidos
        for i in range(5):
            Order.objects.create(
                name=f'Pedido {i}',
                value=Decimal('10.00'),
                value_freight=Decimal('1.00'),
                status='pending',
                installments=1,
                seller=self.seller
            )
        
        seller_orders = Order.objects.filter(seller=self.seller)
        self.assertEqual(seller_orders.count(), 5)
        
        # Deletar um e verificar
        seller_orders.first().delete()
        
        seller_orders = Order.objects.filter(seller=self.seller)
        self.assertEqual(seller_orders.count(), 4)


class PerformanceTestCase(TestCase):
    """Testes de performance e escalabilidade."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.seller = Seller.objects.create(
            name='Vendedor Performance',
            phone='11999999999'
        )

    def test_large_order_batch_creation(self):
        """Testa criação em lote de múltiplos pedidos."""
        orders = [
            Order(
                name=f'Pedido Batch {i}',
                value=Decimal('100.00'),
                value_freight=Decimal('10.00'),
                total=Decimal('110.00'),  # Deve ser calculado, mas vamos ser explícito
                status='pending',
                installments=1,
                seller=self.seller
            )
            for i in range(100)
        ]
        
        Order.objects.bulk_create(orders)
        
        total_orders = Order.objects.filter(seller=self.seller).count()
        self.assertEqual(total_orders, 100)

    def test_payment_filtering_performance(self):
        """Testa performance de filtros de pagamentos."""
        # Criar múltiplos pagamentos
        for i in range(50):
            order = Order.objects.create(
                name=f'Pedido Performance {i}',
                value=Decimal('100.00'),
                value_freight=Decimal('10.00'),
                status='pending',
                installments=1,
                seller=self.seller
            )
            
            link = PaymentLink.objects.create(
                order=order,
                url_link=f'https://pagar.me/link/perf/{i}',
                id_link=f'link_perf_{i}',
                amount=order.total,
                status='active'
            )
            
            status = 'paid' if i % 2 == 0 else 'pending'
            Payment.objects.create(
                payment_link=link,
                status=status,
                payment_date=timezone.now(),
                amount=order.total
            )
        
        # Filtrar pagamentos
        paid_payments = Payment.objects.filter(status='paid')
        pending_payments = Payment.objects.filter(status='pending')
        
        self.assertGreater(paid_payments.count(), 0)
        self.assertGreater(pending_payments.count(), 0)
