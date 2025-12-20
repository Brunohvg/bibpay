from rest_framework import serializers
from apps.orders.models import Order


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "name",
            "value",
            "value_freight",
            "status",
            "installments",
            "seller",
            "created_at",
        ]
