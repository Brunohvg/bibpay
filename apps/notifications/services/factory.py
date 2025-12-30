# apps/notifications/services/whatsapp_factory.py

from decouple import config
from apps.core.integrations.integration_whatsapp.client import get_client
from apps.notifications.services.commands import WhatsAppMessageService


def get_whatsapp_service() -> WhatsAppMessageService:
    """
    Factory oficial para criar o WhatsAppMessageService.
    Centraliza configurações e dependências.
    
    Raises:
        RuntimeError: Se a Evolution API não estiver disponível
        ValueError: Se as configurações de instância estiverem faltando
    """
    client = get_client()

    if not client:
        raise RuntimeError("Evolution API indisponível")
    
    instance_id = config("EVOLUTION_INSTANCE_ID", default="")
    instance_token = config("EVOLUTION_INSTANCE_TOKEN", default="")
    
    if not instance_id or not instance_token:
        raise RuntimeError("Configuração EVOLUTION_INSTANCE_ID ou EVOLUTION_INSTANCE_TOKEN não definida")

    return WhatsAppMessageService(
        client=client,
        instance_id=instance_id,
        instance_token=instance_token,
    )