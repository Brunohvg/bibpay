"""
Regras de negócio do domínio de Pagamentos.

Responsabilidade:
- Decidir transições de estado
- Traduzir eventos financeiros em estados do sistema
- NÃO acessar banco
- NÃO chamar APIs
- NÃO ter efeitos colaterais
"""


# ================================================================
# STATUS DE PAGAMENTO
# ================================================================

VALID_PAYMENT_STATUSES = {
    "pending",
    "processing",
    "paid",
    "failed",
    "canceled",
    "refunded",
    "chargeback",
    "overpaid",
    "underpaid",
}


def is_valid_payment_status(status: str) -> bool:
    """
    Verifica se o status de pagamento é reconhecido pelo sistema.
    """
    return status in VALID_PAYMENT_STATUSES


# ================================================================
# TRANSIÇÃO DE STATUS DO LINK
# ================================================================

def resolve_payment_link_status(payment_status: str) -> str | None:
    """
    Decide o novo status do PaymentLink com base no status do pagamento.

    Retorna:
    - "used"
    - "canceled"
    - None (quando não deve alterar)
    """
    if payment_status in {"paid", "overpaid", "underpaid"}:
        return "used"

    if payment_status in {"failed", "canceled"}:
        return "canceled"

    return None


# ================================================================
# TRANSIÇÃO DE STATUS DO PEDIDO
# ================================================================

def resolve_order_status_from_payment(payment_status: str) -> str | None:
    """
    Decide o novo status do pedido a partir do status do pagamento.

    Retorna:
    - "paid"
    - "canceled"
    - None (quando não deve alterar)
    """
    if payment_status in {"paid", "overpaid", "underpaid"}:
        return "paid"

    if payment_status in {"failed", "canceled", "refunded", "chargeback"}:
        return "canceled"

    return None

def can_process_refund(payment_status: str) -> bool:
    """
    Verifica se um pagamento com o status fornecido pode ser reembolsado.

    Apenas pagamentos com status "paid" ou "overpaid" podem ser reembolsados.
    """
    return payment_status in {"paid", "overpaid"}

def can_cancel_payment_link(link_status: str) -> bool:
    """
    Verifica se um link de pagamento com o status fornecido pode ser cancelado.

    Apenas links com status "active" podem ser cancelados.
    """
    return link_status == "active"  

def can_cancel_order(order_status: str) -> bool:
    """
    Verifica se um pedido com o status fornecido pode ser cancelado.

    Apenas pedidos com status "pending" podem ser cancelados.
    """
    return order_status == "pending"  

def can_create_approved_payment(link_status: str) -> bool:
    """
    Verifica se um link de pagamento com o status fornecido pode criar um pagamento aprovado.

    Apenas links com status diferente de "expired" ou "canceled" podem criar pagamentos aprovados.
    """
    return link_status not in {"expired", "canceled", "used"}

