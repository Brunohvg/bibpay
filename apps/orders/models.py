# =================================================================
# apps/orders/models.py
# =================================================================
from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import BaseModel
from apps.sellers.models import Seller


STATUS_CHOICES = (
    ('pending', 'Pendente'),
    ('paid', 'Pago'),
    ('failed', 'Falhou'),
    ('canceled', 'Cancelado'),
)


class Order(BaseModel):
    name = models.CharField(
        max_length=255,
        verbose_name='Nome',
        help_text='Nome do pedido'
    )
    
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor',
        help_text='Valor do pedido',
        validators=[MinValueValidator(0)]
    )
    
    value_freight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor do frete',
        help_text='Valor do frete',
        validators=[MinValueValidator(0)]
    )
    
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Total',
        help_text='Total do pedido',
        validators=[MinValueValidator(0)]
    )
    
    status = models.CharField(
        max_length=255,
        choices=STATUS_CHOICES,
        verbose_name='Status',
        help_text='Status do pedido',
        db_index=True  # Índice para melhor performance em queries
    )
    
    installments = models.IntegerField(
        default=1,
        verbose_name='Parcelas',
        help_text='Parcelas do pedido',
        validators=[MinValueValidator(1)]
    )
    
    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        verbose_name='Vendedor',
        help_text='Vendedor do pedido'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']
        db_table = 'orders'