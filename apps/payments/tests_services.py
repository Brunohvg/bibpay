from django.test import TestCase
from decimal import Decimal
from apps.sellers.models import Seller
from apps.orders.models import Order
from apps.payments.models import PaymentLink, Payment
from apps.payments import services
from django.utils import timezone


class PaymentsServicesTests(TestCase):
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
        links = services.get_payment_links_for_order(self.order)
        self.assertEqual(list(links)[0].id, self.link.id)

    def test_cancel_payment_link(self):
        ok = services.cancel_payment_link(self.link.id)
        self.assertTrue(ok)
        self.link.refresh_from_db()
        self.assertEqual(self.link.status, 'canceled')

    def test_calculate_total_from_links(self):
        total = services.calculate_total_from_links([self.link])
        self.assertEqual(total, Decimal('25.00'))

    def test_get_payment_status_none(self):
        # Ainda não há Payment associado
        self.assertIsNone(services.get_payment_status(9999))

    def test_create_payment_record_via_webhook(self):
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
