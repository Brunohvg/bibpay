"""
Serviços para gerenciamento de notificações.

Este módulo fornece funções para criar, marcar como lida e buscar notificações.
"""

from django.utils import timezone
from apps.notifications.models import Notification, NotificationType


class NotificationService:
    """Serviço para gerenciar notificações do sistema."""
    
    @staticmethod
    def create_notification(user, title, message, notification_type=NotificationType.INFO):
        """
        Cria uma nova notificação para um usuário.
        
        Args:
            user: Usuário que receberá a notificação
            title: Título da notificação
            message: Mensagem da notificação
            notification_type: Tipo da notificação (INFO, SUCCESS, WARNING, ERROR)
        
        Returns:
            Notification: Notificação criada
        
        Example:
            >>> from django.contrib.auth.models import User
            >>> user = User.objects.first()
            >>> NotificationService.create_notification(
            ...     user=user,
            ...     title="Pagamento Recebido",
            ...     message="Seu pagamento de R$ 100,00 foi confirmado",
            ...     notification_type=NotificationType.SUCCESS
            ... )
        """
        return Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type
        )
    
    @staticmethod
    def mark_as_read(notification_id):
        """
        Marca uma notificação como lida.
        
        Args:
            notification_id: ID da notificação
        
        Returns:
            Notification: Notificação atualizada
        
        Raises:
            Notification.DoesNotExist: Se a notificação não existir
        """
        notification = Notification.objects.get(id=notification_id)
        notification.mark_as_read()
        return notification
    
    @staticmethod
    def mark_all_as_read(user):
        """
        Marca todas as notificações de um usuário como lidas.
        
        Args:
            user: Usuário
        
        Returns:
            int: Número de notificações marcadas como lidas
        """
        count = Notification.objects.filter(
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        return count
    
    @staticmethod
    def get_unread_notifications(user):
        """
        Retorna todas as notificações não lidas de um usuário.
        
        Args:
            user: Usuário
        
        Returns:
            QuerySet: Notificações não lidas
        """
        return Notification.objects.filter(user=user, is_read=False)
    
    @staticmethod
    def get_unread_count(user):
        """
        Retorna o número de notificações não lidas de um usuário.
        
        Args:
            user: Usuário
        
        Returns:
            int: Número de notificações não lidas
        """
        return Notification.objects.filter(user=user, is_read=False).count()
    
    @staticmethod
    def get_recent_notifications(user, limit=10):
        """
        Retorna as notificações mais recentes de um usuário.
        
        Args:
            user: Usuário
            limit: Número máximo de notificações a retornar
        
        Returns:
            QuerySet: Notificações recentes
        """
        return Notification.objects.filter(user=user)[:limit]
