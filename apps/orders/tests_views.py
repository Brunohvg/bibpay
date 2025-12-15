from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal

from apps.sellers.models import Seller
from apps.orders.models import Order


class OrdersViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.seller = Seller.objects.create(name="Seller A", phone="000")
        # Criar alguns pedidos
        for i in range(3):
            Order.objects.create(
                name=f"Pedido {i}",
                value=Decimal('5.00'),
                value_freight=Decimal('1.00'),
                total=Decimal('6.00'),
                status='pending',
                installments=1,
                seller=self.seller,
            )

    def test_order_create_get(self):
        url = reverse('orders:order-create')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('sellers', resp.context)
        self.assertIn('orders', resp.context)

    def test_order_list_view(self):
        url = reverse('orders:order-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('orders', resp.context)
        self.assertIn('sellers', resp.context)
