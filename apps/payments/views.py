from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.payments.services import process_payment_webhook


class WebhookAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.data
        event = payload.get("type")

        print(f"→ Webhook recebido | Evento: {event}")

        if not event or not event.startswith("charge."):
            return Response({"status": "ignorado"}, status=200)

        payment = process_payment_webhook(payload)

        if not payment:
            return Response(
                {"error": "Falha ao processar webhook"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"status": "ok"}, status=status.HTTP_200_OK)
