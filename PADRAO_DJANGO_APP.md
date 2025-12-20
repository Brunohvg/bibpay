# 🎯 ROTEIRO COMPLETO DJANGO PARA INICIANTE AUTODIDATA

## ⚠️ VERDADE INCÔMODA
Você vai:
- ❌ Errar muitas vezes
- ❌ Refatorar código que “funcionava”
- ❌ Ver padrão diferente em outro projeto e ficar confuso
- ❌ Levar 3–6 meses pra internalizar isso

👉 **Isso é NORMAL.**  
👉 **Seguindo este documento, você erra 70% menos.**

---

## 📚 PRÉ-REQUISITOS

### Obrigatório (aprenda ANTES)
- Python básico (funções, dict, classes)
- Django básico (models, views, urls, templates)
- Rodar projeto local (`runserver`)
- Git básico (commit, push, pull)

❗ Se não sabe isso: **pare aqui e estude 30–40h de Django.**

### NÃO precisa agora
- DRF avançado
- Async/Await
- Testes
- Docker
- Celery

**Ordem correta:**  
Estrutura → Básico → Testes → Async → Containers

---

## 🎓 INICIANTE VS PROFISSIONAL

### ❌ Iniciante (ERRADO)
```python
def criar_pedido(request):
    cliente = request.POST.get("cliente")
    valor = request.POST.get("valor")

    if valor <= 0:
        return render(request, "erro.html")

    pedido = Pedido.objects.create(cliente=cliente, valor=valor)

    if valor > 1000:
        enviar_email_admin()
        criar_boleto()

    return render(request, "sucesso.html")

✅ Profissional (CERTO)
def criar_pedido(request):
    try:
        pedido = CriarPedidoService.execute({
            "cliente_nome": request.POST.get("cliente_nome"),
            "valor": request.POST.get("valor"),
        })
        return redirect("pedidos:detalhe", pk=pedido.id)
    except ValueError as e:
        return render(request, "criar.html", {"erro": str(e)})


👉 View coordena. Service trabalha. Domain valida.

🧠 CONCEITO CENTRAL
O CAOS
View → banco
View → validação
View → email
View → API externa
View → cálculo
View → histórico

A SOLUÇÃO
View → Service → Domain → Model


Cada camada com uma responsabilidade.

🧱 OS 5 PILARES
1️⃣ MODELS — Estrutura de dados
class Pedido(models.Model):
    STATUS = [
        ("pendente", "Pendente"),
        ("aprovado", "Aprovado"),
        ("cancelado", "Cancelado"),
    ]

    cliente_nome = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS)
    criado_em = models.DateTimeField(auto_now_add=True)


❌ Nunca coloque regra de negócio no model.

2️⃣ DOMAIN — Regras de negócio (pura lógica)
class PedidoRegras:

    @staticmethod
    def pode_cancelar(pedido) -> bool:
        return pedido.status == "pendente"

    @staticmethod
    def validar_dados(dados: dict) -> dict:
        if not dados.get("cliente_nome"):
            raise ValueError("Cliente obrigatório")

        if dados.get("valor", 0) <= 0:
            raise ValueError("Valor inválido")

        return dados


✔ Sem banco
✔ Sem request
✔ Só regra

3️⃣ SERVICES — Ações do sistema
class CriarPedidoService:

    @staticmethod
    def execute(dados: dict) -> Pedido:
        dados = PedidoRegras.validar_dados(dados)

        pedido = Pedido.objects.create(
            cliente_nome=dados["cliente_nome"],
            valor=dados["valor"],
        )

        return pedido


✔ Orquestra
✔ Chama domain
✔ Salva no banco
✔ Retorna model

4️⃣ WEB VIEWS — HTML
def criar_pedido(request):
    if request.method == "POST":
        try:
            CriarPedidoService.execute({
                "cliente_nome": request.POST.get("cliente_nome"),
                "valor": float(request.POST.get("valor")),
            })
            return redirect("pedidos:listar")
        except ValueError as e:
            return render(request, "criar.html", {"erro": str(e)})

    return render(request, "criar.html")


✔ View não valida
✔ View não acessa banco
✔ View só coordena

5️⃣ API VIEWS — JSON
class PedidoAPIView(APIView):

    def post(self, request):
        try:
            pedido = CriarPedidoService.execute(request.data)
            serializer = PedidoSerializer(pedido)
            return Response(serializer.data, status=201)
        except ValueError as e:
            return Response({"erro": str(e)}, status=400)


✔ API = JSON
✔ Service = regra
✔ Serializer = conversão

📂 ESTRUTURA PADRÃO DO APP
apps/pedidos/
├── api/
│   └── v1/
│       ├── urls.py
│       ├── views.py
│       └── serializers.py
├── domain/
│   └── regras.py
├── services/
│   ├── criar_pedido.py
│   ├── cancelar_pedido.py
│   └── listar_pedidos.py
├── web/
│   └── views.py
├── templates/pedidos/
├── models.py
├── urls.py
└── admin.py

🚫 ERROS CLÁSSICOS

❌ Regra na view
❌ Domain acessando banco
❌ API chamando model direto
❌ Service gigante
❌ Código sem docstring

👉 Se fez algum desses: refatora.

✅ CHECKLIST FINAL
Models

 Só estrutura

 Sem regra

 __str__

Domain

 Sem banco

 Sem request

 Regras claras

Services

 ≤ 30 linhas

 Chamam domain

 Retornam model

Views

 Só coordenação

 Tratam exceções

API

 Versionada (v1)

 Usa service

 Usa serializer

🧠 RESUMO RÁPIDO
Camada	Faz
Model	Estrutura
Domain	Regras
Service	Ações
View	HTML
API	JSON
🏁 CONCLUSÃO

✔ Funciona em projeto real
✔ Escala
✔ Outro dev entende
✔ Você para de sofrer

👉 Use isso como padrão SEMPRE.
👉 Copia, cola, adapta e segue o jogo.

Agora vai codar. 🚀


apps/
└── <app_name>/
    ├── api/
    │   └── v1/
    │       ├── urls.py
    │       ├── views.py
    │       └── serializers.py
    │
    ├── web/
    │   └── views.py
    │
    ├── domain/
    │   └── rules.py
    │
    ├── services/
    │   ├── commands.py
    │   └── queries.py
    │
    ├── signals.py
    ├── models.py
    ├── urls.py
    └── admin.py
