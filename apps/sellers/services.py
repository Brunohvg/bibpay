from apps.sellers.models import Seller

from django.shortcuts import get_object_or_404

# Criar um vendedor
def create_seller(data):
    return Seller.objects.create(**data)

# Atualizar um vendedor
def update_seller(seller_id, data):
    seller = get_object_or_404(Seller, id=seller_id)

    for field, value in data.items():
        setattr(seller, field, value)

    seller.save()
    return seller

# Deletar um vendedor
def delete_seller(seller_id):
    seller = get_object_or_404(Seller, id=seller_id)
    seller.delete()
    return True

# Listar tudo
def list_sellers():
    return Seller.objects.all()

# Buscar um único vendedor
def get_seller(seller_id):
    return get_object_or_404(Seller, id=seller_id)

# Filtros genéricos
def filter_sellers(**filters):
    return Seller.objects.filter(**filters)
