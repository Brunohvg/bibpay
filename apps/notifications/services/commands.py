from evolutionapi.models.message import TextMessage
from apps.notifications.domain.rules import is_evolution_api_available

CLIENT = is_evolution_api_available()
# Mensagem simples
message = TextMessage(
    number="5531973121650",
    text="Olá, como você está agora?",
    delay=1000  # delay opcional em ms
)

CLIENT.messages.send_text(
    instance_id="bibelo",
    message=message,
    instance_token="18CD0780EC1F-4ABB-B83B-D170064554DB",
)

