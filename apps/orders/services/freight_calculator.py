from apps.core.integrations.sgpweb import CorreiosAPI


def calcular_frete_from_request(data: dict) -> dict:
    payload = {
        "cep_destino": data.get("cep", "").replace("-", ""),
        "peso": float(data.get("weight")) * 1000,
        "comprimento": int(data.get("length")),
        "largura": int(data.get("width")),
        "altura": int(data.get("height")),
    }

    api = CorreiosAPI()
    resultado = api.calcular(cep_origem="30170903", **payload)

    def ok(servico):
        return servico and "txErro" not in servico.get("preco", {})

    def to_float(valor):
        return float(valor.replace(",", "."))

    freight = {}

    if ok(resultado.get("03220")):
        s = resultado["03220"]
        freight["sedex"] = {
            "preco": to_float(s["preco"]["pcFinal"]),
            "prazo": int(s["prazo"]["prazoEntrega"]),
        }

    if ok(resultado.get("03298")):
        p = resultado["03298"]
        freight["pac"] = {
            "preco": to_float(p["preco"]["pcFinal"]),
            "prazo": int(p["prazo"]["prazoEntrega"]),
        }

    return freight
