# Guia de Testes - BibPay

Este documento descreve como executar os testes do projeto BibPay.

## 📋 Estrutura de Testes

Os testes estão organizados em diferentes aplicações Django:

```
bibpay/
├── apps/
│   ├── accounts/tests.py          # Testes de autenticação
│   ├── orders/tests.py            # Testes de pedidos
│   ├── payments/tests.py          # Testes de pagamentos
│   ├── sellers/tests.py           # Testes de vendedores
│   ├── dashboard/tests.py         # Testes do dashboard
│   ├── core/
│   │   ├── tests.py               # Testes do modelo BaseModel
│   │   └── integrations/tests.py  # Testes de integrações (Pagar.me, SGPWeb)
│
├── tests_integration.py           # Testes de integração end-to-end
└── conftest.py                    # Fixtures para pytest
```

## 🚀 Executando os Testes

### Com Django TestCase (Recomendado para começar)

Para executar **todos os testes**:

```bash
python manage.py test
```

Para executar testes de uma **aplicação específica**:

```bash
python manage.py test apps.accounts          # Testes de contas
python manage.py test apps.orders            # Testes de pedidos
python manage.py test apps.payments          # Testes de pagamentos
python manage.py test apps.sellers           # Testes de vendedores
python manage.py test apps.dashboard         # Testes do dashboard
python manage.py test apps.core              # Testes do core
```

Para executar **uma classe de teste específica**:

```bash
python manage.py test apps.accounts.tests.UserAuthenticationTestCase
```

Para executar **um método de teste específico**:

```bash
python manage.py test apps.accounts.tests.UserAuthenticationTestCase.test_user_login
```

Para executar **com verbosidade detalhada**:

```bash
python manage.py test --verbosity=2
```

### Com pytest (Alternativa)

Se preferir usar pytest (mais moderno), instale primeiro:

```bash
pip install pytest pytest-django
```

Crie um arquivo `pytest.ini` na raiz do projeto:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
addopts = --tb=short --strict-markers
```

Então execute:

```bash
# Todos os testes
pytest

# Testes de uma aplicação
pytest apps/accounts/tests.py

# Testes com cobertura
pytest --cov=apps

# Testes com marcadores
pytest -m unit
pytest -m integration
pytest -m slow
```

## 📊 Cobertura de Testes

Para gerar um relatório de cobertura de testes:

```bash
pip install coverage

# Executar com cobertura
coverage run --source='apps' manage.py test

# Gerar relatório em HTML
coverage html

# Visualizar relatório
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🧪 Tipos de Testes

### Testes Unitários

Testam funcionalidades isoladas de uma única unidade de código:

- **accounts/tests.py**: Testes de criação, login e gerenciamento de usuários
- **sellers/tests.py**: Testes de CRUD de vendedores
- **orders/tests.py**: Testes de criação e validação de pedidos
- **payments/tests.py**: Testes de modelos e serviços de pagamento
- **core/tests.py**: Testes do BaseModel

### Testes de Integração

Testam como múltiplos componentes trabalham juntos:

- **dashboard/tests.py**: Testes de agregação de dados
- **tests_integration.py**: Testes end-to-end do fluxo completo de pagamento

### Testes de API/Integração Externa

Testam a integração com serviços externos (com mocks):

- **core/integrations/tests.py**: Testes do Pagar.me e CorreiosAPI

## 🎯 Casos de Teste Principais

### Accounts
- ✅ Criar usuário
- ✅ Login com credenciais corretas/incorretas
- ✅ Logout
- ✅ Alterar senha
- ✅ Criar superusuário

### Orders
- ✅ Criar pedido
- ✅ Cálculo automático do total
- ✅ Atualizar status
- ✅ Listar e filtrar pedidos
- ✅ Remover pedido

### Payments
- ✅ Criar link de pagamento
- ✅ Processar webhook de pagamento
- ✅ Sincronizar status entre Payment, PaymentLink e Order
- ✅ Relação OneToOne entre Payment e PaymentLink
- ✅ Listar pagamentos por status

### Sellers
- ✅ Criar vendedor
- ✅ Atualizar dados do vendedor
- ✅ Listar e filtrar vendedores
- ✅ Deletar vendedor
- ✅ Soft delete (marcação lógica)

### Dashboard
- ✅ Acessibilidade da view
- ✅ Contagem de pedidos pagos/pendentes
- ✅ Cálculo de receita total
- ✅ Estatísticas por vendedor
- ✅ Filtros por data

### Core & Integrações
- ✅ Timestamps automáticos (created_at, updated_at)
- ✅ Campos de soft delete (is_deleted, deleted_at)
- ✅ Integração com Pagar.me (com mocks)
- ✅ Integração com CorreiosAPI (com mocks)

## 📝 Executando Testes Específicos

### Exemplo 1: Testar fluxo de pagamento
```bash
python manage.py test apps.payments.tests.PaymentServiceTestCase
```

### Exemplo 2: Testar apenas modelos de Orders
```bash
python manage.py test apps.orders.tests.OrderModelTestCase
```

### Exemplo 3: Testar um caso específico
```bash
python manage.py test apps.accounts.tests.UserAuthenticationTestCase.test_user_login
```

### Exemplo 4: Testes de integração end-to-end
```bash
python manage.py test tests_integration.EndToEndPaymentFlowTestCase
```

## 🔍 Verificando Testes Falhando

Se um teste falhar, você verá:

```
FAIL: test_user_login (apps.accounts.tests.UserAuthenticationTestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/path/to/tests.py", line X, in test_user_login
    self.assertTrue(logged_in)
AssertionError: False != True
```

### Passos para debug:

1. **Leia a mensagem de erro** com atenção
2. **Execute com verbosidade aumentada**:
   ```bash
   python manage.py test --verbosity=2
   ```
3. **Use pdb (Python Debugger)**:
   ```python
   import pdb; pdb.set_trace()  # Adicione em seu teste
   ```
4. **Verifique o banco de dados de teste**:
   ```bash
   python manage.py shell
   >>> from apps.orders.models import Order
   >>> Order.objects.all()
   ```

## 🛠️ Manutenção de Testes

### Adicionando Novos Testes

1. Abra o arquivo `apps/seu_app/tests.py`
2. Adicione uma nova classe TestCase:

```python
class NovoTestCase(TestCase):
    def setUp(self):
        # Setup inicial
        pass

    def test_funcionalidade_nova(self):
        # Teste aqui
        self.assertTrue(condicao)
```

3. Execute para verificar:
```bash
python manage.py test apps.seu_app.tests.NovoTestCase.test_funcionalidade_nova
```

### Modificando Testes Existentes

Ao alterar o código de produção, atualize também os testes correspondentes:

1. Localize o teste relacionado
2. Atualize as asserções se necessário
3. Execute novamente para confirmar

## 📚 Recursos Úteis

- [Django Testing Documentation](https://docs.djangoproject.com/en/5.2/topics/testing/)
- [pytest-django Documentation](https://pytest-django.readthedocs.io/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)

## ✅ Checklist de Testes Antes de Deploy

- [ ] Todos os testes passam: `python manage.py test`
- [ ] Cobertura está acima de 80%: `coverage report`
- [ ] Não há warnings ou deprecations
- [ ] Testes de integração passam
- [ ] Documentação dos testes está atualizada

## 🚨 Troubleshooting

### "No such table" error
```bash
python manage.py migrate
```

### Testes lentos
- Use `--keepdb` para manter o banco de teste entre execuções
- Reduza o número de fixtures ou use factories ao invés

### Testes aleatoriamente falhando
- Verifique se há dependência entre testes
- Use `--shuffle` para randomizar a ordem
- Revise o setUp/tearDown

---

**Dica:** Sempre execute os testes antes de fazer commit! 🧪
