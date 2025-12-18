# =================================================================
# apps/orders/models.py (Sem Alterações)
# =================================================================
from django.db import models
from apps.core.models import BaseModel
from apps.sellers.models import Seller
from apps.orders.utils import formatar_valor


STATUS_CHOICES = (
    ('pending', 'Pendente'),
    ('paid', 'Pago'),
    ('failed', 'Falhou'),
    ('canceled', 'Cancelado'),
)


class Order(BaseModel):
    name = models.CharField(max_length=255, verbose_name='Nome', help_text='Nome do pedido')
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor', help_text='Valor do pedido')
    value_freight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor do frete', help_text='Valor do frete')
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total', help_text='Total do pedido')     
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, verbose_name='Status', help_text='Status do pedido')
    installments = models.IntegerField(default=1, verbose_name='Parcelas', help_text='Parcelas do pedido')
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, verbose_name='Vendedor', help_text='Vendedor do pedido')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Sempre manter como Decimal
        self.value = formatar_valor(self.value)
        self.value_freight = formatar_valor(self.value_freight)

        # Soma continua Decimal
        self.total = self.value + self.value_freight

        super().save(*args, **kwargs)


    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']
        db_table = 'orders'