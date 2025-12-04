from django.db import models
from apps.core.models import BaseModel

PAYMENT_STATUS = (
    ("pending", "Pendente"),
    ("paid", "Pago"),
    ("failed", "Falhou"),
    ("canceled", "Cancelado"),
    ("refunded", "Reembolsado"),
    ("chargeback", "Chargeback"),
)


class Payment(BaseModel, models):
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Pedido",
    )
    payment_method = models.CharField(max_length=50, verbose_name="Método de pagamento")
    payment_type = models.CharField(max_length=50, verbose_name="Tipo de pagamento")
    payment_date = models.DateTimeField(verbose_name="Data do pagamento")
    url_link = models.URLField(max_length=500, verbose_name="Link de pagamento")
    id_link = models.CharField(max_length=255, verbose_name="ID do link de pagamento")

    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    status = models.CharField(
        max_length=50, choices=PAYMENT_STATUS, default="pending", verbose_name="Status"
    )

    def __str__(self):
        return f"Pagamento {self.id} — Pedido {self.order_id} — R$ {self.amount}"

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ["-created_at"]
        db_table = "payments"



# Payment Model - Abordagem Ideal

## Problema

`Payment` está duplicando informações que já estão em `Order`:
- `installments` - já está em Order
- `amount` - já pode ser calculado de Order (value + value_freight)

---

## OPÇÃO 1: Payment MINIMALISTA (Recomendado) ✅

Armazenar **apenas o que é específico do link de pagamento**:

```python
class Payment(models.Model):
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='payments')
    
    # Do Pagar.me (específico do link)
    pagar_me_id = models.CharField(max_length=255, unique=True)
    url = models.URLField(max_length=500)
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS, default='pending')
    
    # Datas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Link {self.pagar_me_id} — {self.order.name}'
```

**Por quê:**
- `installments` → puxar de `payment.order.installments`
- `amount` → puxar de `payment.order.total`
- `payment_method` → sempre `credit_card` (hardcoded no service)

**Na prática:**
```python
payment = Payment.objects.get(id=1)
payment.order.installments  # 3 parcelas
payment.order.total         # R$ 100,00
```

---

## OPÇÃO 2: Payment COM TUDO DO RETORNO DA API ✅

Armazenar **exatamente o que o Pagar.me retorna** (mais dados para auditoria):

```python
class Payment(models.Model):
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='payments')
    
    # Retorno da API do Pagar.me (salvar tudo)
    pagar_me_id = models.CharField(max_length=255, unique=True)
    url = models.URLField(max_length=500)
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS, default='pending')
    
    # Dados salvos no momento da criação
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    installments = models.IntegerField(default=1)
    payment_method = models.CharField(max_length=50, default='credit_card')
    
    # Resposta completa da API (para auditoria/debug)
    api_response = models.JSONField(default=dict)
    
    # Datas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Link {self.pagar_me_id} — {self.order.name}'
```

**Por quê:**
- Histórico completo de tudo que foi salvo
- Fácil auditar/debugar problemas
- Independente se Order mudar
- Rastreabilidade total

**Na prática:**
```python
payment = Payment.objects.get(id=1)
payment.amount          # 10000 (centavos quando foi criado)
payment.installments    # 3 (exatamente como pedido)
payment.api_response    # { "id": "...", "url": "...", ... }
```

---

## COMPARAÇÃO

| Aspecto | Opção 1 (Minimalista) | Opção 2 (Com Tudo) |
|--------|----------------------|-------------------|
| **Simplicidade** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Integridade de dados** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Auditoria** | Difícil | Fácil |
| **Mudança futura** | Quebra se Order mudar | Seguro |
| **Banco de dados** | Menor | Maior |
| **Para startup** | ✅ Perfeito | ⚠️ Overhead |
| **Para empresa** | ⚠️ Risco | ✅ Profissional |

---

## RECOMENDAÇÃO

### Para seu caso (Loja Bibelô):

**👉 Use OPÇÃO 2 (Com Tudo da API)**

**Por quê:**
1. Você usa webhook - precisa rastrear tudo
2. Pode ter problemas de sincronização - `api_response` ajuda a debugar
3. Order pode mudar - seu Payment fica independente
4. Pequeno overhead (JSON é comprimido no banco)

**Código final:**

```python
from django.db import models

PAYMENT_STATUS = (
    ('pending', 'Pendente'),
    ('paid', 'Pago'),
    ('failed', 'Falhou'),
    ('canceled', 'Cancelado'),
    ('refunded', 'Reembolsado'),
    ('chargeback', 'Chargeback'),
)

class Payment(models.Model):
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Pedido'
    )
    
    # Do Pagar.me
    pagar_me_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='ID Pagar.me'
    )
    url = models.URLField(
        max_length=500,
        verbose_name='Link de pagamento'
    )
    status = models.CharField(
        max_length=50,
        choices=PAYMENT_STATUS,
        default='pending',
        verbose_name='Status'
    )
    
    # Snapshot do pedido (salvo no momento da criação)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor'
    )
    installments = models.IntegerField(
        default=1,
        verbose_name='Parcelas'
    )
    payment_method = models.CharField(
        max_length=50,
        default='credit_card',
        verbose_name='Método de pagamento'
    )
    
    # Resposta completa da API
    api_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Resposta da API'
    )
    
    # Datas
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data do pagamento'
    )

    def __str__(self):
        return f'Pagamento {self.pagar_me_id} — {self.order.name}'

    class Meta:
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-created_at']
        db_table = 'payments'
```

**No service:**

```python
def create_payment_link(order_id):
    order = get_object_or_404(Order, id=order_id)
    total_amount = int((order.value + order.value_freight) * 100)
    
    link_generator = PagarMePaymentLink(
        customer_name=order.name,
        total_amount=total_amount,
        max_installments=order.installments,
        free_installments=order.installments
    )
    
    response = link_generator.create_link()
    
    if 'error' in response:
        raise Exception(f"Erro Pagar.me: {response['error']}")
    
    # Salvar tudo que veio da API
    payment = Payment.objects.create(
        order=order,
        pagar_me_id=response.get('id'),
        url=response.get('url'),
        status=response.get('status', 'pending'),
        amount=order.total,
        installments=order.installments,
        payment_method='credit_card',
        api_response=response  # ← Salvar resposta completa
    )
    
    return payment


"""

def create_payment_link(order_id):
    order = get_object_or_404(Order, id=order_id)
    total_amount = int((order.value + order.value_freight) * 100)
    
    link_generator = PagarMePaymentLink(
        customer_name=order.name,
        total_amount=total_amount,
        max_installments=order.installments,
        free_installments=order.installments
    )
    
    response = link_generator.create_link()
    
    if 'error' in response:
        raise Exception(f"Erro Pagar.me: {response['error']}")
    
    # Salvar tudo que veio da API
    payment = Payment.objects.create(
        order=order,
        pagar_me_id=response.get('id'),
        url=response.get('url'),
        status=response.get('status', 'pending'),
        amount=order.total,
        installments=order.installments,
        payment_method='credit_card',
        api_response=response  # ← Salvar resposta completa
    )
    
    return payment
"""