from django.shortcuts import get_object_or_404
from apps.sellers.models import Seller
from apps.sellers.domain.rules import can_delete_seller


def create_seller(data: dict) -> Seller:
    """
    Cria um vendedor.
    """
    return Seller.objects.create(
        name=data.get("name", "").strip(),
        email=data.get("email", "").lower().strip(),
    )


def update_seller(seller_id: int, data: dict) -> Seller:
    """
    Atualiza dados do vendedor.
    """
    seller = get_object_or_404(Seller, id=seller_id)

    for field in ["name", "email"]:
        if field in data:
            setattr(seller, field, data[field])

    seller.save()
    return seller


def delete_seller(seller_id: int) -> None:
    """
    Remove um vendedor se permitido.
    """
    seller = get_object_or_404(Seller, id=seller_id)

    if not can_delete_seller(seller):
        raise ValueError("Vendedor possui pedidos.")

    seller.delete()
