"""
Modelos do app Sales - Vendas Diárias.

Responsável por armazenar os lançamentos de vendas dos vendedores.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator

from apps.core.models import BaseModel
from apps.sellers.models import Seller


class DailySale(BaseModel):
    """
    Registro de venda diária de um vendedor.
    
    Cada vendedor pode ter apenas 1 lançamento por dia (unique_together).
    """
    seller = models.ForeignKey(
        Seller,
        on_delete=models.PROTECT,
        related_name='daily_sales',
        verbose_name='Vendedor'
    )
    
    date = models.DateField(
        verbose_name='Data',
        help_text='Data da venda',
        db_index=True
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor',
        help_text='Valor total vendido no dia',
        validators=[MinValueValidator(0)]
    )
    
    notes = models.TextField(
        verbose_name='Observações',
        help_text='Observações sobre as vendas do dia (opcional)',
        blank=True,
        null=True
    )
    
    def __str__(self):
        return f"{self.seller.name} - {self.date} - R$ {self.amount}"
    
    def clean(self):
        """Validações customizadas."""
        super().clean()
        
        # Não permitir datas futuras
        if self.date and self.date > timezone.now().date():
            raise ValidationError({
                'date': 'Não é permitido lançar vendas para datas futuras.'
            })
        
        # Valor deve ser positivo
        if self.amount and self.amount <= 0:
            raise ValidationError({
                'amount': 'O valor da venda deve ser maior que zero.'
            })
    
    class Meta:
        verbose_name = 'Venda Diária'
        verbose_name_plural = 'Vendas Diárias'
        ordering = ['-date', 'seller__name']
        db_table = 'daily_sales'
        
        # Garantir apenas 1 venda por dia por vendedor
        constraints = [
            models.UniqueConstraint(
                fields=['seller', 'date'],
                name='unique_seller_date'
            )
        ]
        
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['seller', 'date']),
        ]
