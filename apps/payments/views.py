from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.payments.services import process_payment_webhook


class WebhookAPIView(APIView):
    """
    Webhook DRF para pagamentos
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.data

        # Segurança mínima
        event = payload.get("event")
        if not event:
            return Response(
                {"error": "Evento não informado"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Evento esperado
        if event == "order/paid":
            payment = process_payment_webhook(payload)

            if not payment:
                return Response(
                    {"error": "Falha ao processar pagamento"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response({"status": "ok"}, status=status.HTTP_200_OK)
