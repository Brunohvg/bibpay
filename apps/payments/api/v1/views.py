"""
Views da API de Pagamentos.

Responsabilidade:
- Receber requisições HTTP
- Validar entrada mínima
- Chamar COMMANDS
- Retornar resposta HTTP

Este arquivo:
✔ NÃO contém regra de negócio
✔ NÃO acessa modelos diretamente
✔ NÃO decide status
✔ NÃO conhece rules

View é porteiro, não juiz.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.payments.services.commands import process_payment_webhook


class WebhookAPIView(APIView):
    """
    Endpoint de recebimento de webhooks do Pagar.me.

    Fluxo:
    - Recebe payload
    - Filtra eventos relevantes
    - Encaminha para o command
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.data
        event = payload.get("type")

        print(f"→ Webhook recebido | Evento: {event}")

        # Ignora eventos que não são de cobrança
        if not event or not event.startswith("charge."):
            return Response(
                {"status": "ignorado"},
                status=status.HTTP_200_OK
            )

        payment = process_payment_webhook(payload)

        if not payment:
            return Response(
                {"error": "Falha ao processar webhook"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"status": "ok"},
            status=status.HTTP_200_OK
        )
