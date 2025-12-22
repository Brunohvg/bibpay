# apps/notifications/services/whatsapp_factory.py

from decouple import config
from apps.core.integrations.integration_whatsapp.client import get_client
from apps.notifications.services.commands import WhatsAppMessageService


def get_whatsapp_service() -> WhatsAppMessageService:
    """
    Factory oficial para criar o WhatsAppMessageService.
    Centraliza configurações e dependências.
    """
    client = get_client()

    if not client:
        raise RuntimeError("Evolution API indisponível")

    return WhatsAppMessageService(
        client=client,
        instance_id=config("EVOLUTION_INSTANCE_ID"),
        instance_token=config("EVOLUTION_INSTANCE_TOKEN"),
    )