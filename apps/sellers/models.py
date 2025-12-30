from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel


class Seller(BaseModel):
    """
    Vendedor do sistema.
    
    Pode ter um usuário vinculado para login no painel móvel.
    """
    name = models.CharField(
        max_length=255,
        verbose_name='Nome',
        help_text='Nome do vendedor'
    )
    
    phone = models.CharField(
        max_length=20,
        verbose_name='Telefone',
        help_text='Telefone do vendedor (formato: +5511999999999)',
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Número de telefone inválido. Use formato internacional: +5511999999999'
            )
        ]
    )
    
    # Vinculação com usuário para login
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seller_profile',
        verbose_name='Usuário',
        help_text='Usuário para login no painel do vendedor'
    )
    
    # Percentual de comissão (opcional)
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        verbose_name='% Comissão',
        help_text='Percentual de comissão sobre vendas (0-100)'
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'
        ordering = ['created_at']
        db_table = 'sellers'

