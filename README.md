# BibPay - Sistema de Gerenciamento de Pedidos e Pagamentos

BibPay é uma aplicação Django completa para gerenciamento de pedidos e pagamentos integrada com gateways de pagamento (Pagar.me e SGPWeb). O sistema foi desenvolvido para facilitar a gestão de vendedores, pedidos, links de pagamento e histórico de transações.

## 📋 Sobre o Projeto

BibPay é uma plataforma robusta que permite:

- **Gestão de Vendedores**: Cadastro e gerenciamento de vendedores com telefone de contato
- **Gerenciamento de Pedidos**: Criação, visualização e acompanhamento de pedidos com valores e fretes
- **Sistema de Pagamentos**: Geração de links de pagamento e rastreamento de transações
- **Integração com Gateways**: Suporte para Pagar.me e SGPWeb
- **Dashboard**: Painel administrativo para visualização de dados e histórico de pedidos
- **Autenticação e Autorização**: Sistema de contas de usuário com login, logout e recuperação de senha

## 🛠️ Tecnologias Utilizadas

- **Backend**: Django 5.2.8
- **API**: Django REST Framework 3.16.1
- **Banco de Dados**: SQLite3
- **Requisições HTTP**: Requests 2.32.5
- **Configuração**: Python Decouple 3.8
- **Python**: 3.14+

## 📁 Estrutura do Projeto

```
bibpay/
├── apps/
│   ├── accounts/           # Aplicação de autenticação de usuários
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── admin.py
│   │   └── templates/
│   │       └── accounts/   # Templates de login, signup, reset de senha
│   ├── core/               # Funcionalidades principais e integrações
│   │   ├── models.py       # BaseModel para timestamps
│   │   └── integrations/
│   │       ├── pagarme.py  # Integração com Pagar.me
│   │       └── sgpweb.py   # Integração com SGPWeb
│   ├── orders/             # Gerenciamento de pedidos
│   │   ├── models.py       # Modelo de Pedidos
│   │   ├── views.py        # Visualizações de pedidos
│   │   ├── urls.py
│   │   ├── services.py     # Lógica de negócio
│   │   ├── signals.py      # Sinais Django
│   │   ├── utils.py        # Funções utilitárias
│   │   └── templates/
│   ├── payments/           # Gerenciamento de pagamentos
│   │   ├── models.py       # Modelos de Pagamento e Link de Pagamento
│   │   ├── views.py
│   │   ├── services.py
│   │   └── templates/
│   ├── sellers/            # Gerenciamento de vendedores
│   │   ├── models.py       # Modelo de Vendedor
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── services.py
│   └── dashboard/          # Painel de controle
│       ├── views.py
│       ├── urls.py
│       └── templates/
│
├── config/                 # Configurações do Django
│   ├── settings.py        # Configurações principais
│   ├── urls.py            # URLs principais
│   ├── wsgi.py
│   └── asgi.py
│
├── templates/             # Templates globais
│   ├── base.html
│   └── base_auth.html
│
├── static/               # Arquivos estáticos (CSS, JS)
│   └── assets/
│       └── styles.css
│
├── manage.py
├── main.py
├── pyproject.toml
└── README.md
```

## 📊 Modelos de Dados

### Order (Pedido)
```python
- name: CharField          # Nome do pedido
- value: DecimalField      # Valor do pedido
- value_freight: DecimalField  # Valor do frete
- total: DecimalField      # Total (value + frete)
- status: CharField        # Choices: 'paid', 'pending', 'canceled'
- installments: IntegerField   # Número de parcelas
- seller: ForeignKey       # Referência a Seller
- created_at: DateTimeField    # Criado em
- updated_at: DateTimeField    # Atualizado em
```

### Payment (Pagamento)
```python
- payment_link: OneToOneField   # Referência única a PaymentLink
- status: CharField             # Choices: 'pending', 'paid', 'failed', 'canceled', 'refunded', 'chargeback'
- payment_date: DateTimeField   # Data do pagamento
- amount: DecimalField          # Valor do pagamento
- created_at: DateTimeField     # Criado em
- updated_at: DateTimeField     # Atualizado em
```

### PaymentLink (Link de Pagamento)
```python
- order: ForeignKey        # Referência a Order
- url_link: URLField       # URL do link de pagamento
- id_link: CharField       # ID do link do gateway
- amount: DecimalField     # Valor do link
- status: CharField        # Choices: 'active', 'pending', 'inactive', 'expired', 'paid', 'canceled'
- created_at: DateTimeField
- updated_at: DateTimeField
```

### Seller (Vendedor)
```python
- name: CharField          # Nome do vendedor
- phone: CharField         # Telefone de contato
- created_at: DateTimeField
- updated_at: DateTimeField
```

## 🚀 Primeiros Passos

### Pré-requisitos
- Python 3.14 ou superior
- pip (gerenciador de pacotes Python)

### Instalação

1. **Clone o repositório**
   ```bash
   git clone <url-do-repositorio>
   cd bibpay
   ```

2. **Crie um ambiente virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -e .
   ```
   Ou manualmente:
   ```bash
   pip install django>=5.2.8 djangorestframework>=3.16.1 python-decouple>=3.8 requests>=2.32.5
   ```

4. **Execute as migrações do banco de dados**
   ```bash
   python manage.py migrate
   ```

5. **Crie um super usuário para o admin**
   ```bash
   python manage.py createsuperuser
   ```

6. **Inicie o servidor de desenvolvimento**
   ```bash
   python manage.py runserver
   ```

O servidor estará disponível em `http://localhost:8000`

## 📝 Funcionalidades Principais

### Autenticação
- Login de usuários
- Cadastro de novos usuários
- Logout
- Recuperação de senha
- Reset de senha

### Gerenciamento de Pedidos
- Criar novos pedidos
- Visualizar lista de pedidos
- Atualizar status de pedidos
- Calcular total com valor de frete
- Rastrear pedidos por vendedor

### Gerenciamento de Pagamentos
- Gerar links de pagamento
- Rastrear status de pagamentos
- Histórico de transações
- Integração com gateways de pagamento
- Suporte a múltiplas parcelas

### Dashboard
- Visualização geral de pedidos
- Filtros e busca
- Estatísticas de pagamentos
- Histórico de transações

### Integrações de Pagamento
- **Pagar.me**: Gateway de pagamento brasileiro
- **SGPWeb**: Integração adicional de processamento de pagamentos

## ⚙️ Configurações

### Variáveis de Ambiente
As seguintes variáveis podem ser configuradas via `.env` utilizando `python-decouple`:

```
SECRET_KEY=sua-chave-secreta
DEBUG=False  # Em produção
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Banco de Dados
O projeto utiliza SQLite como banco de dados padrão, armazenado em `db.sqlite3`. Para produção, recomenda-se usar PostgreSQL.

## 🔌 Integrações com Gateways

### Pagar.me
A integração com Pagar.me está localizada em `apps/core/integrations/pagarme.py` e permite:
- Geração de links de pagamento
- Rastreamento de transações
- Processamento de webhooks

### SGPWeb
A integração com SGPWeb está localizada em `apps/core/integrations/sgpweb.py`

## 📱 URLs Disponíveis

- `/admin/` - Painel administrativo Django
- `/orders/` - Gerenciamento de pedidos
- `/dashboard/` - Dashboard principal
- `/accounts/login/` - Página de login
- `/accounts/signup/` - Página de cadastro

## 🧪 Testes

Para executar os testes:
```bash
python manage.py test
```

Testes estão disponíveis em:
- `apps/accounts/tests.py`
- `apps/dashboard/tests.py`
- `apps/orders/tests.py`
- `apps/payments/tests.py`
- `apps/sellers/tests.py`

## 🔒 Segurança

- ✅ Proteção CSRF ativada
- ✅ Validação de entrada de dados
- ✅ Autenticação de usuários
- ✅ Senhas com hash seguro (Django)

### Checklist de Segurança para Produção
- [ ] Alterar `SECRET_KEY` para uma chave segura e aleatória
- [ ] Definir `DEBUG = False`
- [ ] Configurar `ALLOWED_HOSTS` com domínios corretos
- [ ] Usar HTTPS em produção
- [ ] Configurar banco de dados de produção (PostgreSQL)
- [ ] Implementar logs de segurança
- [ ] Configurar CORS corretamente para requisições da API

## 🐛 Solução de Problemas

### Erro: "ModuleNotFoundError"
```bash
pip install -e .
```

### Erro de migração
```bash
python manage.py makemigrations
python manage.py migrate
```

### Banco de dados corrompido
```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## 📚 Documentação Adicional

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Documentação Pagar.me](https://docs.pagar.me)

## 👥 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 📞 Suporte

Para suporte, abra uma issue no repositório ou entre em contato com a equipe de desenvolvimento.

---

**Desenvolvido com ❤️ usando Django**
