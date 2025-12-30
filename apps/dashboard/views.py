# ==================================================================
# apps/dashboard/views.py
# Dashboard = QUERY / READ SIDE
# Responsabilidade:
# - Ler dados
# - Agregar métricas
# - Preparar contexto para UI
#
# NÃO:
# - Dispara comandos
# - Altera estado
# - Contém regra de negócio
# ==================================================================

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.views.generic import TemplateView

from apps.payments.models import Payment, PaymentLink
from apps.sellers.models import Seller


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    # ==============================================================
    # STATUS VISUAL (UI ONLY)
    # ==============================================================

    def _get_status_display(self, link, payment):
        payment_status_map = {
            "paid": {"class": "success", "icon": "check-circle-fill", "label": "Pago"},
            "processing": {"class": "warning", "icon": "arrow-repeat", "label": "Processando"},
            "pending": {"class": "warning", "icon": "clock-fill", "label": "Pendente"},
            "failed": {"class": "danger", "icon": "x-circle-fill", "label": "Falhou"},
            "canceled": {"class": "danger", "icon": "x-circle-fill", "label": "Cancelado"},
            "refunded": {"class": "info", "icon": "arrow-counterclockwise", "label": "Reembolsado"},
            "chargeback": {"class": "danger", "icon": "exclamation-triangle-fill", "label": "Chargeback"},
            "overpaid": {"class": "info", "icon": "plus-circle-fill", "label": "Pago a mais"},
            "underpaid": {"class": "warning", "icon": "dash-circle-fill", "label": "Pago a menos"},
        }

        if payment:
            return payment_status_map.get(payment.status, payment_status_map["pending"])

        link_status_map = {
            "active": {"class": "warning", "icon": "clock-fill", "label": "Aguardando pagamento"},
            "expired": {"class": "secondary", "icon": "hourglass-split", "label": "Expirado"},
            "used": {"class": "success", "icon": "check-circle-fill", "label": "Pago"},
            "canceled": {"class": "danger", "icon": "x-circle-fill", "label": "Cancelado"},
        }

        return link_status_map.get(link.status, link_status_map["active"])

    # ==============================================================
    # HELPERS
    # ==============================================================

    def _calculate_days_ago(self, date):
        days = (timezone.now() - date).days
        if days == 0:
            return "Hoje"
        if days == 1:
            return "Ontem"
        return f"{days} dias"

    def _get_chart_data(self, start_date):
        today = timezone.now().date()
        weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

        counts_by_date = (
            PaymentLink.objects
            .filter(created_at__date__gte=start_date.date())
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        counts_map = {item["date"]: item["count"] for item in counts_by_date}
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

        max_count = max((d["count"] for d in chart_data), default=1)
        for data in chart_data:
            data["height"] = int((data["count"] / max_count) * 100) if max_count else 0

        return chart_data

    # ==============================================================
    # CONTEXTO PRINCIPAL
    # ==============================================================

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)

        # ----------------------------------------------------------
        # FINANCEIRO (PAYMENT)
        # ----------------------------------------------------------

        payments_stats = Payment.objects.filter(
            payment_date__gte=thirty_days_ago
        ).aggregate(
            total_received=Sum("amount", filter=Q(status="paid")),
            total_refunded=Sum("amount", filter=Q(status="refunded")),
            total_chargeback=Sum("amount", filter=Q(status="chargeback")),

            total_paid=Count("id", filter=Q(status="paid")),
            total_processing=Count("id", filter=Q(status="processing")),
            total_failed=Count("id", filter=Q(status="failed")),
            total_canceled=Count("id", filter=Q(status="canceled")),
        )

        # ----------------------------------------------------------
        # PIPELINE (PAYMENT LINK)
        # ----------------------------------------------------------

        links_qs = PaymentLink.objects.filter(created_at__gte=thirty_days_ago)

        links_stats = links_qs.aggregate(
            total_links=Count("id"),
            total_expired=Count("id", filter=Q(status="expired")),
            total_canceled=Count("id", filter=Q(status="canceled")),
        )

        links_em_aberto_qs = PaymentLink.objects.filter(
            status="active"
        ).filter(
            Q(payment__isnull=True) |
            Q(payment__status__in=["pending", "processing", "underpaid"])
        )

        valor_em_aberto = links_em_aberto_qs.aggregate(
            total=Sum("amount")
        ).get("total") or Decimal("0")

        total_links_em_aberto = links_em_aberto_qs.count()

        # ----------------------------------------------------------
        # MÉTRICAS
        # ----------------------------------------------------------

        total_received = payments_stats["total_received"] or Decimal("0")
        total_paid = payments_stats["total_paid"] or 0
        total_links = links_stats["total_links"] or 0

        taxa_conversao = round((total_paid / total_links) * 100) if total_links else 0
        ticket_medio = (total_received / total_paid) if total_paid else Decimal("0")

        total_sellers = Seller.objects.filter(is_active=True).count()

        # ----------------------------------------------------------
        # LINKS RECENTES
        # ----------------------------------------------------------

        recent_links = (
            PaymentLink.objects
            .filter(created_at__gte=thirty_days_ago)
            .select_related("order", "order__seller", "payment")
            .order_by("-created_at")[:4]
        )

        links_data = []
        for link in recent_links:
            payment_obj = getattr(link, "payment", None)
            links_data.append(
                {
                    "link": link,
                    "order": link.order,
                    "payment": payment_obj,
                    "status_display": self._get_status_display(link, payment_obj),
                    "days_ago": self._calculate_days_ago(link.created_at),
                }
            )

        # ----------------------------------------------------------
        # GRÁFICO / CRESCIMENTO
        # ----------------------------------------------------------

        chart_data = self._get_chart_data(seven_days_ago)

        this_week_total = (
            Payment.objects
            .filter(status="paid", payment_date__gte=seven_days_ago)
            .aggregate(total=Sum("amount"))
            .get("total") or Decimal("0")
        )

        last_week_total = (
            Payment.objects
            .filter(
                status="paid",
                payment_date__gte=fourteen_days_ago,
                payment_date__lt=seven_days_ago,
            )
            .aggregate(total=Sum("amount"))
            .get("total") or Decimal("0")
        )

        week_growth = (
            round(((this_week_total - last_week_total) / last_week_total) * 100)
            if last_week_total > 0
            else (100 if this_week_total > 0 else 0)
        )

        # ----------------------------------------------------------
        # CONTEXTO FINAL
        # ----------------------------------------------------------

        context.update(
            {
                "total_received": total_received,
                "total_refunded": payments_stats["total_refunded"] or Decimal("0"),
                "total_chargeback": payments_stats["total_chargeback"] or Decimal("0"),

                "total_pagos": payments_stats["total_paid"],
                "total_processando": payments_stats["total_processing"],
                "total_falhados": payments_stats["total_failed"],
                "total_cancelados": payments_stats["total_canceled"],

                "valor_em_aberto": valor_em_aberto,
                "total_links_ativos": total_links_em_aberto,
                "total_links_criados": links_stats["total_links"],
                "total_links_expirados": links_stats["total_expired"],

                "taxa_conversao": taxa_conversao,
                "ticket_medio": ticket_medio,
                "total_sellers": total_sellers,

                "recent_links": links_data,
                "chart_data": chart_data,
                "this_week_total": this_week_total,
                "last_week_total": last_week_total,
                "week_growth": week_growth,
                "week_growth_positive": week_growth >= 0,
            }
        )

        return context
