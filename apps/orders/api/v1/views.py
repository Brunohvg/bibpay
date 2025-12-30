from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.orders.services.commands import create_order, get_order
from apps.orders.services.queries import list_orders_filtered
from .serializers import OrderSerializer


from rest_framework.permissions import IsAuthenticated

class OrderListCreateAPIView(APIView):
    """
    GET  -> lista pedidos (Filtrado por vendedor se não for admin)
    POST -> cria pedido
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Parametros de filtro
        params = request.query_params.copy()
        
        # Security: Force seller filter if not admin
        if not request.user.is_superuser:
            if hasattr(request.user, 'seller_profile'):
                params['seller'] = str(request.user.seller_profile.id)
            else:
                return Response([], status=status.HTTP_200_OK)

        orders = list_orders_filtered(params)
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

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_order(pk)
        
        # Security: Check ownership
        if not request.user.is_superuser:
            if not hasattr(request.user, 'seller_profile') or order.seller != request.user.seller_profile:
                return Response(
                    {"error": "Você não tem permissão para ver este pedido."}, 
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = OrderSerializer(order)
        return Response(serializer.data)
