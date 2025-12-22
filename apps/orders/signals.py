# apps/orders/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.orders.models import Order
from apps.payments.models import PaymentLink
from apps.payments.services.commands import process_payment_link_for_order
from apps.notifications.services.factory import get_whatsapp_service


@receiver(post_save, sender=Order)
def create_payment_link_for_order(sender, instance: Order, created, **kwargs):
    if not created:
        return

    if PaymentLink.objects.filter(order=instance, status="active").exists():
        return

    # Cria o link de pagamento
    payment_link = process_payment_link_for_order(order=instance)

    # Segurança básica
    if not payment_link or not payment_link.url_link:
        return

    try:
        service = get_whatsapp_service()
        service.send_payment_link_successful(
            value=instance.total,
            phone=f"55{instance.seller.phone}",
            link=payment_link.url_link,
        )
    except Exception:
        # Signal NUNCA pode derrubar o fluxo
        pass
