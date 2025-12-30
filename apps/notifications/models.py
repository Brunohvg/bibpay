from django.db import models
from django.contrib.auth.models import User
from apps.core.models import BaseModel


class NotificationType(models.TextChoices):
    """Tipos de notificação disponíveis."""
    INFO = 'info', 'Informação'
    SUCCESS = 'success', 'Sucesso'
    WARNING = 'warning', 'Aviso'
    ERROR = 'error', 'Erro'


class Notification(BaseModel):
    """
    Modelo para notificações do sistema.
    
    Permite enviar notificações para usuários sobre eventos importantes
    como pagamentos recebidos, pedidos criados, etc.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Usuário',
        help_text='Usuário que receberá a notificação'
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name='Título',
        help_text='Título da notificação'
    )
    
    message = models.TextField(
        verbose_name='Mensagem',
        help_text='Conteúdo da notificação'
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        verbose_name='Tipo',
        help_text='Tipo de notificação (info, success, warning, error)'
    )
    
    is_read = models.BooleanField(
        default=False,
        verbose_name='Lida',
        help_text='Indica se a notificação foi lida'
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Lida em',
        help_text='Data e hora em que a notificação foi lida'
    )
    
    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Marca a notificação como lida."""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
