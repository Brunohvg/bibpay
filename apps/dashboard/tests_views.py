from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from apps.sellers.models import Seller
from apps.orders.models import Order
from apps.payments.models import PaymentLink, Payment


class DashboardViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Criar vendedor
        self.seller = Seller.objects.create(name="Vendedor Test", phone="123456789")
        # Criar pedido
        self.order = Order.objects.create(
            name="Pedido Test",
            value=Decimal('10.00'),
            value_freight=Decimal('2.00'),
            total=Decimal('12.00'),
            status='pending',
            installments=1,
            seller=self.seller,
        )
        # Criar link de pagamento
        self.link = PaymentLink.objects.create(
            order=self.order,
            url_link="https://example.com/pay/1",
            id_link="lnk_1",
            amount=self.order.total,
            status="active",
        )

    def test_dashboard_home_renders_and_context(self):
        url = reverse('dashboard:dashboard-home')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Verifica chaves de contexto importantes
        ctx = resp.context
        self.assertIn('total_links_criados', ctx)
        self.assertIn('chart_data', ctx)
        self.assertIn('recent_links', ctx)
        self.assertIn('total_links_ativos', ctx)
        # recent_links deve conter pelo menos o link criado
        recent = ctx['recent_links']
        self.assertTrue(any(item['link'].id == self.link.id for item in recent))
