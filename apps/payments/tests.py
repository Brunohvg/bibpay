from django.test import TestCase
from decimal import Decimal
from django.utils import timezone
from apps.payments.models import Payment, PaymentLink
from apps.orders.models import Order
from apps.sellers.models import Seller
from apps.payments.services import (
    create_payment_link_record,
    process_payment_webhook,
    get_payment_status,
    get_payment_links_by_order,
    get_payment_by_link,
    cancel_payment_link,
    list_payments_by_status
)


class PaymentLinkModelTestCase(TestCase):
    """Testes do modelo PaymentLink."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.seller = Seller.objects.create(
            name='Vendedor Teste',
            phone='11999999999'
        )
        self.order = Order.objects.create(
            name='Pedido Teste',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )

    def test_payment_link_creation(self):
        """Testa a criação de um link de pagamento."""
        link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/123',
            id_link='link_123',
            amount=self.order.total,
            status='active'
        )
        self.assertEqual(link.order, self.order)
        self.assertEqual(link.status, 'active')
        self.assertEqual(link.amount, Decimal('110.00'))

    def test_payment_link_status_choices(self):
        """Testa os valores válidos para status do link."""
        statuses = ['active', 'pending', 'inactive', 'expired', 'paid', 'canceled']
        
        for status in statuses:
            link = PaymentLink.objects.create(
                order=self.order,
                url_link=f'https://pagar.me/link/{status}',
                id_link=f'link_{status}',
                amount=self.order.total,
                status=status
            )
            self.assertEqual(link.status, status)

    def test_payment_link_string_representation(self):
        """Testa a representação em string do link de pagamento."""
        link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/123',
            id_link='link_123',
            amount=Decimal('110.00'),
            status='active'
        )
        expected = f'Link {link.id} — Pedido {self.order.id} — R$ 110.00'
        self.assertEqual(str(link), expected)

    def test_payment_link_order_relationship(self):
        """Testa a relação entre PaymentLink e Order."""
        link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/123',
            id_link='link_123',
            amount=self.order.total,
            status='active'
        )
        self.assertEqual(link.order, self.order)
        self.assertIn(link, self.order.payment_links.all())

    def test_payment_link_ordering(self):
        """Testa a ordenação dos links por data de criação (descendente)."""
        link1 = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/1',
            id_link='link_1',
            amount=self.order.total,
            status='active'
        )
        link2 = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/2',
            id_link='link_2',
            amount=self.order.total,
            status='active'
        )
        
        links = list(PaymentLink.objects.all())
        self.assertEqual(links[0], link2)  # Mais recente primeiro
        self.assertEqual(links[1], link1)


class PaymentModelTestCase(TestCase):
    """Testes do modelo Payment."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.seller = Seller.objects.create(
            name='Vendedor Teste',
            phone='11999999999'
        )
        self.order = Order.objects.create(
            name='Pedido Teste',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        self.payment_link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/123',
            id_link='link_123',
            amount=self.order.total,
            status='active'
        )

    def test_payment_creation(self):
        """Testa a criação de um pagamento."""
        payment = Payment.objects.create(
            payment_link=self.payment_link,
            status='paid',
            payment_date=timezone.now(),
            amount=self.order.total
        )
        self.assertEqual(payment.status, 'paid')
        self.assertEqual(payment.amount, Decimal('110.00'))

    def test_payment_status_choices(self):
        """Testa os valores válidos para status do pagamento."""
        statuses = ['pending', 'paid', 'failed', 'canceled', 'refunded', 'chargeback']
        
        payment_links = []
        for i, status in enumerate(statuses):
            link = PaymentLink.objects.create(
                order=self.order,
                url_link=f'https://pagar.me/link/{i}',
                id_link=f'link_{i}',
                amount=self.order.total,
                status='active'
            )
            payment_links.append(link)
            
            payment = Payment.objects.create(
                payment_link=link,
                status=status,
                payment_date=timezone.now(),
                amount=self.order.total
            )
            self.assertEqual(payment.status, status)

    def test_payment_one_to_one_relationship(self):
        """Testa a relação OneToOne entre Payment e PaymentLink."""
        payment = Payment.objects.create(
            payment_link=self.payment_link,
            status='paid',
            payment_date=timezone.now(),
            amount=self.order.total
        )
        
        # Deve ser possível acessar o payment via link
        self.assertEqual(self.payment_link.payment, payment)
        
        # Não deve ser possível criar outro payment para o mesmo link
        with self.assertRaises(Exception):
            Payment.objects.create(
                payment_link=self.payment_link,
                status='paid',
                payment_date=timezone.now(),
                amount=self.order.total
            )

    def test_payment_order_property(self):
        """Testa a propriedade order do Payment."""
        payment = Payment.objects.create(
            payment_link=self.payment_link,
            status='paid',
            payment_date=timezone.now(),
            amount=self.order.total
        )
        self.assertEqual(payment.order, self.order)

    def test_payment_string_representation(self):
        """Testa a representação em string do pagamento."""
        payment = Payment.objects.create(
            payment_link=self.payment_link,
            status='paid',
            payment_date=timezone.now(),
            amount=Decimal('110.00')
        )
        expected = f'Pagamento {payment.id} — Link {self.payment_link.id} — R$ 110.00'
        self.assertEqual(str(payment), expected)

    def test_payment_ordering(self):
        """Testa a ordenação dos pagamentos por data de criação (descendente)."""
        payment1 = Payment.objects.create(
            payment_link=self.payment_link,
            status='paid',
            payment_date=timezone.now(),
            amount=self.order.total
        )
        
        # Criar novo link e pagamento para testar ordenação
        link2 = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/456',
            id_link='link_456',
            amount=self.order.total,
            status='active'
        )
        payment2 = Payment.objects.create(
            payment_link=link2,
            status='paid',
            payment_date=timezone.now(),
            amount=self.order.total
        )
        
        payments = list(Payment.objects.all())
        self.assertEqual(payments[0], payment2)  # Mais recente primeiro
        self.assertEqual(payments[1], payment1)


class PaymentServiceTestCase(TestCase):
    """Testes das funções de serviço do Payment."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.seller = Seller.objects.create(
            name='Vendedor Teste',
            phone='11999999999'
        )
        self.order = Order.objects.create(
            name='Pedido Teste',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )

    def test_create_payment_link_record(self):
        """Testa a criação de registro de link de pagamento."""
        link_data = {
            'id': 'link_123',
            'url': 'https://pagar.me/link/123'
        }
        
        link = create_payment_link_record(self.order, link_data)
        self.assertEqual(link.order, self.order)
        self.assertEqual(link.id_link, 'link_123')
        self.assertEqual(link.status, 'active')

    def test_get_payment_links_by_order(self):
        """Testa a busca de links de pagamento por pedido."""
        # Limpar links existentes criados por signals
        PaymentLink.objects.all().delete()
        
        PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/1',
            id_link='link_1',
            amount=self.order.total,
            status='active'
        )
        PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/2',
            id_link='link_2',
            amount=self.order.total,
            status='active'
        )
        
        links = get_payment_links_by_order(self.order.id)
        self.assertEqual(len(links), 2)

    def test_get_payment_by_link(self):
        """Testa a busca de pagamento por link."""
        link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/123',
            id_link='link_123',
            amount=self.order.total,
            status='active'
        )
        payment = Payment.objects.create(
            payment_link=link,
            status='paid',
            payment_date=timezone.now(),
            amount=self.order.total
        )
        
        fetched_payment = get_payment_by_link(link.id)
        self.assertEqual(fetched_payment, payment)

    def test_list_payments_by_status(self):
        """Testa a listagem de pagamentos por status."""
        link1 = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/1',
            id_link='link_1',
            amount=self.order.total,
            status='active'
        )
        link2 = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/2',
            id_link='link_2',
            amount=self.order.total,
            status='active'
        )
        
        Payment.objects.create(
            payment_link=link1,
            status='paid',
            payment_date=timezone.now(),
            amount=self.order.total
        )
        Payment.objects.create(
            payment_link=link2,
            status='pending',
            payment_date=timezone.now(),
            amount=self.order.total
        )
        
        paid_payments = list_payments_by_status('paid')
        self.assertEqual(len(paid_payments), 1)
        self.assertEqual(paid_payments[0].status, 'paid')
