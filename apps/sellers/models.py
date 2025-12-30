from django.db import models
from django.core.validators import RegexValidator
from apps.core.models import BaseModel


class Seller(BaseModel):
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
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'
        ordering = ['created_at']
        db_table = 'sellers'
