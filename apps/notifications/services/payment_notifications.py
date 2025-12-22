from apps.notifications.services.factory import get_whatsapp_service


def payment_status(*, payment):
    service = get_whatsapp_service()
    order = payment.order
    phone = order.seller.phone  # ou de onde vier
    print(phone)
    status = payment.status
    print(f"Estamos aqui {status}")
    if status == "paid":
        service.send_payment_success_approved(
            phone=f"55{phone}",
            value=payment.amount
        )

    elif status == "failed":
        service.send_payment_refused(phone=f"55{phone}")

    elif status == "canceled":
        service.send_payment_refused(phone=f"55{phone}")

    elif status in {"refunded", "chargeback"}:
        service.send_payment_refused(phone=f"55{phone}")
