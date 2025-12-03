import requests
from decouple import config


class CorreiosAPI:
    """
    Cliente simples para consultar preço e prazo da API dos Correios.
    Tudo dinâmico. Você passa parâmetros, ela devolve os resultados.
    """

    def __init__(self):
        self.token = config("MAIL_ACCESS_KEY")

        self.url_preco = "https://api.correios.com.br/preco/v1/nacional"
        self.url_prazo = "https://api.correios.com.br/prazo/v1/nacional"

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # -------------------------
    # CONSULTAS SIMPLES
    # -------------------------

    def consultar_preco(self, payload: dict):
        resp = requests.post(self.url_preco, json=payload, headers=self.headers)
        return resp.json()

    def consultar_prazo(self, payload: dict):
        resp = requests.post(self.url_prazo, json=payload, headers=self.headers)
        return resp.json()

    # -------------------------
    # MÉTODO PRINCIPAL (DINÂMICO)
    # -------------------------

    def calcular(self,
                 produtos: list,
                 cep_origem: str,
                 cep_destino: str,
                 peso: int,
                 comprimento: int,
                 largura: int,
                 altura: int,
                 formato: int = 1):
        """
        produtos → lista de códigos ["03220", "03298"]
        """

        id_lote = "lote-001"

        # ----- Monta params PREÇO -----
        parametros_preco = []
        for i, produto in enumerate(produtos, start=1):
            parametros_preco.append({
                "coProduto": produto,
                "nuRequisicao": i,
                "cepOrigem": cep_origem,
                "cepDestino": cep_destino,
                "psObjeto": peso,
                "comprimento": comprimento,
                "largura": largura,
                "altura": altura,
                "nuFormato": formato,
            })

        payload_preco = {
            "idLote": id_lote,
            "parametrosProduto": parametros_preco
        }

        # ----- Monta params PRAZO -----
        parametros_prazo = []
        for i, produto in enumerate(produtos, start=1):
            parametros_prazo.append({
                "coProduto": produto,
                "nuRequisicao": i,
                "cepOrigem": cep_origem,
                "cepDestino": cep_destino,
            })

        payload_prazo = {
            "idLote": id_lote,
            "parametrosPrazo": parametros_prazo
        }

        # ----- Chama APIs -----
        preco = self.consultar_preco(payload_preco)
        prazo = self.consultar_prazo(payload_prazo)

        # ----- Junta retorno organizado -----
        retorno = {}
        for i, produto in enumerate(produtos, start=1):
            retorno[produto] = {
                "preco": preco[i - 1] if isinstance(preco, list) else preco,
                "prazo": prazo[i - 1] if isinstance(prazo, list) else prazo,
            }

        return retorno


# -------------------------
# TESTE RÁPIDO
# -------------------------
if __name__ == "__main__":
    api = CorreiosAPI()

    resultado = api.calcular(
        produtos=["03220", "03298"],  # SEDEX / PAC
        cep_origem="30170903",
        cep_destino="35384000",
        peso=300,
        comprimento=22,
        largura=16,
        altura=18
    )

    print(resultado)
