from apps.core.integrations.integration_whatsapp.whatsapp import get_evolution_client

CLIENT = get_evolution_client()


def get_client():
    return CLIENT
