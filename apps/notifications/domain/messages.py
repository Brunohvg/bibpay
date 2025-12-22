# apps/notifications/domain/messages.py

from evolutionapi.models.message import TextMessage

DEFAULT_DELAY_MS = 1000


def build_payment_link_success_message(*, phone: str, link: str, value: float) -> TextMessage:
    return TextMessage(
        number=phone,
        text=(
            "🛒 *Pedido criado com sucesso!*\n\n"
            f"Finalize seu pagamento no valor de *R$ {value:.2f}*.\nPelo link abaixo:\n\n"
            f"*{link}*"
        ),
        delay=DEFAULT_DELAY_MS,
    )


def build_payment_approved_message(*, phone: str, value: float) -> TextMessage:
    return TextMessage(
        number=phone,
        text=(
            "✅ *Pagamento confirmado!*\n\n"
            f"Recebemos seu pagamento no valor de R$ *{value:.2f}*.\n"
            "Seu pedido está sendo processado."
        ),
        delay=DEFAULT_DELAY_MS,
    )


def build_payment_link_failed_message(*, phone: str) -> TextMessage:
    return TextMessage(
        number=phone,
        text=(
            "❌ *Falha ao gerar pagamento*\n\n"
            "Não foi possível gerar seu link de pagamento no momento."
        ),
        delay=DEFAULT_DELAY_MS,
    )


def build_payment_refused_message(*, phone: str) -> TextMessage:
    return TextMessage(
        number=phone,
        text=(
            "⚠️ *Pagamento recusado*\n\n"
            "Tente novamente ou utilize outro meio de pagamento."
        ),
        delay=DEFAULT_DELAY_MS,
    )
