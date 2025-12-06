# orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.orders.models import Order
from apps.payments.services import process_payment_link_for_order

@receiver(post_save, sender=Order)
def create_payment_link_for_order(sender, instance, created, **kwargs):
    if created:
        process_payment_link_for_order(order=instance)

