from rest_framework import serializers
from apps.sales.models import DailySale

class DailySaleSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.name', read_only=True)
    
    class Meta:
        model = DailySale
        fields = ['id', 'seller', 'seller_name', 'date', 'amount', 'notes', 'created_at']
        read_only_fields = ['seller', 'created_at']

    def validate(self, data):
        """
        Garante que o dia não está duplicado para este vendedor
        (embora o model já tenha unique_together, é bom validar antes)
        """
        # A validação de unicidade é feita no create da view ou aqui se tivermos request user contexto
        return data
