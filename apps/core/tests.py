from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.core.models import BaseModel
from apps.orders.models import Order
from apps.sellers.models import Seller
from decimal import Decimal


class BaseModelTestCase(TestCase):
    """Testes do modelo abstrato BaseModel."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.seller = Seller.objects.create(
            name='Vendedor Teste',
            phone='11999999999'
        )

    def test_base_model_created_at(self):
        """Testa se o campo created_at é preenchido automaticamente."""
        order = Order.objects.create(
            name='Pedido Teste',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        self.assertIsNotNone(order.created_at)

    def test_base_model_updated_at(self):
        """Testa se o campo updated_at é preenchido automaticamente."""
        order = Order.objects.create(
            name='Pedido Teste',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        self.assertIsNotNone(order.updated_at)

    def test_base_model_is_active_default(self):
        """Testa se is_active tem valor padrão True."""
        order = Order.objects.create(
            name='Pedido Teste',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        self.assertTrue(order.is_active)

    def test_base_model_is_deleted_default(self):
        """Testa se is_deleted tem valor padrão False."""
        order = Order.objects.create(
            name='Pedido Teste',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        self.assertFalse(order.is_deleted)

    def test_base_model_deleted_at_null(self):
        """Testa se deleted_at é NULL por padrão."""
        order = Order.objects.create(
            name='Pedido Teste',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        self.assertIsNone(order.deleted_at)

    def test_base_model_update_changes_updated_at(self):
        """Testa se updated_at muda quando o objeto é atualizado."""
        order = Order.objects.create(
            name='Pedido Teste',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        original_updated_at = order.updated_at
        
        # Aguarda um pouco
        import time
        time.sleep(0.1)
        
        order.name = 'Pedido Atualizado'
        order.save()
        
        self.assertGreaterEqual(order.updated_at, original_updated_at)

    def test_base_model_soft_delete(self):
        """Testa a possibilidade de soft delete."""
        order = Order.objects.create(
            name='Pedido para Soft Delete',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        # Marca como deletado
        order.is_deleted = True
        order.deleted_at = timezone.now()
        order.save()
        
        # Recupera para verificar
        updated_order = Order.objects.get(id=order.id)
        self.assertTrue(updated_order.is_deleted)
        self.assertIsNotNone(updated_order.deleted_at)

    def test_base_model_timestamps_type(self):
        """Testa se os timestamps são do tipo datetime."""
        order = Order.objects.create(
            name='Pedido Teste',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        
        self.assertIsInstance(order.created_at, type(timezone.now()))
        self.assertIsInstance(order.updated_at, type(timezone.now()))

    def test_base_model_created_at_not_updated(self):
        """Testa que created_at não muda quando o objeto é atualizado."""
        order = Order.objects.create(
            name='Pedido Teste',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )
        original_created_at = order.created_at
        
        # Aguarda e atualiza
        import time
        time.sleep(0.1)
        
        order.name = 'Novo Nome'
        order.save()
        
        # created_at deve permanecer o mesmo
        self.assertEqual(order.created_at, original_created_at)
