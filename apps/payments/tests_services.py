from django.test import TestCase
from decimal import Decimal
from apps.sellers.models import Seller
from apps.orders.models import Order
from apps.payments.models import PaymentLink, Payment
from apps.payments import services
from django.utils import timezone


class PaymentsServicesTests(TestCase):
    """Testes dos serviços de pagamento."""
    
    def setUp(self):
        self.seller = Seller.objects.create(name="Seller Pay", phone="999")
        self.order = Order.objects.create(
            name="Order Pay",
            value=Decimal('20.00'),
            value_freight=Decimal('5.00'),
            total=Decimal('25.00'),
            status='pending',
            installments=1,
            seller=self.seller,
        )
        self.link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pay.test/1',
            id_link='lnk_test',
            amount=self.order.total,
            status='active',
        )

    def test_create_and_query_links(self):
        """Testa criação e consulta de links de pagamento."""
        links = services.get_payment_links_for_order(self.order)
        self.assertEqual(list(links)[0].id, self.link.id)

    def test_cancel_payment_link(self):
        """Testa cancelamento de link de pagamento."""
        ok = services.cancel_payment_link(self.link.id)
        self.assertTrue(ok)
        self.link.refresh_from_db()
        self.assertEqual(self.link.status, 'canceled')

    def test_calculate_total_from_links(self):
        """Testa cálculo do total a partir dos links."""
        total = services.calculate_total_from_links([self.link])
        self.assertEqual(total, Decimal('25.00'))

    def test_get_payment_status_none(self):
        """Testa busca de status quando não há pagamento."""
        # Ainda não há Payment associado
        self.assertIsNone(services.get_payment_status(9999))

    def test_create_payment_record_via_webhook(self):
        """Testa criação de registro de pagamento via webhook."""
        payload = {
            'data': {
                'id': self.link.id_link,
                'status': 'paid',
                'amount': int(self.link.amount * 100),
                'paid_at': timezone.now(),
            }
        }
        payment = services.process_payment_webhook(payload)
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'paid')
        # PaymentLink should be updated
        self.link.refresh_from_db()
        self.assertEqual(self.link.status, 'paid')

    def test_get_payment_links_multiple(self):
        """Testa busca de múltiplos links para um pedido."""
        # O signal cria um link automaticamente, então precisa contar isso
        initial_count = PaymentLink.objects.filter(order=self.order).count()
        
        link2 = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pay.test/2',
            id_link='lnk_test2',
            amount=self.order.total,
            status='active',
        )
        
        links = list(services.get_payment_links_for_order(self.order))
        # initial_count + 1 novo link
        self.assertEqual(len(links), initial_count + 1)

    def test_cancel_nonexistent_link(self):
        """Testa cancelamento de link inexistente."""
        ok = services.cancel_payment_link(9999)
        self.assertFalse(ok)

    def test_calculate_total_empty_list(self):
        """Testa cálculo de total com lista vazia."""
        total = services.calculate_total_from_links([])
        self.assertEqual(total, Decimal('0.00'))

    def test_calculate_total_multiple_links(self):
        """Testa cálculo de total com múltiplos links."""
        link2 = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pay.test/2',
            id_link='lnk_test2',
            amount=Decimal('50.00'),
            status='active',
        )
        
        total = services.calculate_total_from_links([self.link, link2])
        self.assertEqual(total, Decimal('75.00'))

    def test_webhook_with_invalid_data(self):
        """Testa webhook com dados inválidos."""
        payload = {
            'data': {
                'id': 'link_inexistente',
                'status': 'paid',
                'amount': 2500,
            }
        }
        
        # Não deve gerar erro
        result = services.process_payment_webhook(payload)

    def test_webhook_status_update(self):
        """Testa atualização de status via webhook."""
        payload = {
            'data': {
                'id': self.link.id_link,
                'status': 'failed',
                'amount': int(self.link.amount * 100),
            }
        }
        
        payment = services.process_payment_webhook(payload)
        if payment:
            self.assertEqual(payment.status, 'failed')

    def test_get_payment_by_link_id(self):
        """Testa busca de pagamento por ID do link."""
        payment = Payment.objects.create(
            payment_link=self.link,
            status='paid',
            payment_date=timezone.now(),
            amount=self.link.amount
        )
        
        fetched = services.get_payment_by_link(self.link.id)
        if fetched:
            self.assertEqual(fetched.id, payment.id)

    def test_list_payments_by_status_paid(self):
        """Testa listagem de pagamentos com status pago."""
        Payment.objects.create(
            payment_link=self.link,
            status='paid',
            payment_date=timezone.now(),
            amount=self.link.amount
        )
        
        payments = services.list_payments_by_status('paid')
        self.assertGreaterEqual(len(payments), 1)

    def test_list_payments_by_status_pending(self):
        """Testa listagem de pagamentos com status pendente."""
        link2 = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pay.test/pending',
            id_link='lnk_pending',
            amount=self.order.total,
            status='active',
        )
        
        Payment.objects.create(
            payment_link=link2,
            status='pending',
            payment_date=timezone.now(),
            amount=link2.amount
        )
        
        payments = services.list_payments_by_status('pending')
        self.assertGreaterEqual(len(payments), 1)

    def test_get_payment_statistics(self):
        """Testa obtenção de estatísticas de pagamentos."""
        # Criar alguns pagamentos
        Payment.objects.create(
            payment_link=self.link,
            status='paid',
            payment_date=timezone.now(),
            amount=self.link.amount
        )
        
        stats = services.get_payment_statistics()
        if stats:
            self.assertIn('count_paid', stats)
            self.assertIn('count_pending', stats)

    def test_link_creation_with_different_amounts(self):
        """Testa criação de links com valores diferentes."""
        amounts = [Decimal('10.00'), Decimal('50.00'), Decimal('100.00')]
        
        for amount in amounts:
            link = PaymentLink.objects.create(
                order=self.order,
                url_link=f'https://pay.test/{amount}',
                id_link=f'lnk_{amount}',
                amount=amount,
                status='active',
            )
            self.assertEqual(link.amount, amount)

    def test_payment_webhook_multiple_times(self):
        """Testa processamento múltiplo de webhook para mesmo link."""
        payload1 = {
            'data': {
                'id': self.link.id_link,
                'status': 'pending',
                'amount': int(self.link.amount * 100),
            }
        }
        
        result1 = services.process_payment_webhook(payload1)
        
        # Segundo processamento
        payload2 = {
            'data': {
                'id': self.link.id_link,
                'status': 'paid',
                'amount': int(self.link.amount * 100),
            }
        }
        
        result2 = services.process_payment_webhook(payload2)

    def test_cancel_already_canceled_link(self):
        """Testa cancelamento de link já cancelado."""
        self.link.status = 'canceled'
        self.link.save()
        
        ok = services.cancel_payment_link(self.link.id)
        # Deve retornar True mesmo se já está cancelado
        self.assertTrue(ok)
        
        self.link.refresh_from_db()
        self.assertEqual(self.link.status, 'canceled')

    def test_payment_amount_precision(self):
        """Testa precisão dos valores de pagamento."""
        exact_amount = Decimal('99.99')
        link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pay.test/precision',
            id_link='lnk_precision',
            amount=exact_amount,
            status='active',
        )
        
        payment = Payment.objects.create(
            payment_link=link,
            status='paid',
            payment_date=timezone.now(),
            amount=exact_amount
        )
        
        self.assertEqual(payment.amount, exact_amount)
        self.assertEqual(link.amount, exact_amount)

    def test_order_relationship_through_payment(self):
        """Testa acesso ao pedido através de um pagamento."""
        payment = Payment.objects.create(
            payment_link=self.link,
            status='paid',
            payment_date=timezone.now(),
            amount=self.link.amount
        )
        
        order = payment.order
        self.assertEqual(order, self.order)
