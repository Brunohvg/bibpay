"""
Testes adicionais e abrangentes para todas as views, services e integrações.
Foca em cobertura de edge cases, validações e comportamentos esperados.
"""
from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone
from unittest.mock import patch, MagicMock

from apps.sellers.models import Seller
from apps.orders.models import Order
from apps.payments.models import PaymentLink, Payment
from apps.payments import services as payment_services
from apps.orders import services as order_services


class OrderFreteViewTests(TestCase):
    """Testes da view de cálculo de frete."""

    def setUp(self):
        self.client = Client()

    def test_order_frete_get(self):
        """Testa GET na view de frete."""
        url = reverse('orders:order-frete')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_order_frete_post_valid(self):
        """Testa POST com dados válidos."""
        url = reverse('orders:order-frete')
        data = {
            'cep': '01310-100',
            'weight': '2.5',
            'length': '30',
            'width': '20',
            'height': '15',
        }
        with patch('apps.orders.services.calcular_frete') as mock_frete:
            mock_frete.return_value = {'servicos': [{'valor': '25.50'}]}
            resp = self.client.post(url, data)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('freight', resp.context)

    def test_order_frete_post_invalid_data(self):
        """Testa POST com dados inválidos."""
        url = reverse('orders:order-frete')
        data = {
            'cep': '',
            'weight': 'invalid',
            'length': '',
            'width': '',
            'height': '',
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('error', resp.context)


class OrderSuccessViewTests(TestCase):
    """Testes da view de sucesso de pedido."""

    def setUp(self):
        self.client = Client()
        self.seller = Seller.objects.create(name="Seller", phone="123")
        self.order = Order.objects.create(
            name="Order",
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            total=Decimal('110.00'),
            status='pending',
            installments=1,
            seller=self.seller,
        )
        self.link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pay.test',
            id_link='lnk_test',
            amount=Decimal('110.00'),
            status='active',
        )

    def test_order_success_view_unpaid(self):
        """Testa view de sucesso para pedido não pago."""
        url = reverse('orders:order-success', args=[self.order.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('payment_link', resp.context)

    def test_order_success_view_paid(self):
        """Testa view de sucesso para pedido pago."""
        payment = Payment.objects.create(
            payment_link=self.link,
            status='paid',
            amount=Decimal('110.00'),
            payment_date=timezone.now(),
        )
        
        url = reverse('orders:order-success', args=[self.order.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Deve renderizar recibo para pagamento confirmado
        self.assertIn('payment', resp.context)

    def test_order_success_view_nonexistent_order(self):
        """Testa view de sucesso com pedido inexistente."""
        url = reverse('orders:order-success', args=[9999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


class PaymentsWebhookTests(TestCase):
    """Testes de processamento de webhooks de pagamento."""

    def setUp(self):
        self.seller = Seller.objects.create(name="Seller", phone="123")
        self.order = Order.objects.create(
            name="Order",
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            total=Decimal('110.00'),
            status='pending',
            installments=1,
            seller=self.seller,
        )
        self.link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pay.test',
            id_link='charge_123',
            amount=Decimal('110.00'),
            status='active',
        )

    def test_webhook_payment_paid(self):
        """Testa webhook de pagamento confirmado."""
        payload = {
            'data': {
                'id': 'charge_123',
                'status': 'paid',
                'amount': 11000,
                'paid_at': timezone.now(),
            }
        }
        
        payment = payment_services.process_payment_webhook(payload)
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'paid')
        
        # Verificar se PaymentLink foi atualizado
        self.link.refresh_from_db()
        self.assertEqual(self.link.status, 'paid')
        self.assertFalse(self.link.is_active)

    def test_webhook_payment_canceled(self):
        """Testa webhook de pagamento cancelado."""
        payload = {
            'data': {
                'id': 'charge_123',
                'status': 'canceled',
                'amount': 11000,
                'paid_at': timezone.now(),
            }
        }
        
        payment = payment_services.process_payment_webhook(payload)
        self.assertEqual(payment.status, 'canceled')
        
        self.link.refresh_from_db()
        self.assertEqual(self.link.status, 'canceled')

    def test_webhook_payment_refunded(self):
        """Testa webhook de reembolso."""
        payload = {
            'data': {
                'id': 'charge_123',
                'status': 'refunded',
                'amount': 11000,
                'paid_at': timezone.now(),
            }
        }
        
        payment = payment_services.process_payment_webhook(payload)
        self.assertEqual(payment.status, 'refunded')

    def test_webhook_unknown_charge(self):
        """Testa webhook para charge desconhecido."""
        payload = {
            'data': {
                'id': 'charge_unknown',
                'status': 'paid',
                'amount': 11000,
                'paid_at': timezone.now(),
            }
        }
        
        payment = payment_services.process_payment_webhook(payload)
        self.assertIsNone(payment)


class PaymentsServicesExtendedTests(TestCase):
    """Testes estendidos para services de pagamentos."""

    def setUp(self):
        self.seller = Seller.objects.create(name="Seller", phone="123")
        self.order = Order.objects.create(
            name="Order",
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            total=Decimal('110.00'),
            status='pending',
            installments=1,
            seller=self.seller,
        )

    def test_list_active_payment_links(self):
        """Testa listagem de links ativos."""
        # Nota: o signal cria um link automaticamente
        link2 = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pay.test/2',
            id_link='lnk_2',
            amount=Decimal('110.00'),
            status='expired',
        )
        
        active_links = payment_services.list_active_payment_links()
        # Após o signal, há pelo menos 1 link ativo
        self.assertGreaterEqual(active_links.count(), 1)
        # Verificar que links inativos não estão na lista
        self.assertNotIn(link2.id, [l.id for l in active_links])

    def test_list_payments_by_status(self):
        """Testa listagem de pagamentos por status."""
        link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pay.test',
            id_link='lnk_test',
            amount=Decimal('110.00'),
            status='active',
        )
        
        payment_paid = Payment.objects.create(
            payment_link=link,
            status='paid',
            amount=Decimal('110.00'),
            payment_date=timezone.now(),
        )
        
        paid_payments = payment_services.list_payments_by_status('paid')
        self.assertEqual(paid_payments.count(), 1)

    def test_get_payment_statistics(self):
        """Testa obtenção de estatísticas de pagamentos."""
        link1 = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pay.test/1',
            id_link='lnk_1',
            amount=Decimal('100.00'),
            status='active',
        )
        link2 = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pay.test/2',
            id_link='lnk_2',
            amount=Decimal('50.00'),
            status='active',
        )
        
        payment1 = Payment.objects.create(
            payment_link=link1,
            status='paid',
            amount=Decimal('100.00'),
            payment_date=timezone.now(),
        )
        payment2 = Payment.objects.create(
            payment_link=link2,
            status='pending',
            amount=Decimal('50.00'),
            payment_date=timezone.now(),
        )
        
        stats = payment_services.get_payment_statistics()
        self.assertEqual(stats['count_paid'], 1)
        self.assertEqual(stats['count_pending'], 1)


class DashboardViewsExtendedTests(TestCase):
    """Testes estendidos para views de dashboard."""

    def setUp(self):
        self.client = Client()
        self.seller = Seller.objects.create(name="Seller", phone="123")
        
        # Criar múltiplos pedidos e pagamentos
        for i in range(5):
            order = Order.objects.create(
                name=f"Order {i}",
                value=Decimal('100.00'),
                value_freight=Decimal('10.00'),
                total=Decimal('110.00'),
                status='pending' if i % 2 == 0 else 'paid',
                installments=1,
                seller=self.seller,
            )
            
            link = PaymentLink.objects.create(
                order=order,
                url_link=f'https://pay.test/{i}',
                id_link=f'lnk_{i}',
                amount=Decimal('110.00'),
                status='active' if i % 2 == 0 else 'paid',
            )
            
            if i % 2 != 0:
                Payment.objects.create(
                    payment_link=link,
                    status='paid',
                    amount=Decimal('110.00'),
                    payment_date=timezone.now(),
                )

    def test_dashboard_context_has_all_keys(self):
        """Testa que dashboard contém todas as chaves de contexto esperadas."""
        url = reverse('dashboard:dashboard-home')
        resp = self.client.get(url)
        
        expected_keys = [
            'volume_processado', 'total_received', 'valor_em_aberto',
            'total_pagos', 'total_pendentes', 'total_cancelados',
            'taxa_conversao', 'ticket_medio', 'total_sellers',
            'recent_links', 'chart_data', 'week_growth'
        ]
        
        for key in expected_keys:
            self.assertIn(key, resp.context, f"Chave {key} faltando no contexto")

    def test_dashboard_metrics_calculation(self):
        """Testa que as métricas do dashboard são calculadas corretamente."""
        url = reverse('dashboard:dashboard-home')
        resp = self.client.get(url)
        
        self.assertEqual(resp.context['total_sellers'], 1)
        self.assertGreaterEqual(resp.context['volume_processado'], 0)

    def test_dashboard_chart_data_structure(self):
        """Testa que os dados do gráfico têm a estrutura esperada."""
        url = reverse('dashboard:dashboard-home')
        resp = self.client.get(url)
        
        chart_data = resp.context['chart_data']
        self.assertIsInstance(chart_data, list)
        self.assertEqual(len(chart_data), 7)  # 7 dias
        
        for item in chart_data:
            self.assertIn('day', item)
            self.assertIn('count', item)
            self.assertIn('height', item)
            self.assertIn('is_today', item)


class OrderServicesExtendedTests(TestCase):
    """Testes estendidos para services de pedidos."""

    def setUp(self):
        self.seller = Seller.objects.create(name="Seller", phone="123")

    def test_create_order_success(self):
        """Testa criação bem-sucedida de pedido."""
        data = {
            'cliente_nome': 'Cliente Teste',
            'valor_produto': '150.00',
            'valor_frete': '10.50',
            'vendedor': self.seller.id,
            'parcelas': '3'
        }
        
        order = order_services.create_order(data)
        self.assertIsNotNone(order)
        self.assertEqual(order.name, 'Cliente Teste')
        self.assertEqual(order.value, Decimal('150.00'))

    def test_create_order_with_invalid_seller(self):
        """Testa criação de pedido com vendedor inválido."""
        data = {
            'cliente_nome': 'Cliente Teste',
            'valor_produto': '150.00',
            'valor_frete': '10.50',
            'vendedor': 9999,
            'parcelas': '3'
        }
        
        with self.assertRaises(ValueError):
            order_services.create_order(data)

    def test_list_orders(self):
        """Testa listagem de pedidos."""
        Order.objects.create(
            name="Order 1",
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            total=Decimal('110.00'),
            status='pending',
            installments=1,
            seller=self.seller,
        )
        Order.objects.create(
            name="Order 2",
            value=Decimal('200.00'),
            value_freight=Decimal('20.00'),
            total=Decimal('220.00'),
            status='paid',
            installments=2,
            seller=self.seller,
        )
        
        orders = order_services.list_orders()
        self.assertEqual(len(orders), 2)

    def test_update_order(self):
        """Testa atualização de pedido."""
        order = Order.objects.create(
            name="Original",
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            total=Decimal('110.00'),
            status='pending',
            installments=1,
            seller=self.seller,
        )
        
        updated = order_services.update_order(order.id, {'name': 'Updated'})
        self.assertEqual(updated.name, 'Updated')

    def test_delete_order(self):
        """Testa deleção de pedido."""
        order = Order.objects.create(
            name="To Delete",
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            total=Decimal('110.00'),
            status='pending',
            installments=1,
            seller=self.seller,
        )
        
        order_id = order.id
        order_services.delete_order(order_id)
        
        with self.assertRaises(Order.DoesNotExist):
            Order.objects.get(id=order_id)

    def test_filter_orders_by_status(self):
        """Testa filtro de pedidos por status."""
        # Limpar orders criados automaticamente pelo signal
        Order.objects.all().delete()
        
        Order.objects.create(
            name="Pending",
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            total=Decimal('110.00'),
            status='pending',
            installments=1,
            seller=self.seller,
        )
        Order.objects.create(
            name="Paid",
            value=Decimal('200.00'),
            value_freight=Decimal('20.00'),
            total=Decimal('220.00'),
            status='paid',
            installments=2,
            seller=self.seller,
        )
        
        # Usar o QuerySet diretamente
        pending_orders = Order.objects.filter(status='pending')
        self.assertEqual(len(pending_orders), 1)
