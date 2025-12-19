from integrations.whatsapp import get_evolution_client
from evolutionapi.models.message import TextMessage, QuotedMessage

client = get_evolution_client()



if not client:
    raise RuntimeError("Evolution API indisponível")


# Mensagem simples
message = TextMessage(
    number="5531973121650",
    text="Olá, como você está?. seu burro",
    delay=1000  # delay opcional em ms
)
response = client.messages.send_text('instancia', message, 'token_aqui')
