# apps/notifications/services/commands.py

import logging

from evolutionapi.models.message import TextMessage
from apps.core.integrations.integration_whatsapp.evolution_service import CLIENT
from apps.notifications import templates

logger = logging.getLogger("integrations")


def send_payment_link_notification(
    *,
    phone: str,
    link: str,
    instance_id: str,
) -> None:
    """
    Envia link de pagamento via WhatsApp.
    """

    if not CLIENT:
        logger.error("Evolution API indisponível")
        return

    CLIENT.messages.send_message(
        instance_id=instance_id,
        to=phone,
        message=TextMessage(
            text=templates.payment_link_message(link)
        ),
    )


def send_payment_confirmed_notification(
    *,
    phone: str,
    value: float,
    instance_id: str,
) -> None:
    """
    Envia confirmação de pagamento via WhatsApp.
    """

    if not CLIENT:
        logger.error("Evolution API indisponível")
        return

    CLIENT.messages.send_message(
        instance_id=instance_id,
        to=phone,
        message=TextMessage(
            text=templates.payment_confirmed_message(value)
        ),
    )
