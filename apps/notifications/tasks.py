# apps/notifications/tasks.py

from celery import shared_task
from .services.whatsapp import (
    send_payment_link,
    send_payment_confirmed
)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 3})
def send_payment_link_task(phone, link, instance_id):
    send_payment_link(phone, link, instance_id)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=5, retry_kwargs={"max_retries": 3})
def send_payment_confirmed_task(phone, value, instance_id):
    send_payment_confirmed(phone, value, instance_id)
