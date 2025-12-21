from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.orders.services.commands import create_order, get_order
from apps.orders.services.queries import list_orders_filtered
from .serializers import OrderSerializer


class OrderListCreateAPIView(APIView):
    """
    GET  -> lista pedidos
    POST -> cria pedido
    """

    def get(self, request):
        orders = list_orders_filtered(request.query_params)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        try:
            order = create_order(request.data)
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class OrderDetailAPIView(APIView):
    """
    GET -> detalhe do pedido
    """

    def get(self, request, pk):
        order = get_order(pk)
        serializer = OrderSerializer(order)
        return Response(serializer.data)
