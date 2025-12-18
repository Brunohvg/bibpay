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

""""
{
  "id": "hook_G9VNgX2i4CLJnX4Q",
  "account": {
    "id": "acc_6XgnEXwu8tN51xOd",
    "name": "LOJA BIBELÔ"
  },
  "type": "charge.paid",
  "created_at": "2025-12-18T14:47:08.9346361Z",
  "data": {
    "amount": 38940,
    "code": "pl_pWy9k1ObMo2z3VZSX2Tpbgr3dZB5Q0qL",
    "created_at": "2025-12-18T14:46:53",
    "currency": "BRL",
    "customer": {
      "address": {
        "city": "Belo Horizonte",
        "country": "BR",
        "created_at": "2025-12-18T14:46:52",
        "id": "addr_e4W6KGxIG0tRav8Y",
        "line_1": "676, Avenida General Olímpio Mourão Filho, Itapoã",
        "neighborhood": "Itapoã",
        "number": "676",
        "state": "MG",
        "status": "active",
        "street": "Avenida General Olímpio Mourão Filho",
        "updated_at": "2025-12-18T14:46:52",
        "zip_code": "31710-690"
      },
      "created_at": "2025-12-18T14:45:53",
      "delinquent": false,
      "document": "87543010682",
      "document_type": "cpf",
      "email": "andreamarquesgarcia2017@gmail.com",
      "id": "cus_gpAx8ylCxCd0r0Wv",
      "name": "Andrea Marques da",
      "phones": {
        "mobile_phone": {
          "area_code": "31",
          "country_code": "55",
          "number": "994558666"
        }
      },
      "type": "individual",
      "updated_at": "2025-12-18T14:46:52"
    },
    "gateway_id": "4215644227",
    "id": "ch_a59b0d7HDwf218AG",
    "last_transaction": {
      "acquirer_auth_code": "075433",
      "acquirer_message": "Transação aprovada com sucesso",
      "acquirer_name": "pagarme",
      "acquirer_nsu": "4215644227",
      "acquirer_return_code": "0000",
      "acquirer_tid": "4215644227",
      "amount": 38940,
      "antifraud_response": {
        "provider_name": "pagarme",
        "score": "moderated",
        "status": "approved"
      },
      "brand_id": "VR56TI",
      "card": {
        "billing_address": {
          "city": "Belo Horizonte",
          "country": "BR",
          "line_1": "676, Avenida General Olímpio Mourão Filho, Itapoã",
          "state": "MG",
          "zip_code": "31710-690"
        },
        "brand": "Mastercard",
        "created_at": "2025-12-18T14:46:53",
        "exp_month": 9,
        "exp_year": 2028,
        "first_six_digits": "520018",
        "holder_name": "APPLE PAY",
        "id": "card_jGEJnLBFm6hXNrB8",
        "last_four_digits": "4857",
        "status": "active",
        "tokenization_method": "apple_pay",
        "type": "credit",
        "updated_at": "2025-12-18T14:46:53"
      },
      "created_at": "2025-12-18T14:46:53",
      "funding_source": "credit",
      "gateway_id": "4215644227",
      "gateway_response": {
        "code": "200",
        "errors": []
      },
      "id": "tran_g6OARJ17SvIa8Dln",
      "installments": 3,
      "metadata": {},
      "operation_type": "auth_and_capture",
      "status": "captured",
      "success": true,
      "transaction_type": "credit_card",
      "updated_at": "2025-12-18T14:46:53"
    },
    "metadata": {
      "session_id": "session_kBxn3NRjgZ1agr0c4KSVeOzVrm98MJ64"
    },
    "order": {
      "amount": 38940,
      "closed": true,
      "closed_at": "2025-12-18T14:46:53",
      "code": "pl_pWy9k1ObMo2z3VZSX2Tpbgr3dZB5Q0qL",
      "created_at": "2025-12-18T14:46:53",
      "currency": "BRL",
      "customer_id": "cus_gpAx8ylCxCd0r0Wv",
      "id": "or_AepadppiqC4oablQ",
      "metadata": {
        "session_id": "session_kBxn3NRjgZ1agr0c4KSVeOzVrm98MJ64"
      },
      "status": "paid",
      "updated_at": "2025-12-18T14:46:57"
    },
    "paid_amount": 38940,
    "paid_at": "2025-12-18T14:46:57",
    "payment_method": "credit_card",
    "status": "paid",
    "updated_at": "2025-12-18T14:46:57"
  }
}

"""
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from apps.payments.models import Payment, PaymentLink


def process_payment_webhook(webhook_data):
    """
    Processa eventos do webhook do Pagar.me.

    Atualiza corretamente:
    - Payment (dinheiro)
    - PaymentLink (estado do link)
    - Order (estado do pedido)
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
        print(f"✗ PaymentLink não encontrado: {charge_id}")
        return None

    pagarme_status = data.get("status")

    # STATUS FINANCEIROS VÁLIDOS
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

    if not payment_status:
        print(f"⚠ Status ignorado: {pagarme_status}")
        return None

    amount = Decimal(str(data.get("amount", 0))) / 100
    paid_at = data.get("paid_at")

    with transaction.atomic():

        payment, created = Payment.objects.get_or_create(
            payment_link=payment_link,
            defaults={
                "status": payment_status,
                "amount": amount,
                "payment_date": paid_at or timezone.now(),
            }
        )

        if not created and payment.status != payment_status:
            payment.status = payment_status
            payment.save(update_fields=["status"])

        # --------------------------------------------------
        # PAYMENT LINK (estado do link)
        # --------------------------------------------------
        if payment_status in ["paid", "overpaid", "underpaid"]:
            payment_link.status = "used"

        elif payment_status in ["failed", "canceled"]:
            payment_link.status = "canceled"

        payment_link.save(update_fields=["status"])

        # --------------------------------------------------
        # ORDER (estado comercial)
        # --------------------------------------------------
        order = payment_link.order

        if payment_status in ["paid", "overpaid", "underpaid"]:
            order.status = "paid"

        elif payment_status in ["failed", "canceled", "refunded", "chargeback"]:
            order.status = "canceled"

        order.save(update_fields=["status"])

    print(f"✓ Payment {'criado' if created else 'atualizado'} | {payment_status}")
    return payment

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
