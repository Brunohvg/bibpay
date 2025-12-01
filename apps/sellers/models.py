from django.db import models
from apps.core.models import BaseModel


class Seller(BaseModel):
    name = models.CharField(max_length=255, verbose_name='Nome', help_text='Nome do vendedor')
    phone = models.CharField(max_length=255, verbose_name='Telefone', help_text='Telefone do vendedor')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'
        ordering = ['created_at']
        db_table = 'sellers'
    
    
