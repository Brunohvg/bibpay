# apps/notifications/tasks.py
"""
Tasks Celery para envio assíncrono de notificações.

Configurado com:
- Retry automático (3 tentativas)
- Backoff exponencial (5s, 10s, 20s)
- Logging detalhado
"""
import logging
from celery import shared_task

from apps.notifications.services.factory import get_whatsapp_service

logger = logging.getLogger("notifications")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_backoff_max=60,
    retry_kwargs={"max_retries": 3},
    ignore_result=True,
)
def send_payment_notification_task(self, status: str, phone: str, amount: float = None):
    """
    Task assíncrona para enviar notificação de pagamento via WhatsApp.
    
    Args:
        status: Status do pagamento (paid, failed, canceled, etc.)
        phone: Telefone do destinatário (formato: 5511999999999)
        amount: Valor do pagamento (opcional, usado para status 'paid')
    """
    logger.info(f"[Task] Processando notificação: status={status}, phone={phone}")
    
    try:
        service = get_whatsapp_service()
    except RuntimeError as e:
        logger.error(f"[Task] WhatsApp indisponível: {e}")
        raise  # Vai fazer retry
    
    try:
        if status == "paid" and amount is not None:
            service.send_payment_success_approved(phone=phone, value=amount)
            logger.info(f"[Task] Mensagem de sucesso enviada para {phone}")
            
        elif status in {"failed", "canceled", "refunded", "chargeback"}:
            service.send_payment_refused(phone=phone)
            logger.info(f"[Task] Mensagem de recusa enviada para {phone}")
            
        else:
            logger.debug(f"[Task] Status {status} não requer notificação")
            
    except Exception as e:
        logger.error(f"[Task] Erro ao enviar mensagem: {e}")
        raise  # Vai fazer retry


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 3},
    ignore_result=True,
)
def send_payment_link_task(self, phone: str, link: str, value: float):
    """
    Task assíncrona para enviar link de pagamento via WhatsApp.
    """
    logger.info(f"[Task] Enviando link de pagamento para {phone}")
    
    try:
        service = get_whatsapp_service()
        service.send_payment_link_successful(phone=phone, value=value, link=link)
        logger.info(f"[Task] Link enviado com sucesso para {phone}")
    except Exception as e:
        logger.error(f"[Task] Erro ao enviar link: {e}")
        raise
