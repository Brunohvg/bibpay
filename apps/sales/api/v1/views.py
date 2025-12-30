from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.sales.models import DailySale
from .serializers import DailySaleSerializer
from django.db import IntegrityError

class DailySaleListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = DailySale.objects.all()
        
        # Filtro de vendedor
        if not request.user.is_superuser:
            if hasattr(request.user, 'seller_profile'):
                qs = qs.filter(seller=request.user.seller_profile)
            else:
                return Response([], status=status.HTTP_200_OK)
        else:
             # Admin pode filtrar por ?seller_id=
             seller_id = request.query_params.get('seller_id')
             if seller_id:
                 qs = qs.filter(seller_id=seller_id)
                 
        qs = qs.order_by('-date')
        serializer = DailySaleSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not hasattr(request.user, 'seller_profile') and not request.user.is_superuser:
             return Response({"error": "Apenas vendedores podem criar vendas."}, status=status.HTTP_403_FORBIDDEN)
             
        serializer = DailySaleSerializer(data=request.data)
        if serializer.is_valid():
            seller = request.user.seller_profile
            
            # Se for admin criando pra outro, lógica seria diferente, 
            # mas vamos assumir que API é para o próprio uso do vendedor por enquanto
            
            try:
                serializer.save(seller=seller)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {"error": "Já existe um lançamento para esta data."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DailySaleDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, user):
        obj = get_object_or_404(DailySale, pk=pk)
        if not user.is_superuser:
             if not hasattr(user, 'seller_profile') or obj.seller != user.seller_profile:
                 return None
        return obj

    def get(self, request, pk):
        sale = self.get_object(pk, request.user)
        if not sale:
            return Response({"error": "Não encontrado ou acesso negado."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = DailySaleSerializer(sale)
        return Response(serializer.data)

    def patch(self, request, pk):
        sale = self.get_object(pk, request.user)
        if not sale:
            return Response({"error": "Acesso negado."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = DailySaleSerializer(sale, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        sale = self.get_object(pk, request.user)
        if not sale:
            return Response({"error": "Acesso negado."}, status=status.HTTP_403_FORBIDDEN)
            
        sale.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
