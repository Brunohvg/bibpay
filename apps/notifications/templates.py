# apps/notifications/templates.py

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
