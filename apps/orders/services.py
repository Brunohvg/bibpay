from django.shortcuts import get_object_or_404
from apps.orders.models import Order
from apps.orders.utils import formatar_valor
from apps.sellers.services import get_seller
from apps.core.integrations.sgpweb import CorreiosAPI


# ============================
#   CRIAÇÃO DE PEDIDO
# ============================

def create_order(data):
    """
    Cria um pedido no status inicial 'pending'.

    Espera no dict `data`:
        - cliente_nome
        - valor_produto
        - valor_frete
        - parcelas
        - vendedor
    """

    order_data = {
        "name": data.get("cliente_nome", "").strip(),
        "value": formatar_valor(data.get("valor_produto", "0")),
        "value_freight": formatar_valor(data.get("valor_frete", "0")),
        "status": "pending",
        "installments": int(data.get("parcelas", 1)),
        "seller": get_seller(seller_id=data.get("vendedor")),
    }

    return Order.objects.create(**order_data)


# ============================
#   ATUALIZAÇÃO DE PEDIDO
# ============================

def update_order(order_id, data):
    """
    Atualiza apenas campos permitidos do pedido.
    Evita sobrescrever campos críticos por engano.
    """

    order = get_object_or_404(Order, id=order_id)

    # Campos que PODEM ser alterados
    allowed_fields = {
        "name",
        "value",
        "value_freight",
        "status",
        "installments",
        "seller",
    }

    for field, value in data.items():
        if field in allowed_fields:
            setattr(order, field, value)

    order.save()
    return order


# ============================
#   EXCLUSÃO
# ============================

def delete_order(order_id):
    """
    Remove o pedido.
    Se futuramente usar soft delete, muda aqui.
    """
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return True


# ============================
#   CONSULTAS
# ============================

def list_orders():
    """Lista todos os pedidos."""
    return Order.objects.all()


def get_order(order_id):
    """Busca um pedido pelo ID."""
    return get_object_or_404(Order, id=order_id)


def filter_orders(**filters):
    """
    Filtro genérico.
    ⚠ Use apenas internamente (não passe request direto aqui).
    """
    return Order.objects.filter(**filters)


# ============================
#   FRETE (CORREIOS)
# ============================

def calcular_frete(**data) -> dict:
    """
    Calcula frete nos Correios.

    Espera em `data`:
        - cep_destino
        - peso
        - altura
        - largura
        - comprimento

    Retorna:
        {
            "sedex": {"preco": float, "prazo": int},
            "pac": {"preco": float, "prazo": int}
        }
    """

    api = CorreiosAPI()

    resultado = api.calcular(
        cep_origem="30170903",
        **data
    )

    freight = {}

    def ok(servico):
        return (
            servico
            and "txErro" not in servico.get("preco", {})
            and "txErro" not in servico.get("prazo", {})
        )

    def to_float(valor: str) -> float:
        # Correios retornam vírgula como separador decimal
        return float(valor.replace(",", "."))

    # SEDEX - 03220
    sedex = resultado.get("03220")
    if ok(sedex):
        freight["sedex"] = {
            "preco": to_float(sedex["preco"]["pcFinal"]),
            "prazo": int(sedex["prazo"]["prazoEntrega"]),
        }

    # PAC - 03298
    pac = resultado.get("03298")
    if ok(pac):
        freight["pac"] = {
            "preco": to_float(pac["preco"]["pcFinal"]),
            "prazo": int(pac["prazo"]["prazoEntrega"]),
        }

    return freight
