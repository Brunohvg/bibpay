# =================================================================
# ARQUIVO COMPLETO: apps/payments/services.py
# =================================================================

from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone

from apps.payments.models import PaymentLink, Payment

# Integração Pagar.me
from apps.core.integrations.pagarme import PagarMePaymentLink


# ================================================================
# CRIAÇÃO DE LINK DE PAGAMENTO
# ================================================================

def process_payment_link_for_order(order):
    """
    Gera um link de pagamento via Pagar.me e salva no banco.
    """
    try:
        link_data = generate_payment_link(order)
        if not link_data:
            print(f"✗ Erro ao gerar link para Order {order.id}")
            return None

        payment_link = create_payment_link_record(order, link_data)
        if not payment_link:
            print(f"✗ Erro ao salvar PaymentLink da Order {order.id}")
            return None

        print(f"✓ PaymentLink criado: {payment_link.url_link}")
        return payment_link

    except Exception as e:
        print(f"✗ Erro inesperado ao criar PaymentLink: {e}")
        return None


def generate_payment_link(order):
    """
    Chama a API do Pagar.me para gerar o link de pagamento.
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

    except Exception as e:
        print(f"✗ Erro API Pagar.me: {e}")
        return None


def create_payment_link_record(order, link_data):
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
    except Exception as e:
        print(f"✗ Erro ao salvar PaymentLink: {e}")
        return None


# ================================================================
# WEBHOOK – PROCESSAMENTO DE PAGAMENTO
# ================================================================

def process_payment_webhook(webhook_data):
    """
    Processa eventos do webhook do Pagar.me.
    Garante:
    - Um Payment por PaymentLink (OneToOne)
    - Sincronização de status (Payment, PaymentLink e Order)
    """
    try:
        data = webhook_data.get("data", {})
        charge_id = data.get("id")

        payment_link = PaymentLink.objects.filter(id_link=charge_id).first()
        if not payment_link:
            print(f"✗ PaymentLink não encontrado: {charge_id}")
            return None

        status_map = {
            "paid": "paid",
            "pending": "pending",
            "canceled": "canceled",
            "failed": "failed",
            "refunded": "refunded",
            "chargeback": "chargeback",
            "inactive": "inactive",
        }

        payment_status = status_map.get(data.get("status"), "pending")

        with transaction.atomic():

            payment, created = Payment.objects.get_or_create(
                payment_link=payment_link,
                defaults={
                    "status": payment_status,
                    "amount": Decimal(str(data.get("amount", 0))) / 100,
                    "payment_date": data.get("paid_at") or timezone.now(),
                }
            )

            # Atualiza Payment se já existir
            if not created and payment.status != payment_status:
                payment.status = payment_status
                payment.save(update_fields=["status"])

            # Atualiza PaymentLink
            final_statuses = ["paid", "canceled", "failed", "refunded", "chargeback"]

            if payment_status in final_statuses:
                payment_link.status = payment_status
                payment_link.is_active = False
                payment_link.save(update_fields=["status", "is_active"])

            # Atualiza Order
            order = payment_link.order
            if payment_status == "paid":
                order.status = "paid"
            elif payment_status in ["canceled", "failed", "refunded", "chargeback"]:
                order.status = "canceled"

            order.save(update_fields=["status"])

        print(f"✓ Payment {'criado' if created else 'atualizado'} | {payment_status}")
        return payment

    except Exception as e:
        print(f"✗ Erro webhook: {e}")
        return None


# ================================================================
# CONSULTAS / LISTAGENS
# ================================================================

def get_payment_links_for_order(order):
    return PaymentLink.objects.filter(
        order=order,
        is_active=True,
        is_deleted=False
    )


def list_active_payment_links():
    return PaymentLink.objects.filter(
        status="active",
        is_active=True,
        is_deleted=False
    )


def list_payments(**filters):
    qs = Payment.objects.filter(is_active=True, is_deleted=False)
    if filters:
        qs = qs.filter(**filters)
    return qs


def calculate_total_from_links(objects):
    total = Decimal("0")
    for obj in objects:
        if obj.amount:
            total += Decimal(obj.amount)
    return total


def get_payment_statistics(start_date=None, end_date=None):
    qs = Payment.objects.all()

    if start_date:
        qs = qs.filter(payment_date__gte=start_date)
    if end_date:
        qs = qs.filter(payment_date__lte=end_date)

    return qs.aggregate(
        total_paid=Sum("amount", filter=Q(status="paid")) or Decimal("0"),
        total_pending=Sum("amount", filter=Q(status="pending")) or Decimal("0"),
        total_canceled=Sum("amount", filter=Q(status="canceled")) or Decimal("0"),
        total_failed=Sum("amount", filter=Q(status="failed")) or Decimal("0"),
        count_paid=Count("id", filter=Q(status="paid")),
        count_pending=Count("id", filter=Q(status="pending")),
        count_canceled=Count("id", filter=Q(status="canceled")),
        count_failed=Count("id", filter=Q(status="failed")),
    )


# ================================================================
# AUXILIARES
# ================================================================

def get_payment_status(payment_id):
    try:
        return Payment.objects.get(id=payment_id).status
    except Payment.DoesNotExist:
        return None


def get_payment_links_by_order(order_id):
    return PaymentLink.objects.filter(
        order_id=order_id,
        is_deleted=False
    )


def get_payment_by_link(link_id):
    try:
        return PaymentLink.objects.get(id=link_id).payment
    except PaymentLink.DoesNotExist:
        return None


def cancel_payment_link(link_id):
    try:
        link = PaymentLink.objects.get(id=link_id)
        link.status = "canceled"
        link.is_active = False
        link.save(update_fields=["status", "is_active"])
        return True
    except PaymentLink.DoesNotExist:
        return False


def list_payments_by_status(status):
    return Payment.objects.filter(
        status=status,
        is_deleted=False
    )
