"""
Domain de Pedido.
Contém SOMENTE regras de negócio.
"""

def build_order(*, name: str, value: float, freight: float, installments: int, seller) -> dict:
    if not name or not name.strip():
        raise ValueError("Nome do cliente é obrigatório")

    if installments < 1:
        raise ValueError("Parcelas inválidas")

    return {
        "name": name.strip(),
        "value": value,
        "value_freight": freight,
        "status": "pending",
        "installments": installments,
        "seller": seller,
    }
