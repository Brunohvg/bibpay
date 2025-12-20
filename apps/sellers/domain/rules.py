def can_delete_seller(seller) -> bool:
    """
    Um vendedor não pode ser deletado se tiver pedidos.
    """
    return not seller.orders.exists()
