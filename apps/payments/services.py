# payments/services.py
from apps.payments.models import PaymentLink
from apps.core.integrations.pagarme import PagarMePaymentLink

def process_payment_link_for_order(order):
    link_data = generate_payment_link(order)

    if not link_data or "error" in link_data:
        print("✗ Falha ao gerar o link de pagamento:", link_data)
        return None

    return create_payment_link_record(order, link_data)


def generate_payment_link(order):
    """
    Gera um link de pagamento usando a API do Pagar.me.
    """
    try:
        pagarme = PagarMePaymentLink(
            customer_name=order.name,
            total_amount=int(order.total * 100),    # centavos
            max_installments=order.installments,
            free_installments=order.installments,
        )

        response = pagarme.create_link()
        print("✓ Link gerado:", response)
        return response

    except Exception as e:
        return {"error": str(e)}


def create_payment_link_record(order, link_data):
    """
    Salva o link de pagamento.
    """
    try:
        return PaymentLink.objects.create(
            order=order,
            id_link=link_data.get("id"),
            url_link=link_data.get("url") or link_data.get("short_url"),
            amount=order.total,
            status="active",
        )
    except Exception as e:
        print(f"✗ Erro ao criar PaymentLink: {e}")
        return None
