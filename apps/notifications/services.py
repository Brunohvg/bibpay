# apps/payments/services.py

from apps.notifications.services.whatsapp import send_payment_link

def create_payment_link(order):
    link = gerar_link_gateway(order)

    send_payment_link(
        phone=order.seller.phone,
        link=link,
        instance_id=order.seller.instance_id
    )

    return link

