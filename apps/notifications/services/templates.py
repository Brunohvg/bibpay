from evolutionapi.models.message import TextMessage

# Mensagem simples
message = TextMessage(
    number="5511999999999",
    text="Olá, como você está?",
    delay=1000  # delay opcional em ms
)


def payment_link_message(link: str) -> str:
    return f"""
💳 *Link de pagamento*
Clique abaixo para pagar:
{link}
"""

def payment_confirmed_message(value: float) -> str:
    return f"""
✅ *Pagamento confirmado*
Valor: R$ {value:.2f}
Obrigado!
"""

def generic_notification_message(content: str) -> str:
    return f"""
🔔 *Notificação*

{content}
""" 

def alert_message(title: str, body: str) -> str:
    return f"""
🚨 *{title}*
{body}
"""