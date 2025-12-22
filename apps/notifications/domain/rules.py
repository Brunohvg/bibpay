from apps.core.integrations.integration_whatsapp.evolution_service import CLIENT

def is_evolution_api_available() -> str:
    """
    Verifica se o cliente da Evolution API está disponível.
    """
    if CLIENT is None:
        return False
    
    return CLIENT
