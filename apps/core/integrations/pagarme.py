import requests
from decouple import config
from enum import Enum


class PaymentLinkType(Enum):
    """Tipos de endpoints disponíveis no Pagar.me"""
    ORDER = "https://api.pagar.me/core/v5/orders"
    PAYMENT_LINK = "https://api.pagar.me/core/v5/paymentlinks"


class BasePagarMeApi:
    """
    Classe base para interações com a API do Pagar.me.
    
    Attributes:
        api_url (str): URL da API do Pagar.me.
        api_key (str): Chave da API carregada do ambiente.
        total_amount (int): Valor total em centavos.
        max_installments (int): Número máximo de parcelas.
        customer_name (str): Nome do cliente/pedido.
    """
    
    def __init__(self, total_amount, max_installments, customer_name, api_url):
        self.api_url = api_url
        self.api_key = config("API_KEY_PAGAR_ME")
        self.total_amount = total_amount
        self.max_installments = max_installments
        self.customer_name = customer_name
    
    def _get_headers(self):
        """Retorna os headers padrão para requisições à API."""
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Basic {self.api_key}"
        }
    
    def _make_request(self, payload):
        """
        Faz a requisição POST para a API.
        
        Args:
            payload (dict): Dados a serem enviados.
            
        Returns:
            dict: Resposta da API em formato JSON ou erro.
        """
        try:
            response = requests.post(self.api_url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}


class PagarMeOrder(BasePagarMeApi):
    """
    Cria pedidos na API do Pagar.me usando o endpoint /orders.
    
    Attributes:
        Herda de BasePagarMeApi.
    """
    
    def __init__(self, total_amount, max_installments, customer_name):
        super().__init__(total_amount, max_installments, customer_name, PaymentLinkType.ORDER.value)
    
    def generate_installments(self):
        """
        Gera lista de parcelas.
        
        Returns:
            list: Lista de parcelas com número e valor total.
        """
        return [{"number": i, "total": self.total_amount} for i in range(1, self.max_installments + 1)]
    
    def create_order(self):
        """
        Cria um pedido na API do Pagar.me.
        
        Returns:
            dict: Resposta da API.
        """
        installments = self.generate_installments()
        
        payload = {
            "customer": {"name": self.customer_name},
            "items": [
                {
                    "amount": self.total_amount,
                    "description": "Link de pagamento da loja Lojas Bibelô",
                    "code": "1",
                    "quantity": 1
                }
            ],
            "payments": [
                {
                    "checkout": {
                        "expires_in": 1000,
                        "accepted_payment_methods": ["credit_card"],
                        "success_url": "https://www.bibelo.com.br/",
                        "customer_editable": True,
                        "billing_address_editable": False,
                        "credit_card": {
                            "installments": installments
                        }
                    },
                    "payment_method": "checkout"
                }
            ]
        }
        
        return self._make_request(payload)


class PagarMePaymentLink(BasePagarMeApi):
    """
    Cria links de pagamento na API do Pagar.me usando o endpoint /paymentlinks.
    
    Attributes:
        free_installments (int): Número de parcelas sem juros.
        interest_rate (float): Taxa de juros para parcelamento.
    """
    
    def __init__(self, total_amount, max_installments, customer_name, free_installments, interest_rate=2):
        super().__init__(total_amount, max_installments, customer_name, PaymentLinkType.PAYMENT_LINK.value)
        self.free_installments = free_installments
        self.interest_rate = interest_rate
    
    def create_link(self):
        """
        Cria um link de pagamento na API do Pagar.me.
        
        Returns:
            dict: Resposta da API contendo o link gerado.
        """
        payload = {
            "is_building": False,
            "payment_settings": {
                "credit_card_settings": {
                    "installments_setup": {
                        "interest_type": "simple",
                        "max_installments": self.max_installments,
                        "amount": self.total_amount,
                        "interest_rate": self.interest_rate,
                        "free_installments": self.free_installments,
                    },
                    "operation_type": "auth_and_capture"
                },
                "accepted_payment_methods": ["credit_card"]
            },
            "cart_settings": {
                "items": [
                    {
                        "amount": self.total_amount,
                        "name": "Vendas Whatsapp",
                        "description": "Pedido feito por cliente via WhatsApp",
                        "default_quantity": 1
                    }
                ]
            },
            "name": self.customer_name,
            "type": "order",
            "expires_in": 1200,
            "max_paid_sessions": 1,
        }
        
        return self._make_request(payload)


"""# Exemplos de uso
if __name__ == "__main__":
    total_amount = 20000  # R$ 200,00 em centavos
    max_installments = 1
    customer_name = "Campo_Obrigatorio"
    
    # Criar pedido usando /orders
    print("=== Criando pedido via /orders ===")
    order = PagarMeOrder(total_amount, max_installments, customer_name)
    order_response = order.create_order()
    print(order_response)
    
    # Criar link de pagamento usando /paymentlinks
    print("\n=== Criando link de pagamento via /paymentlinks ===")
    payment_link = PagarMePaymentLink(total_amount, max_installments, customer_name, free_installments=1)
    link_response = payment_link.create_link()
    print(link_response)"""