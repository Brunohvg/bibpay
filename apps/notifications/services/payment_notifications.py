"""
Serviço de notificações de pagamento via WhatsApp.

Responsável por enviar mensagens ao cliente quando o status do pagamento muda.
"""
import logging

from apps.notifications.services.factory import get_whatsapp_service

logger = logging.getLogger("notifications")


def payment_status(*, payment):
    """
    Envia notificação de mudança de status do pagamento.
    
    Não lança exceção para evitar quebrar o fluxo do webhook.
    """
    try:
        service = get_whatsapp_service()
    except RuntimeError as e:
        logger.warning(f"WhatsApp indisponível, notificação não enviada: {e}")
        return
    
    order = payment.payment_link.order
    phone = order.seller.phone
    
    if not phone:
        logger.warning(f"Seller sem telefone cadastrado, pedido {order.id}")
        return
    
    status = payment.status
    phone_formatted = f"55{phone}"
    
    logger.info(f"Enviando notificação: status={status}, pedido={order.id}")
    
    try:
        if status == "paid":
            service.send_payment_success_approved(
                phone=phone_formatted,
                value=payment.amount
            )
        elif status == "pending":
            # Pagamento criado, aguardando confirmação
            logger.debug(f"Status pending - não notificar ainda")
        elif status == "processing":
            # Em processamento - não notificar
            logger.debug(f"Status processing - aguardando conclusão")
        elif status in {"failed", "canceled"}:
            service.send_payment_refused(phone=phone_formatted)
        elif status in {"refunded", "chargeback"}:
            service.send_payment_refused(phone=phone_formatted)
        else:
            logger.warning(f"Status desconhecido: {status}")
            
    except Exception as e:
        # Log do erro mas não propaga - webhook deve continuar funcionando
        logger.error(f"Erro ao enviar notificação WhatsApp: {e}", exc_info=True)
