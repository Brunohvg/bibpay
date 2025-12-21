"""
Módulo de CONSULTAS (Queries) do domínio de Pagamentos.

Responsabilidade:
- APENAS leitura de dados
- Nenhuma regra de negócio
- Nenhuma escrita no banco
- Nenhuma integração externa

Este arquivo segue o padrão CQRS:
Query = leitura
Command = escrita
"""

from decimal import Decimal
from typing import Iterable
from django.db.models import Sum, Count, Q, QuerySet

from apps.payments.models import PaymentLink, Payment


# ================================================================
# PAYMENT LINKS (LEITURA)
# ================================================================

def get_payment_links_for_order(order) -> QuerySet[PaymentLink]:
    """
    Retorna todos os links de pagamento ATIVOS de um pedido.

    Regras aplicadas:
    - Link ativo
    - Não deletado logicamente

    Uso típico:
    - Exibir links disponíveis para pagamento
    - Dashboard administrativo
    """
    return PaymentLink.objects.filter(
        order=order,
        is_active=True,
        is_deleted=False
    )


def list_active_payment_links() -> QuerySet[PaymentLink]:
    """
    Lista todos os links de pagamento ativos no sistema.

    Usado para:
    - Monitoramento
    - Tarefas administrativas
    - Relatórios
    """
    return PaymentLink.objects.filter(
        status="active",
        is_active=True,
        is_deleted=False
    )


# ================================================================
# PAYMENTS (LEITURA)
# ================================================================

def list_payments(**filters) -> QuerySet[Payment]:
    """
    Lista pagamentos ativos aplicando filtros opcionais.

    Exemplo de uso:
        list_payments(status="paid")
        list_payments(payment_link_id=1)

    Importante:
    - Apenas leitura
    - Nenhuma alteração de estado
    """
    qs = Payment.objects.filter(
        is_active=True,
        is_deleted=False
    )
    return qs.filter(**filters) if filters else qs


def list_payments_by_status(status: str) -> QuerySet[Payment]:
    """
    Retorna pagamentos filtrados por status financeiro.

    Exemplos de status:
    - pending
    - paid
    - failed
    - canceled
    """
    return Payment.objects.filter(
        status=status,
        is_deleted=False
    )


# ================================================================
# AGREGAÇÕES / CÁLCULOS
# ================================================================

def calculate_total_from_links(
    links: Iterable[PaymentLink]
) -> Decimal:
    """
    Calcula o valor total somando os valores dos links informados.

    Aceita:
    - QuerySet
    - Lista
    - Qualquer iterável de PaymentLink

    Segurança:
    - Links sem valor são tratados como zero
    """
    return sum(
        (link.amount or Decimal("0")) for link in links
    )


def get_payment_statistics(start_date=None, end_date=None) -> dict:
    """
    Retorna estatísticas financeiras agregadas do sistema.

    Métricas retornadas:
    - Total pago
    - Total pendente
    - Total cancelado
    - Total falhado
    - Quantidade por status

    Parâmetros opcionais:
    - start_date: filtra pagamentos a partir da data
    - end_date: filtra pagamentos até a data

    Retorno:
    - Dicionário com valores seguros (nunca None)
    """
    qs = Payment.objects.all()

    if start_date:
        qs = qs.filter(payment_date__gte=start_date)

    if end_date:
        qs = qs.filter(payment_date__lte=end_date)

    raw = qs.aggregate(
        total_paid=Sum("amount", filter=Q(status="paid")),
        total_pending=Sum("amount", filter=Q(status="pending")),
        total_canceled=Sum("amount", filter=Q(status="canceled")),
        total_failed=Sum("amount", filter=Q(status="failed")),
        count_paid=Count("id", filter=Q(status="paid")),
        count_pending=Count("id", filter=Q(status="pending")),
        count_canceled=Count("id", filter=Q(status="canceled")),
        count_failed=Count("id", filter=Q(status="failed")),
    )

    # Garante que nenhum valor venha como None
    return {
        key: value or Decimal("0")
        for key, value in raw.items()
    }
