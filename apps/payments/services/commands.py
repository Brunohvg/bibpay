"""
Módulo de COMMANDS do domínio de Pagamentos.

Responsabilidade:
- Executar ações que ALTERAM estado
- Orquestrar fluxos de escrita
- Garantir consistência transacional
- Aplicar regras de negócio via rules.py

Este arquivo:
✔ escreve no banco
✔ muda status
✔ chama integrações externas
✔ USA rules

Este arquivo NÃO:
✘ faz listagens
✘ faz agregações
✘ decide regras (isso é do rules)
"""

from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from apps.payments.models import Payment, PaymentLink
from apps.core.integrations.pagarme import PagarMePaymentLink

# REGRAS DE NEGÓCIO (DOMÍNIO)
from apps.payments.domain.rules import (
    is_valid_payment_status,
    resolve_payment_link_status,
    resolve_order_status_from_payment,
    can_process_refund,
    can_cancel_payment_link,
    can_cancel_order,
    can_create_approved_payment,
)

# ================================================================
# CRIAÇÃO DE LINK DE PAGAMENTO
# ================================================================

def process_payment_link_for_order(order) -> PaymentLink | None:
    """
    Cria um link de pagamento para um pedido.
    """
    link_data = _generate_payment_link(order)
    if not link_data:
        return None

    return _create_payment_link_record(order, link_data)


def _generate_payment_link(order) -> dict | None:
    """
    Integração com Pagar.me para gerar link de pagamento.
    """
    try:
        pagarme = PagarMePaymentLink(
            customer_name=order.name,
            total_amount=int(order.total * 100),  # centavos
            max_installments=order.installments,
            free_installments=order.installments,
        )

        response = pagarme.create_link()
        if not response:
            return None

        link_id = response.get("id")
        link_url = response.get("url") or response.get("short_url")

        if not link_id or not link_url:
            return None

        return {
            "id": link_id,
            "url": link_url,
        }

    except Exception:
        return None


def _create_payment_link_record(order, link_data: dict) -> PaymentLink | None:
    """
    Persiste o PaymentLink no banco.
    """
    try:
        return PaymentLink.objects.create(
            order=order,
            id_link=link_data["id"],
            url_link=link_data["url"],
            amount=order.total,
            status="active",
            is_active=True,
        )
    except Exception:
        return None


# ================================================================
# WEBHOOK – PROCESSAMENTO DE PAGAMENTO
# ================================================================

def process_payment_webhook(webhook_data: dict) -> Payment | None:
    """
    Processa eventos recebidos via webhook do Pagar.me.

    Fluxo:
    - Identifica PaymentLink
    - Normaliza status
    - Aplica rules
    - Persiste tudo de forma transacional
    """

    data = webhook_data.get("data", {})
    charge_id = data.get("code")

    payment_link = (
        PaymentLink.objects
        .select_related("order")
        .filter(id_link=charge_id)
        .first()
    )
    
    if not payment_link:
        return None

    pagarme_status = data.get("status")

    # Tradução status externo → interno
    payment_status_map = {
        "pending": "pending",
        "processing": "processing",
        "paid": "paid",
        "failed": "failed",
        "canceled": "canceled",
        "refunded": "refunded",
        "chargeback": "chargeback",
        "overpaid": "overpaid",
        "underpaid": "underpaid",
    }

    payment_status = payment_status_map.get(pagarme_status)

    if not payment_status or not is_valid_payment_status(payment_status):
        return None

    amount = Decimal(str(data.get("paid_amount", 0))) / 100
    paid_at = data.get("paid_at") or timezone.now()

    with transaction.atomic():

        # --------------------------------------------------
        # PAYMENT (financeiro)
        # --------------------------------------------------
        payment, created = Payment.objects.get_or_create(
            payment_link=payment_link,
            defaults={
                "status": payment_status,
                "amount": amount,
                "payment_date": paid_at,
            }
        )

        if not created and payment.status != payment_status:
            payment.status = payment_status
            payment.save(update_fields=["status"])

        # --------------------------------------------------
        # PAYMENT LINK (estado do link)
        # --------------------------------------------------
        new_link_status = resolve_payment_link_status(payment_status)
        if new_link_status:
            payment_link.status = new_link_status
            payment_link.save(update_fields=["status"])

        # --------------------------------------------------
        # ORDER (estado comercial)
        # --------------------------------------------------
        order = payment_link.order
        new_order_status = resolve_order_status_from_payment(payment_status)
        if new_order_status:
            order.status = new_order_status
            order.save(update_fields=["status"])

    return payment


# ================================================================
# AÇÕES DIRETAS (COMMANDS SIMPLES)
# ================================================================

def cancel_payment_link(link_id: int) -> bool:
    """
    Cancela manualmente um link de pagamento.
    """
    try:
        link = PaymentLink.objects.get(id=link_id)
        link.status = "canceled"
        link.is_active = False
        link.save(update_fields=["status", "is_active"])
        return True
    except PaymentLink.DoesNotExist:
        return False
