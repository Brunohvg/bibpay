"""
Módulo de serviços de Pagamentos.

Exporta as funções de Commands (escrita) e Queries (leitura).
"""

# COMMANDS - Escrita
from apps.payments.services.commands import (
    process_payment_link_for_order,
    process_payment_webhook,
    cancel_payment_link,
)

# QUERIES - Leitura
from apps.payments.services.queries import (
    get_payment_links_for_order,
    list_active_payment_links,
    list_payments,
    list_payments_by_status,
    calculate_total_from_links,
    get_payment_statistics,
)


# Funções auxiliares que os testes esperam
def get_payment_status(payment_id):
    """Retorna o status de um pagamento pelo ID do PaymentLink."""
    from apps.payments.models import Payment
    try:
        payment = Payment.objects.get(payment_link_id=payment_id)
        return payment.status
    except Payment.DoesNotExist:
        return None


def get_payment_by_link(link_id):
    """Retorna o Payment associado a um PaymentLink."""
    from apps.payments.models import Payment
    try:
        return Payment.objects.get(payment_link_id=link_id)
    except Payment.DoesNotExist:
        return None
