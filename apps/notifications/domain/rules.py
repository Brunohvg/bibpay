from apps.core.integrations.integration_whatsapp.whatsapp import get_evolution_client

# Singleton global do client
CLIENT = get_evolution_client()


def is_evolution_api_available() -> dict:
    """
    Verifica se o cliente da Evolution API está disponível.
    """
    # Busca instâncias apenas uma vez
    if CLIENT:
        INSTANCES = CLIENT.instances.fetch_instances()
        context = {
            "client": CLIENT,
            "instances": INSTANCES,
        }
        return context.get("client")


def is_valid_phone(phone: str) -> bool:
    return phone.startswith("55") and phone.isdigit()

def value_float_format(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")
