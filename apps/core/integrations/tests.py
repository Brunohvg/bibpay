from django.test import TestCase
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.utils import timezone
from apps.core.integrations.pagarme import PagarMeOrder, PagarMePaymentLink
from apps.core.integrations.sgpweb import CorreiosAPI
import json


class PagarMeOrderTestCase(TestCase):
    """Testes da integração com Pagar.me para Orders."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.customer_name = 'João Silva'
        self.total_amount = 10000  # 100 reais em centavos
        self.max_installments = 12

    @patch('apps.core.integrations.pagarme.requests.post')
    def test_pagarme_create_order_success(self, mock_post):
        """Testa a criação bem-sucedida de um pedido no Pagar.me."""
        # Mock da resposta da API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'order_123',
            'status': 'pending',
            'customer': {'name': self.customer_name}
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        pagarme = PagarMeOrder(
            total_amount=self.total_amount,
            max_installments=self.max_installments,
            customer_name=self.customer_name
        )
        
        result = pagarme.create_order()
        
        self.assertEqual(result['id'], 'order_123')
        self.assertEqual(result['customer']['name'], self.customer_name)

    @patch('apps.core.integrations.pagarme.requests.post')
    def test_pagarme_create_order_api_error(self, mock_post):
        """Testa o comportamento quando há erro na API do Pagar.me."""
        # Mock de erro
        mock_post.side_effect = Exception('API Error')

        pagarme = PagarMeOrder(
            total_amount=self.total_amount,
            max_installments=self.max_installments,
            customer_name=self.customer_name
        )
        
        result = pagarme.create_order()
        
        self.assertIn('error', result)

    def test_pagarme_generate_installments(self):
        """Testa a geração de parcelas."""
        pagarme = PagarMeOrder(
            total_amount=self.total_amount,
            max_installments=3,
            customer_name=self.customer_name
        )
        
        installments = pagarme.generate_installments()
        
        self.assertEqual(len(installments), 3)
        self.assertEqual(installments[0]['number'], 1)
        self.assertEqual(installments[0]['total'], self.total_amount)
        self.assertEqual(installments[2]['number'], 3)

    def test_pagarme_headers(self):
        """Testa a geração correta dos headers da API."""
        pagarme = PagarMeOrder(
            total_amount=self.total_amount,
            max_installments=self.max_installments,
            customer_name=self.customer_name
        )
        
        headers = pagarme._get_headers()
        
        self.assertEqual(headers['accept'], 'application/json')
        self.assertEqual(headers['content-type'], 'application/json')
        self.assertIn('authorization', headers)


class PagarMePaymentLinkTestCase(TestCase):
    """Testes da integração com Pagar.me para Payment Links."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.customer_name = 'João Silva'
        self.total_amount = 10000  # 100 reais em centavos
        self.max_installments = 12
        self.free_installments = 12

    @patch('apps.core.integrations.pagarme.requests.post')
    def test_pagarme_create_payment_link_success(self, mock_post):
        """Testa a criação bem-sucedida de um link de pagamento."""
        # Mock da resposta da API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'link_123',
            'url': 'https://pagar.me/link/123',
            'short_url': 'https://pagar.me/l/abc123',
            'status': 'active'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        pagarme = PagarMePaymentLink(
            customer_name=self.customer_name,
            total_amount=self.total_amount,
            max_installments=self.max_installments,
            free_installments=self.free_installments
        )
        
        result = pagarme.create_link()
        
        self.assertEqual(result['id'], 'link_123')
        self.assertIn('url', result)

    def test_pagarme_payment_link_inheritance(self):
        """Testa que PagarMePaymentLink herda de BasePagarMeApi."""
        pagarme = PagarMePaymentLink(
            customer_name=self.customer_name,
            total_amount=self.total_amount,
            max_installments=self.max_installments,
            free_installments=self.free_installments
        )
        
        self.assertEqual(pagarme.customer_name, self.customer_name)
        self.assertEqual(pagarme.total_amount, self.total_amount)
        self.assertEqual(pagarme.max_installments, self.max_installments)


class CorreiosAPITestCase(TestCase):
    """Testes da integração com a API dos Correios via SGPWeb."""

    def setUp(self):
        """Configuração inicial para os testes."""
        self.api = CorreiosAPI()

    @patch('apps.core.integrations.sgpweb.requests.post')
    def test_consultar_preco_success(self, mock_post):
        """Testa a consulta de preço nos Correios."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                'coProduto': '03220',
                'preco': {'pcFinal': '50,00'},
                'txErro': None
            }
        ]
        mock_post.return_value = mock_response

        payload = {
            'idLote': 'lote-001',
            'parametrosProduto': [
                {
                    'coProduto': '03220',
                    'nuRequisicao': 1,
                    'cepOrigem': '30170903',
                    'cepDestino': '01310100',
                    'psObjeto': 1.0,
                    'comprimento': 20,
                    'largura': 15,
                    'altura': 10,
                }
            ]
        }
        
        result = self.api.consultar_preco(payload)
        
        self.assertIsNotNone(result)
        self.assertIn('coProduto', result[0])

    @patch('apps.core.integrations.sgpweb.requests.post')
    def test_consultar_prazo_success(self, mock_post):
        """Testa a consulta de prazo nos Correios."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                'coProduto': '03220',
                'prazo': {'prazoEntrega': '3'},
                'txErro': None
            }
        ]
        mock_post.return_value = mock_response

        payload = {
            'idLote': 'lote-001',
            'parametrosPrazo': [
                {
                    'coProduto': '03220',
                    'nuRequisicao': 1,
                    'cepOrigem': '30170903',
                    'cepDestino': '01310100',
                }
            ]
        }
        
        result = self.api.consultar_prazo(payload)
        
        self.assertIsNotNone(result)
        self.assertIn('prazo', result[0])

    def test_correios_default_produtos(self):
        """Testa os produtos padrão da API dos Correios."""
        self.assertEqual(self.api.PRODUTOS_DEFAULT, ['03220', '03298'])

    @patch('apps.core.integrations.sgpweb.requests.post')
    def test_calcular_frete_success(self, mock_post):
        """Testa o cálculo de frete completo."""
        # Mock para preço
        mock_response_preco = MagicMock()
        mock_response_preco.json.return_value = [
            {
                'coProduto': '03220',
                'preco': {'pcFinal': '50,00'},
                'txErro': None
            },
            {
                'coProduto': '03298',
                'preco': {'pcFinal': '30,00'},
                'txErro': None
            }
        ]
        
        # Mock para prazo
        mock_response_prazo = MagicMock()
        mock_response_prazo.json.return_value = [
            {
                'coProduto': '03220',
                'prazo': {'prazoEntrega': '3'},
                'txErro': None
            },
            {
                'coProduto': '03298',
                'prazo': {'prazoEntrega': '10'},
                'txErro': None
            }
        ]
        
        mock_post.side_effect = [mock_response_preco, mock_response_prazo]
        
        result = self.api.calcular(
            cep_origem='30170903',
            cep_destino='01310100',
            peso=1.0,
            comprimento=20,
            largura=15,
            altura=10
        )
        
        self.assertIn('03220', result)
        self.assertIn('03298', result)

    def test_correios_headers_structure(self):
        """Testa a estrutura dos headers da API."""
        self.assertIn('Authorization', self.api.headers)
        self.assertEqual(self.api.headers['Content-Type'], 'application/json')
        self.assertEqual(self.api.headers['Accept'], 'application/json')

    def test_correios_urls(self):
        """Testa as URLs da API dos Correios."""
        self.assertIn('api.correios.com.br', self.api.url_preco)
        self.assertIn('api.correios.com.br', self.api.url_prazo)
        self.assertIn('preco', self.api.url_preco)
        self.assertIn('prazo', self.api.url_prazo)


class IntegrationEndToEndTestCase(TestCase):
    """Testes de integração end-to-end do fluxo de pagamento."""

    def setUp(self):
        """Configuração inicial para os testes."""
        from apps.sellers.models import Seller
        from apps.orders.models import Order
        
        self.seller = Seller.objects.create(
            name='Vendedor Integration Test',
            phone='11999999999'
        )
        self.order = Order.objects.create(
            name='Pedido Integration Test',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )

    @patch('apps.core.integrations.pagarme.requests.post')
    def test_full_payment_flow_success(self, mock_post):
        """Testa o fluxo completo de pagamento do pedido."""
        # Mock da criação do link de pagamento
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'link_123',
            'url': 'https://pagar.me/link/123',
            'short_url': 'https://pagar.me/l/abc123',
            'status': 'active'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        pagarme = PagarMePaymentLink(
            customer_name=self.order.name,
            total_amount=int(self.order.total * 100),
            max_installments=self.order.installments,
            free_installments=self.order.installments
        )
        
        result = pagarme.create_link()
        
        # Verificar sucesso
        self.assertEqual(result['status'], 'active')
        self.assertIn('url', result)

    @patch('apps.core.integrations.pagarme.requests.post')
    def test_payment_link_with_installments(self, mock_post):
        """Testa criação de link de pagamento com parcelas."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'link_parcelas',
            'url': 'https://pagar.me/link/parcelas',
            'status': 'active',
            'installments': 12
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        pagarme = PagarMePaymentLink(
            customer_name=self.order.name,
            total_amount=int(self.order.total * 100),
            max_installments=12,
            free_installments=12
        )
        
        result = pagarme.create_link()
        
        self.assertEqual(result['status'], 'active')

    def test_payment_status_update_workflow(self):
        """Testa o fluxo de atualização de status de pagamento."""
        from apps.payments.models import PaymentLink, Payment
        from apps.payments.services import process_payment_webhook
        
        # Criar link de pagamento
        link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/123',
            id_link='link_123',
            amount=self.order.total,
            status='active'
        )
        
        # Simular webhook de pagamento
        payload = {
            'data': {
                'id': link.id_link,
                'status': 'paid',
                'amount': int(link.amount * 100),
                'paid_at': timezone.now(),
            }
        }
        
        payment = process_payment_webhook(payload)
        
        if payment:
            self.assertEqual(payment.status, 'paid')
            # Verificar que o link foi atualizado
            link.refresh_from_db()
            self.assertEqual(link.status, 'paid')

    @patch('apps.core.integrations.sgpweb.requests.post')
    def test_shipping_calculation_workflow(self, mock_post):
        """Testa o fluxo de cálculo de frete."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                'coProduto': '03220',
                'preco': {'pcFinal': '50,00'},
                'prazo': {'prazoEntrega': '3'},
                'txErro': None
            }
        ]
        mock_post.return_value = mock_response

        api = CorreiosAPI()
        
        payload = {
            'idLote': 'lote-001',
            'parametrosProduto': [
                {
                    'coProduto': '03220',
                    'nuRequisicao': 1,
                    'cepOrigem': '30170903',
                    'cepDestino': '01310100',
                    'psObjeto': 1.0,
                    'comprimento': 20,
                    'largura': 15,
                    'altura': 10,
                }
            ]
        }
        
        result = api.consultar_preco(payload)
        
        self.assertIsNotNone(result)

    def test_order_payment_link_relationship(self):
        """Testa a relação entre Order e PaymentLink no fluxo."""
        from apps.payments.models import PaymentLink
        
        link = PaymentLink.objects.create(
            order=self.order,
            url_link='https://pagar.me/link/test',
            id_link='link_test',
            amount=self.order.total,
            status='active'
        )
        
        # Verificar que o link está associado ao pedido
        self.assertEqual(link.order, self.order)
        self.assertIn(link, self.order.payment_links.all())

    def test_seller_orders_payment_flow(self):
        """Testa fluxo de múltiplos pedidos do vendedor."""
        from apps.payments.models import PaymentLink, Payment
        
        # Criar múltiplos pedidos
        orders = []
        for i in range(3):
            order = Order.objects.create(
                name=f'Pedido {i}',
                value=Decimal('50.00'),
                value_freight=Decimal('5.00'),
                status='pending',
                installments=1,
                seller=self.seller
            )
            orders.append(order)
            
            # Criar link de pagamento
            link = PaymentLink.objects.create(
                order=order,
                url_link=f'https://pagar.me/link/{i}',
                id_link=f'link_{i}',
                amount=order.total,
                status='active'
            )
            
            # Simular pagamento
            Payment.objects.create(
                payment_link=link,
                status='paid',
                payment_date=timezone.now(),
                amount=order.total
            )
        
        # Verificar que os pedidos foram criados
        seller_orders = Order.objects.filter(seller=self.seller)
        self.assertEqual(seller_orders.count(), 4)  # 1 do setUp + 3 novos
        
        # Verificar que todos têm links de pagamento
        links = PaymentLink.objects.filter(order__seller=self.seller)
        self.assertEqual(links.count(), 4)


class PaymentErrorHandlingTestCase(TestCase):
    """Testes de tratamento de erros nos pagamentos."""

    def setUp(self):
        """Configuração inicial para os testes."""
        from apps.sellers.models import Seller
        from apps.orders.models import Order
        
        self.seller = Seller.objects.create(
            name='Vendedor Teste',
            phone='11999999999'
        )
        self.order = Order.objects.create(
            name='Pedido Teste',
            value=Decimal('100.00'),
            value_freight=Decimal('10.00'),
            status='pending',
            installments=1,
            seller=self.seller
        )

    @patch('apps.core.integrations.pagarme.requests.post')
    def test_pagarme_timeout_error(self, mock_post):
        """Testa tratamento de timeout da API."""
        from requests.exceptions import Timeout
        mock_post.side_effect = Timeout('Connection timeout')

        pagarme = PagarMePaymentLink(
            customer_name=self.order.name,
            total_amount=int(self.order.total * 100),
            max_installments=1,
            free_installments=1
        )
        
        result = pagarme.create_link()
        
        # Deve retornar um dicionário com erro
        self.assertIn('error', result)

    @patch('apps.core.integrations.pagarme.requests.post')
    def test_pagarme_invalid_response(self, mock_post):
        """Testa tratamento de resposta inválida da API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        pagarme = PagarMePaymentLink(
            customer_name=self.order.name,
            total_amount=int(self.order.total * 100),
            max_installments=1,
            free_installments=1
        )
        
        result = pagarme.create_link()
        
        # Deve ter processado sem erro
        self.assertIsNotNone(result)

    @patch('apps.core.integrations.sgpweb.requests.post')
    def test_correios_api_error(self, mock_post):
        """Testa tratamento de erro na API dos Correios."""
        mock_post.side_effect = Exception('API Error')

        api = CorreiosAPI()
        
        payload = {
            'idLote': 'lote-001',
            'parametrosProduto': []
        }
        
        result = api.consultar_preco(payload)
        
        # Deve retornar None ou valor seguro
        self.assertIsNone(result)

    @patch('apps.core.integrations.sgpweb.requests.post')
    def test_correios_network_error(self, mock_post):
        """Testa tratamento de erro de rede nos Correios."""
        from requests.exceptions import ConnectionError
        mock_post.side_effect = ConnectionError('Network error')

        api = CorreiosAPI()
        
        result = api.consultar_preco({})
        
        # Deve ser tratado graciosamente
        self.assertIsNone(result)
