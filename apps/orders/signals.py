# apps/orders/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.orders.models import Order
from apps.payments.models import PaymentLink
from apps.payments.services import process_payment_link_for_order

from apps.core.integrations.integration_whatsapp.evolution_service import CLIENT

@receiver(post_save, sender=Order)
def create_payment_link_for_order(sender, instance, created, **kwargs):
    """
    Cria automaticamente um PaymentLink quando um Order é criado.

    Regras:
    - Só executa quando created=True
    - Não cria se já existir link ativo para o pedido
    """

    if not created:
        return

    # 🔒 Proteção contra duplicidade
    has_active_link = PaymentLink.objects.filter(
        order=instance,
        status="active"
    ).exists()

    if has_active_link:
        return

    print(f"\n🔔 SIGNAL Order criado | ID={instance.id}")

    payment_link = process_payment_link_for_order(order=instance)

    if payment_link:
        CLIENT.messages.send_text_message(
            number=instance.customer_phone,
            text=f"Olá {instance.customer_name}, seu pedido #{instance.id} foi criado com sucesso! "
                 f"Acesse o link para completar o pagamento: {payment_link.url_link}"
        )   
        print("✓ PaymentLink criado")
        print(f"  Link ID: {payment_link.id_link}")
        print(f"  URL: {payment_link.url_link}")
    else:
        print("✗ ERRO ao criar PaymentLink")

    print("🔔 FIM SIGNAL\n")
