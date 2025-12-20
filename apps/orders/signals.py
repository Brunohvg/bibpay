from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.orders.models import Order
from apps.payments.models import PaymentLink
from apps.payments.services import process_payment_link_for_order


@receiver(post_save, sender=Order)
def create_payment_link_for_order(sender, instance, created, **kwargs):
    if not created:
        return

    if PaymentLink.objects.filter(order=instance, status="active").exists():
        return

    process_payment_link_for_order(order=instance)
