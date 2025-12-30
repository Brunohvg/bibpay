from django.shortcuts import get_object_or_404
from apps.sellers.models import Seller


def list_sellers():
    return Seller.objects.all().distinct()


def get_seller(seller_id: int) -> Seller:
    return get_object_or_404(Seller, id=seller_id)


def filter_sellers(**filters):
    return Seller.objects.filter(**filters)
