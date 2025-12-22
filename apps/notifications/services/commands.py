# apps/notifications/services/whatsapp_service.py

import logging

from apps.notifications.domain.messages import (
    build_payment_link_success_message,
    build_payment_link_failed_message,
    build_payment_refused_message,
    build_payment_approved_message,
)
from apps.notifications.domain.rules import is_valid_phone, value_float_format

logger = logging.getLogger("integrations")


class WhatsAppMessageService:
    def __init__(self, *, client, instance_id: str, instance_token: str):
        if not client:
            raise ValueError("Client da Evolution API não informado")

        self.client = client
        self.instance_id = instance_id
        self.instance_token = instance_token

    def _send(self, message):
        try:
            self.client.messages.send_text(
                instance_id=self.instance_id,
                message=message,
                instance_token=self.instance_token,
            )
        except Exception:
            logger.exception("Erro ao enviar mensagem WhatsApp")
            raise

    def _validate_phone(self, phone: str):
        if not is_valid_phone(phone):
            raise ValueError("Telefone inválido")


    def send_payment_link_successful(self, *, phone: str, value: float, link: str):
        self._validate_phone(phone)
    
        message = build_payment_link_success_message(
            phone=phone,
            link=link,
            value=value,
        )
        self._send(message)

    def send_payment_link_failed(self, *, phone: str):
        self._validate_phone(phone)

        message = build_payment_link_failed_message(phone=phone)
        self._send(message)

    def send_payment_refused(self, *, phone: str):
        self._validate_phone(phone)

        message = build_payment_refused_message(phone=phone)
        self._send(message)

    def send_payment_success_approved(self, *, phone: str, value: float):
        self._validate_phone(phone)

        message = build_payment_approved_message(
            phone=phone,
            value=value,
        )
        self._send(message)


