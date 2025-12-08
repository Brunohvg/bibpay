# payments/services.py

from decimal import Decimal
from apps.payments.models import PaymentLink, Payment
from apps.core.integrations.pagarme import PagarMePaymentLink


# ============================
#   CRIAÇÃO DE LINK DE PAGAMENTO
# ============================

def process_payment_link_for_order(order):
    """
    Gera o link de pagamento via API do Pagar.me e salva no banco.
    Retorna o PaymentLink criado ou None se algo falhar.
    """
    link_data = generate_payment_link(order)
    if not link_data:
        return None

    return create_payment_link_record(order, link_data)


def generate_payment_link(order):
    """
    Chama a API do Pagar.me para criar um link de pagamento.
    Retorna um dict com {id, url} ou None se falhar.
    """
    try:
        pagarme = PagarMePaymentLink(
            customer_name=order.name,
            total_amount=int(order.total * 100),   # Pagar.me exige em centavos
            max_installments=order.installments,
            free_installments=order.installments,
        )

        response = pagarme.create_link()

        link_id = response.get("id")
        link_url = response.get("url") or response.get("short_url")

        # API precisa retornar id + url
        if not link_id or not link_url:
            print("✗ API do Pagar.me voltou incompleta:", response)
            return None

        return {"id": link_id, "url": link_url}

    except Exception as e:
        print("✗ Erro ao chamar Pagar.me:", e)
        return None


def create_payment_link_record(order, link_data):
    """
    Salva o PaymentLink no banco, usando os dados retornados pela API.
    """
    try:
        return PaymentLink.objects.create(
            order=order,
            id_link=link_data["id"],
            url_link=link_data["url"],
            amount=order.total,
            status="active",
        )
    except Exception as e:
        print("✗ Erro ao salvar PaymentLink:", e)
        return None


# ============================
#   LISTAGENS / CONSULTAS
# ============================

def get_payment_links_for_order(order):
    """
    Retorna todos os PaymentLinks ativos e não deletados de um pedido.
    """
    return PaymentLink.objects.filter(
        order=order,
        is_active=True,
        is_deleted=False
    )


def list_active_payment_links():
    """
    Lista todos os PaymentLinks ativos.
    """
    return PaymentLink.objects.filter(
        is_active=True,
        is_deleted=False
    )


def list_payments(**filters):
    """
    Lista pagamentos aplicando filtros opcionais.
    Ex: list_payments(status='paid')
    """
    qs = Payment.objects.all()
    if filters:
        qs = qs.filter(**filters)
    return qs


# ============================
#   SOMATÓRIOS
# ============================

def calculate_total_from_links(objects):
    """
    Soma o campo 'amount' de Payment ou PaymentLink.

    Funciona para:
    - QuerySet de Payment
    - QuerySet de PaymentLink

    O nome antigo era confuso.
    """
    total = Decimal("0")

    for obj in objects:
        if not obj.amount:
            continue
        total += Decimal(str(obj.amount))

    return total

