# ==================================================================
# ARQUIVO COMPLETO: apps/dashboard/views.py
# ==================================================================
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Q, F, Prefetch
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.views.generic import TemplateView

# Importações dos seus modelos 
from apps.payments.models import Payment, PaymentLink
from apps.sellers.models import Seller


class DashboardHomeView(TemplateView):
    """
    Dashboard principal otimizado para a estrutura OneToOneField (PaymentLink -> Payment).
    """

    template_name = "dashboard/dashboard.html"

    # ==================================================================
    # AUXILIARES
    # ==================================================================

    def _get_status_display(self, link, payment):
        """
        Retorna o status visual baseado no Payment (se existir).
        Se não houver Payment, usa o status do Link.
        """
        payment_status_map = {
            "paid": {"class": "success", "icon": "check-circle-fill", "label": "Pago"},
            "pending": {"class": "warning", "icon": "clock-fill", "label": "Pendente"},
            "canceled": {"class": "danger", "icon": "x-circle-fill", "label": "Cancelado"},
            "failed": {"class": "danger", "icon": "x-circle-fill", "label": "Falhou"},
            "refunded": {"class": "info", "icon": "arrow-counterclockwise", "label": "Reembolsado"},
            "chargeback": {"class": "danger", "icon": "exclamation-triangle-fill", "label": "Chargeback"},
        }

        # Se houver objeto Payment associado (link.payment)
        if payment:
            return payment_status_map.get(payment.status, payment_status_map["pending"])

        # Se não houver Payment, usa o status do Link (que é atualizado pelo webhook)
        link_status_map = {
            "active": {"class": "warning", "icon": "clock-fill", "label": "Aguardando"},
            "pending": {"class": "warning", "icon": "clock-fill", "label": "Pendente"},
            "expired": {"class": "info", "icon": "hourglass-split", "label": "Expirado"},
            "inactive": {"class": "secondary", "icon": "dash-circle", "label": "Inativo"},
            # Adicionamos os status finais aqui para cobrir a sincronização do webhook (paid/canceled)
            "paid": {"class": "success", "icon": "check-circle-fill", "label": "Pago"},
            "canceled": {"class": "danger", "icon": "x-circle-fill", "label": "Cancelado"},
        }
        
        return link_status_map.get(link.status, link_status_map["pending"])

    def _calculate_days_ago(self, date):
        """Calcula quantos dias atrás foi a data."""
        days = (timezone.now() - date).days
        if days == 0:
            return "Hoje"
        if days == 1:
            return "Ontem"
        return f"{days} dias"

    def _get_chart_data(self, start_date):
        """
        Retorna dados dos últimos 7 dias para o gráfico. Otimizado com TruncDate.
        """
        today = timezone.now().date()
        weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        
        # Consulta ÚNICA para obter a contagem por data
        counts_by_date = (
            PaymentLink.objects.filter(created_at__date__gte=start_date.date())
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        
        counts_map = {item['date']: item['count'] for item in counts_by_date}
        chart_data = []

        all_dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
        
        for date in all_dates:
            count = counts_map.get(date, 0)
            chart_data.append(
                {
                    "day": "Hoje" if date == today else weekdays[date.weekday()],
                    "count": count,
                    "is_today": date == today,
                }
            )

        # Cálculo da altura relativa para o gráfico (normalização)
        max_count = max((d["count"] for d in chart_data), default=1)
        for data in chart_data:
            # Garante que a altura é calculada corretamente, mas não força um min-height aqui.
            # O min-height fica no CSS (já está como 5% no template).
            data["height"] = int((data["count"] / max_count) * 100) if max_count > 0 else 0

        return chart_data
    
    # ==================================================================
    # MÉTODO PRINCIPAL
    # ==================================================================

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Datas de referência
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)
        
        # ------------------------------------------------------------------
        # 1. AGREGAÇÃO CONSOLIDADA (PAGAMENTOS e LINKS - 30 dias)
        # ------------------------------------------------------------------
        # Uma única consulta ao banco para Payments (DB Hit 1)
        payments_stats = Payment.objects.filter(
            payment_date__gte=thirty_days_ago
        ).aggregate(
            # Valores
            total_received=Sum('amount', filter=Q(status='paid')),
            total_canceled_value=Sum('amount', filter=Q(status='canceled')),
            
            # Contagens
            total_pagos=Count('id', filter=Q(status='paid')),
            total_pendentes=Count('id', filter=Q(status='pending')),
            total_cancelados=Count('id', filter=Q(status='canceled')),
            total_falhados=Count('id', filter=Q(status='failed')),
        )
        
        # Uma única consulta ao banco para Links (DB Hit 2)
        links_qs = PaymentLink.objects.filter(created_at__gte=thirty_days_ago)
        
        links_stats = links_qs.aggregate(
            total_criados=Count("id"),
            total_expirados=Count("id", filter=Q(status="expired")),
            total_inativos=Count("id", filter=Q(status="inactive")),
        )
        
        # Atribuição de valores base
        total_received = payments_stats.get("total_received") or Decimal("0")
        total_links = links_stats["total_criados"]
        total_pagos = payments_stats["total_pagos"]
        total_canceled_value = payments_stats.get("total_canceled_value") or Decimal("0")
        
        # ------------------------------------------------------------------
        # 2. PIPELINE E VALOR EM ABERTO (Corrigido para OneToOneField)
        # ------------------------------------------------------------------
        
        # Links que NÃO têm um Payment com status 'paid'
        links_em_aberto_qs = links_qs.filter(status__in=["active", "pending"]).exclude(
            payment__status='paid' # Usa o related_name 'payment' do OneToOneField
        )
        
        valor_em_aberto = links_em_aberto_qs.aggregate(total=Sum("amount")).get("total") or Decimal("0")
        total_links_ativos_nao_pagos = links_em_aberto_qs.count() # Contagem correta de links em aberto

        # ------------------------------------------------------------------
        # 3. MÉTRICAS DERIVADAS
        # ------------------------------------------------------------------

        taxa_conversao = (
            round((total_pagos / total_links) * 100)
            if total_links > 0
            else 0
        )

        ticket_medio = (
            total_received / total_pagos
            if total_pagos > 0
            else Decimal("0")
        )
        
        # Total de Vendedores (DB Hit 3)
        total_sellers = Seller.objects.filter(is_active=True).count()


        # ------------------------------------------------------------------
        # 4. LINKS RECENTES (N+1 Resolvido com select_related)
        # ------------------------------------------------------------------
        
        # select_related pode buscar os campos da Foreign/OneToOneKey (Order, Seller, Payment)
        # em uma única consulta (DB Hit 4)
        recent_links = (
            PaymentLink.objects.filter(created_at__gte=thirty_days_ago)
            .select_related("order", "order__seller", "payment") 
            .order_by("-created_at")[:4]
        )

        links_data = []
        for link in recent_links:
            # Acessando o Payment via related_name='payment'
            payment_obj = getattr(link, 'payment', None) 
            
            links_data.append(
                {
                    "link": link,
                    "order": link.order,
                    "payment": payment_obj,
                    "status_display": self._get_status_display(link, payment_obj),
                    "days_ago": self._calculate_days_ago(link.created_at),
                }
            )

        # ------------------------------------------------------------------
        # 5. GRÁFICO E CRESCIMENTO SEMANAL (Otimizado)
        # ------------------------------------------------------------------
        
        chart_data = self._get_chart_data(seven_days_ago) # DB Hit 5 (do auxiliar)
        
        # Comparativo Semanal (DB Hit 6 e 7)
        this_week_total = (
            Payment.objects.filter(status="paid", payment_date__gte=seven_days_ago)
            .aggregate(total=Sum("amount")).get("total") or Decimal("0")
        )

        last_week_total = (
            Payment.objects.filter(
                status="paid",
                payment_date__gte=fourteen_days_ago,
                payment_date__lt=seven_days_ago,
            )
            .aggregate(total=Sum("amount")).get("total") or Decimal("0")
        )

        if last_week_total > 0:
            week_growth = round(((this_week_total - last_week_total) / last_week_total) * 100)
        else:
            week_growth = 100 if this_week_total > 0 else 0


        # ==================================================================
        # CONTEXTO FINAL
        # ==================================================================

        context.update(
            {
                # Financeiro real
                "volume_processado": total_received,
                "total_received": total_received,
                "total_canceled": total_canceled_value, # Valor cancelado
                "total_failed": payments_stats.get("total_failed") or Decimal("0"),

                # Pipeline (corrigido)
                "valor_em_aberto": valor_em_aberto, 
                "total_links_ativos": total_links_ativos_nao_pagos, # Contagem de links em aberto

                # Pagamentos (Contagens)
                "total_pagos": total_pagos,
                "total_pendentes": payments_stats["total_pendentes"],
                "total_cancelados": payments_stats["total_cancelados"], # Contagem de cancelados
                "total_falhados": payments_stats["total_falhados"],

                # Links
                "total_links_criados": total_links,
                "total_links_expirados": links_stats["total_expirados"],
                "total_links_inativos": links_stats["total_inativos"],

                # Métricas
                "taxa_conversao": taxa_conversao,
                "ticket_medio": ticket_medio,
                "total_sellers": total_sellers,

                # UI / Gráfico
                "recent_links": links_data,
                "chart_data": chart_data,
                "this_week_total": this_week_total,
                "last_week_total": last_week_total,
                "week_growth": week_growth,
                "week_growth_positive": week_growth >= 0,
            }
        )

        return context