from apps.notifications.services.factory import get_whatsapp_service

service = get_whatsapp_service()

service.send_payment_link_successful(
    phone="5531973121650",
    link="https://pay.me/abc",
)
