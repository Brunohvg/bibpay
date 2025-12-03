import requests
from decouple import config

TOKEN = config("MAIL_ACCESS_KEY")

URL_PRECO = "https://api.correios.com.br/preco/v1/nacional"
URL_PRAZO = "https://api.correios.com.br/prazo/v1/nacional"



def calcular_preco_prazo():
    # Cabeçalhos da API
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Lote que vamos usar para preço e prazo
    id_lote = "lote-001"

    # -------------------------
    # 1) Parâmetros do PREÇO
    # -------------------------
    dados_preco = {
        "idLote": id_lote,
        "parametrosProduto": [
            {
                "coProduto": "03220",         # SEDEX
                "nuRequisicao": 1,
                "cepOrigem": "30170903",
                "cepDestino": "34600190",
                "psObjeto": 300,
                "comprimento": 22,
                "largura": 16,
                "altura": 18,
                "nuFormato": 1
            },
            {
                "coProduto": "03298",        # PAC 
                "nuRequisicao": 2,
                "cepOrigem": "30170903",
                "cepDestino": "34600190",
                "psObjeto": 300,
                "comprimento": 22,
                "largura": 16,
                "altura": 18,
                "nuFormato": 1
            }
        ]
    }

    # -------------------------
    # 2) Parâmetros do PRAZO
    # -------------------------
    dados_prazo = {
        "idLote": id_lote,
        "parametrosPrazo": [
            {
                "coProduto": "03220",
                "nuRequisicao": 1,
                "cepOrigem": "30170903",
                "cepDestino": "34600190"
            },
            {
                "coProduto": "03298",
                "nuRequisicao": 2,
                "cepOrigem": "30170903",
                "cepDestino": "34600190"
            }
        ]
    }

    # -------------------------
    # Chamada PREÇO
    # -------------------------
    resp_preco = requests.post(URL_PRECO, json=dados_preco, headers=headers)
    preco_data = resp_preco.json()

    # -------------------------
    # Chamada PRAZO
    # -------------------------
    resp_prazo = requests.post(URL_PRAZO, json=dados_prazo, headers=headers)
    prazo_data = resp_prazo.json()

    # -------------------------
    # Junta os dois resultados
    # -------------------------
    resultado_final = {
        "PAC": {
            "preco": preco_data,
            "prazo": prazo_data,
        },
        "SEDEX": {
            "preco": preco_data,
            "prazo": prazo_data,
        },
    }

    return resultado_final




        

    
# TESTE
if __name__ == "__main__":
    print(calcular_preco_prazo())
