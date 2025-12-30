"""
Serviço de notificações de pagamento via WhatsApp.

Responsável por enviar mensagens ao cliente quando o status do pagamento muda.
Usa Celery para processamento assíncrono (não bloqueia o webhook).
"""
import logging

from apps.notifications.tasks import send_payment_notification_task

logger = logging.getLogger("notifications")


def payment_status(*, payment):
    """
    Enfileira notificação de mudança de status do pagamento.
    
    Despacha para fila Celery - não bloqueia o webhook.
    """
    order = payment.payment_link.order
    phone = order.seller.phone
    
    if not phone:
        logger.warning(f"Seller sem telefone cadastrado, pedido {order.id}")
        return
    
    status = payment.status
    phone_formatted = f"55{phone}"
    
    # Status que não precisam de notificação
    if status in {"pending", "processing"}:
        logger.debug(f"Status {status} - não notificar")
        return
    
    logger.info(f"Enfileirando notificação: status={status}, pedido={order.id}")
    
    # Despachar para fila Celery (assíncrono)
    amount = float(payment.amount) if status == "paid" else None
    
    send_payment_notification_task.delay(
        status=status,
        phone=phone_formatted,
        amount=amount,
    )
