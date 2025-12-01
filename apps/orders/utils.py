from decimal import Decimal, InvalidOperation

def formatar_valor(valor):
    valor = str(valor).strip()

    # None, string vazia, espaço, etc → vira 0
    if not valor:
        return Decimal("0")

    # Conversão BR → US
    if "," in valor:
        valor = valor.replace(".", "")  # remove separador de milhar
        valor = valor.replace(",", ".")  # vírgula vira decimal

    try:
        return Decimal(valor)
    except InvalidOperation:
        # Se o valor for inválido, devolve 0 em vez de explodir
        return Decimal("0")
