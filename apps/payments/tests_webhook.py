"""
Testes HTTP do Webhook de Pagamentos.

Testa o endpoint de webhook via chamadas HTTP simuladas.
Com suporte para fila Celery (mock das tasks).
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.sellers.models import Seller
from apps.orders.models import Order
from apps.payments.models import PaymentLink, Payment


# Desabilitar Celery durante testes - executar sync
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class WebhookAPITests(TestCase):
    """Testes do endpoint de webhook HTTP."""
    
    def setUp(self):
        self.client = APIClient()
        self.seller = Seller.objects.create(
            name="Vendedor Teste",
            phone="11999999999"
        )
        self.order = Order.objects.create(
            name="Pedido Teste",
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            total=Decimal('110.00'),
            status='pending',
            installments=1,
            seller=self.seller,
        )
        self.payment_link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pay.test/webhook-test',
            id_link='lnk_webhook_test',
            amount=self.order.total,
            status='active',
        )
        # URL do webhook
        self.webhook_url = '/api/payments/v1/hook/'
    
    def test_webhook_payment_paid_success(self):
        """Testa webhook de pagamento aprovado com sucesso."""
        payload = {
            'type': 'charge.paid',
            'data': {
                'code': self.payment_link.id_link,
                'status': 'paid',
                'paid_amount': int(self.payment_link.amount * 100),
                'paid_at': '2025-12-29T23:00:00-03:00',
            }
        }
        
        with patch('apps.notifications.tasks.send_payment_notification_task.delay') as mock_task:
            response = self.client.post(
                self.webhook_url,
                data=payload,
                format='json'
            )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        
        # Verificar que o pagamento foi criado
        payment = Payment.objects.filter(payment_link=self.payment_link).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'paid')
        
        # Verificar que o link foi atualizado
        self.payment_link.refresh_from_db()
        self.assertEqual(self.payment_link.status, 'used')
        
        # Verificar que a task foi enfileirada
        mock_task.assert_called_once()
    
    def test_webhook_payment_canceled(self):
        """Testa webhook de pagamento cancelado."""
        payload = {
            'type': 'charge.canceled',
            'data': {
                'code': self.payment_link.id_link,
                'status': 'canceled',
                'paid_amount': 0,
            }
        }
        
        with patch('apps.notifications.tasks.send_payment_notification_task.delay') as mock_task:
            response = self.client.post(
                self.webhook_url,
                data=payload,
                format='json'
            )
        
        self.assertEqual(response.status_code, 200)
        
        payment = Payment.objects.filter(payment_link=self.payment_link).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'canceled')
    
    def test_webhook_payment_failed(self):
        """Testa webhook de pagamento falho."""
        payload = {
            'type': 'charge.failed',
            'data': {
                'code': self.payment_link.id_link,
                'status': 'failed',
                'paid_amount': 0,
            }
        }
        
        with patch('apps.notifications.tasks.send_payment_notification_task.delay') as mock_task:
            response = self.client.post(
                self.webhook_url,
                data=payload,
                format='json'
            )
        
        self.assertEqual(response.status_code, 200)
        
        payment = Payment.objects.filter(payment_link=self.payment_link).first()
        self.assertEqual(payment.status, 'failed')
    
    def test_webhook_payment_refunded(self):
        """Testa webhook de reembolso."""
        # Primeiro cria um pagamento pago
        from django.utils import timezone
        Payment.objects.create(
            payment_link=self.payment_link,
            status='paid',
            amount=self.payment_link.amount,
            payment_date=timezone.now()
        )
        
        payload = {
            'type': 'charge.refunded',
            'data': {
                'code': self.payment_link.id_link,
                'status': 'refunded',
                'paid_amount': 0,
            }
        }
        
        with patch('apps.notifications.tasks.send_payment_notification_task.delay') as mock_task:
            response = self.client.post(
                self.webhook_url,
                data=payload,
                format='json'
            )
        
        self.assertEqual(response.status_code, 200)
        
        payment = Payment.objects.filter(payment_link=self.payment_link).first()
        self.assertEqual(payment.status, 'refunded')
    
    def test_webhook_ignores_non_charge_events(self):
        """Testa que eventos não relacionados a charge são ignorados."""
        payload = {
            'type': 'subscription.created',
            'data': {
                'id': 'sub_123',
            }
        }
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ignorado')
    
    def test_webhook_unknown_charge_returns_error(self):
        """Testa webhook para charge desconhecido retorna erro."""
        payload = {
            'type': 'charge.paid',
            'data': {
                'code': 'lnk_nao_existe',
                'status': 'paid',
                'paid_amount': 10000,
            }
        }
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
    
    def test_webhook_invalid_status(self):
        """Testa webhook com status inválido."""
        payload = {
            'type': 'charge.unknown',
            'data': {
                'code': self.payment_link.id_link,
                'status': 'status_invalido',
                'paid_amount': 10000,
            }
        }
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            format='json'
        )
        
        # Status inválido resulta em erro
        self.assertEqual(response.status_code, 400)
    
    def test_webhook_empty_payload(self):
        """Testa webhook com payload vazio."""
        response = self.client.post(
            self.webhook_url,
            data={},
            format='json'
        )
        
        # Sem 'type', deve ser ignorado
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ignorado')
    
    def test_webhook_enqueues_notification_task(self):
        """Testa que o webhook enfileira task de notificação."""
        payload = {
            'type': 'charge.paid',
            'data': {
                'code': self.payment_link.id_link,
                'status': 'paid',
                'paid_amount': int(self.payment_link.amount * 100),
            }
        }
        
        with patch('apps.notifications.services.payment_notifications.send_payment_notification_task') as mock_task:
            mock_task.delay = MagicMock()
            
            response = self.client.post(
                self.webhook_url,
                data=payload,
                format='json'
            )
            
            # Verifica que a task foi enfileirada com .delay()
            mock_task.delay.assert_called_once_with(
                status='paid',
                phone=f'55{self.seller.phone}',
                amount=float(self.payment_link.amount),
            )
    
    def test_webhook_returns_immediately(self):
        """Testa que webhook retorna imediatamente (não bloqueia)."""
        payload = {
            'type': 'charge.paid',
            'data': {
                'code': self.payment_link.id_link,
                'status': 'paid',
                'paid_amount': int(self.payment_link.amount * 100),
            }
        }
        
        with patch('apps.notifications.services.payment_notifications.send_payment_notification_task') as mock_task:
            mock_task.delay = MagicMock()
            
            response = self.client.post(
                self.webhook_url,
                data=payload,
                format='json'
            )
        
        # Webhook retorna sucesso
        self.assertEqual(response.status_code, 200)
        
        # Pagamento foi criado
        payment = Payment.objects.filter(payment_link=self.payment_link).first()
        self.assertIsNotNone(payment)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class WebhookNotificationTests(TestCase):
    """Testes específicos de disparo de notificações via webhook."""
    
    def setUp(self):
        self.client = APIClient()
        self.seller = Seller.objects.create(
            name="Vendedor Notif",
            phone="11988887777"
        )
        self.order = Order.objects.create(
            name="Pedido Notif",
            value=Decimal('50.00'),
            value_freight=Decimal('5.00'),
            total=Decimal('55.00'),
            status='pending',
            installments=1,
            seller=self.seller,
        )
        self.payment_link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pay.test/notif',
            id_link='lnk_notif_test',
            amount=self.order.total,
            status='active',
        )
        self.webhook_url = '/api/payments/v1/hook/'
    
    def test_paid_status_enqueues_notification(self):
        """Testa que status paid enfileira notificação de sucesso."""
        payload = {
            'type': 'charge.paid',
            'data': {
                'code': self.payment_link.id_link,
                'status': 'paid',
                'paid_amount': int(self.payment_link.amount * 100),
            }
        }
        
        with patch('apps.notifications.services.payment_notifications.send_payment_notification_task') as mock_task:
            mock_task.delay = MagicMock()
            
            self.client.post(self.webhook_url, data=payload, format='json')
            
            mock_task.delay.assert_called_once_with(
                status='paid',
                phone=f'55{self.seller.phone}',
                amount=55.0,
            )
    
    def test_failed_status_enqueues_notification(self):
        """Testa que status failed enfileira notificação de recusa."""
        payload = {
            'type': 'charge.failed',
            'data': {
                'code': self.payment_link.id_link,
                'status': 'failed',
                'paid_amount': 0,
            }
        }
        
        with patch('apps.notifications.services.payment_notifications.send_payment_notification_task') as mock_task:
            mock_task.delay = MagicMock()
            
            self.client.post(self.webhook_url, data=payload, format='json')
            
            mock_task.delay.assert_called_once_with(
                status='failed',
                phone=f'55{self.seller.phone}',
                amount=None,
            )
    
    def test_canceled_status_enqueues_notification(self):
        """Testa que status canceled enfileira notificação de recusa."""
        payload = {
            'type': 'charge.canceled',
            'data': {
                'code': self.payment_link.id_link,
                'status': 'canceled',
                'paid_amount': 0,
            }
        }
        
        with patch('apps.notifications.services.payment_notifications.send_payment_notification_task') as mock_task:
            mock_task.delay = MagicMock()
            
            self.client.post(self.webhook_url, data=payload, format='json')
            
            mock_task.delay.assert_called_once()
    
    def test_pending_status_no_notification(self):
        """Testa que status pending não enfileira notificação."""
        payload = {
            'type': 'charge.pending',
            'data': {
                'code': self.payment_link.id_link,
                'status': 'pending',
                'paid_amount': 0,
            }
        }
        
        with patch('apps.notifications.services.payment_notifications.send_payment_notification_task') as mock_task:
            mock_task.delay = MagicMock()
            
            self.client.post(self.webhook_url, data=payload, format='json')
            
            # Não deve chamar .delay() para status pending
            mock_task.delay.assert_not_called()
    
    def test_seller_without_phone_no_notification(self):
        """Testa que vendedor sem telefone não enfileira notificação."""
        # Criar seller sem telefone
        seller_no_phone = Seller.objects.create(name="Sem Telefone", phone="")
        order_no_phone = Order.objects.create(
            name="Pedido Sem Tel",
            value=Decimal('30.00'),
            value_freight=Decimal('0.00'),
            total=Decimal('30.00'),
            status='pending',
            installments=1,
            seller=seller_no_phone,
        )
        link_no_phone = PaymentLink.objects.create(
            order=order_no_phone,
            url_link='https://pay.test/no-phone',
            id_link='lnk_no_phone',
            amount=order_no_phone.total,
            status='active',
        )
        
        payload = {
            'type': 'charge.paid',
            'data': {
                'code': 'lnk_no_phone',
                'status': 'paid',
                'paid_amount': 3000,
            }
        }
        
        with patch('apps.notifications.services.payment_notifications.send_payment_notification_task') as mock_task:
            mock_task.delay = MagicMock()
            
            response = self.client.post(self.webhook_url, data=payload, format='json')
            
            # Webhook ainda funciona
            self.assertEqual(response.status_code, 200)
            
            # Mas não enfileira mensagem
            mock_task.delay.assert_not_called()


class CeleryTaskTests(TestCase):
    """Testes unitários das tasks Celery de notificação."""
    
    def test_notification_task_paid_calls_service(self):
        """Testa que task de notificação paid chama serviço corretamente."""
        from apps.notifications.tasks import send_payment_notification_task
        
        with patch('apps.notifications.tasks.get_whatsapp_service') as mock_factory:
            mock_service = MagicMock()
            mock_factory.return_value = mock_service
            
            # Executar task diretamente (sem fila)
            send_payment_notification_task(
                status='paid',
                phone='5511999999999',
                amount=100.0
            )
            
            mock_service.send_payment_success_approved.assert_called_once_with(
                phone='5511999999999',
                value=100.0
            )
    
    def test_notification_task_failed_calls_service(self):
        """Testa que task de notificação failed chama serviço corretamente."""
        from apps.notifications.tasks import send_payment_notification_task
        
        with patch('apps.notifications.tasks.get_whatsapp_service') as mock_factory:
            mock_service = MagicMock()
            mock_factory.return_value = mock_service
            
            send_payment_notification_task(
                status='failed',
                phone='5511999999999',
                amount=None
            )
            
            mock_service.send_payment_refused.assert_called_once_with(
                phone='5511999999999'
            )
    
    def test_notification_task_retries_on_error(self):
        """Testa que task faz retry em caso de erro."""
        from apps.notifications.tasks import send_payment_notification_task
        
        with patch('apps.notifications.tasks.get_whatsapp_service') as mock_factory:
            mock_factory.side_effect = RuntimeError("API indisponível")
            
            # Task deve levantar exceção (que causa retry no Celery)
            with self.assertRaises(RuntimeError):
                send_payment_notification_task(
                    status='paid',
                    phone='5511999999999',
                    amount=100.0
                )
