from apps.payments.models import PaymentLink
from apps.core.integrations.pagarme import PagarMePaymentLink


def create_payment_link(**kwargs):
    payment_link = PagarMePaymentLink(**kwargs)
    return payment_link
