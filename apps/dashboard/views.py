# dashboard/views.py
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.orders.models import Order
from apps.payments.models import Payment, PaymentLink
from apps.sellers.models import Seller


class DashboardHomeView(TemplateView):
    """
    Dashboard principal do sistema de links de pagamento.
    Exibe métricas consolidadas sem necessidade de login.
    """
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Período de análise: últimos 30 dias
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # ============================
        # TOTAIS POR STATUS
        # ============================
        
        # Total recebido (pagamentos concluídos)
        total_received = Payment.objects.filter(
            status='paid',
            payment_date__gte=thirty_days_ago
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        # Total pendente (links ativos)
        total_pending = PaymentLink.objects.filter(
            status='active',
            created_at__gte=thirty_days_ago
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        # Total cancelado
        total_canceled = Payment.objects.filter(
            status='canceled',
            payment_date__gte=thirty_days_ago
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        # Total falhado
        total_failed = Payment.objects.filter(
            status='failed',
            payment_date__gte=thirty_days_ago
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        # ============================
        # CONTADORES DE LINKS
        # ============================
        
        links_stats = PaymentLink.objects.filter(
            created_at__gte=thirty_days_ago
        ).aggregate(
            total_criados=Count('id'),
            ativos=Count('id', filter=Q(status='active')),
            expirados=Count('id', filter=Q(status='expired')),
            inativos=Count('id', filter=Q(status='inactive'))
        )
        
        # ============================
        # CONTADORES DE PAGAMENTOS
        # ============================
        
        payments_stats = Payment.objects.filter(
            payment_date__gte=thirty_days_ago
        ).aggregate(
            pagos=Count('id', filter=Q(status='paid')),
            pendentes=Count('id', filter=Q(status='pending')),
            cancelados=Count('id', filter=Q(status='canceled')),
            falhados=Count('id', filter=Q(status='failed'))
        )
        
        # ============================
        # MÉTRICAS DE PERFORMANCE
        # ============================
        
        # Taxa de conversão (pagos / criados)
        total_links = links_stats['total_criados']
        total_pagos = payments_stats['pagos']
        taxa_conversao = 0
        if total_links > 0:
            taxa_conversao = round((total_pagos / total_links) * 100)
        
        # Ticket médio
        ticket_medio = Decimal('0')
        if total_pagos > 0:
            ticket_medio = total_received / total_pagos
        
        # ============================
        # VOLUME TOTAL PROCESSADO
        # ============================
        
        volume_total = total_received + total_pending
        
        # ============================
        # LINKS RECENTES (últimos 4)
        # ============================
        
        recent_links = PaymentLink.objects.filter(
            created_at__gte=thirty_days_ago
        ).select_related('order', 'order__seller').order_by('-created_at')[:4]
        
        # Preparar dados dos links para o template
        links_data = []
        for link in recent_links:
            # Buscar pagamento associado se existir
            payment = Payment.objects.filter(payment_link=link).first()
            
            links_data.append({
                'link': link,
                'order': link.order,
                'payment': payment,
                'seller_name': link.order.seller.name if link.order.seller else 'Sem vendedor',
                'status_display': self._get_status_display(link, payment),
                'days_ago': self._calculate_days_ago(link.created_at)
            })
        
        # ============================
        # GRÁFICO - ÚLTIMOS 7 DIAS
        # ============================
        
        chart_data = self._get_chart_data()
        
        # ============================
        # TOTAL DE VENDEDORES
        # ============================
        
        total_sellers = Seller.objects.filter(is_active=True).count()
        
        # ============================
        # COMPARATIVO SEMANA ANTERIOR
        # ============================
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        fourteen_days_ago = timezone.now() - timedelta(days=14)
        
        this_week_total = Payment.objects.filter(
            status='paid',
            payment_date__gte=seven_days_ago
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        last_week_total = Payment.objects.filter(
            status='paid',
            payment_date__gte=fourteen_days_ago,
            payment_date__lt=seven_days_ago
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Percentual de crescimento
        week_growth = 0
        if last_week_total > 0:
            week_growth = round(((this_week_total - last_week_total) / last_week_total) * 100)
        
        # ============================
        # INJETAR NO CONTEXTO
        # ============================
        
        context.update({
            # Totais financeiros
            'volume_total': volume_total,
            'total_received': total_received,
            'total_pending': total_pending,
            'total_canceled': total_canceled,
            'total_failed': total_failed,
            
            # Contadores
            'total_links_criados': total_links,
            'total_links_ativos': links_stats['ativos'],
            'total_links_expirados': links_stats['expirados'],
            'total_pagos': total_pagos,
            'total_pendentes': payments_stats['pendentes'],
            'total_cancelados': payments_stats['cancelados'],
            'total_falhados': payments_stats['falhados'],
            
            # Métricas
            'taxa_conversao': taxa_conversao,
            'ticket_medio': ticket_medio,
            'total_sellers': total_sellers,
            
            # Links recentes
            'recent_links': links_data,
            
            # Gráfico
            'chart_data': chart_data,
            
            # Comparativo semanal
            'this_week_total': this_week_total,
            'last_week_total': last_week_total,
            'week_growth': week_growth,
            'week_growth_positive': week_growth >= 0,
        })
        
        return context
    
    def _get_status_display(self, link, payment):
        """
        Retorna o status visual do link/pagamento.
        """
        if payment:
            status_map = {
                'paid': {'class': 'success', 'icon': 'check-circle-fill', 'label': 'Pago'},
                'pending': {'class': 'warning', 'icon': 'clock-fill', 'label': 'Pendente'},
                'canceled': {'class': 'danger', 'icon': 'x-circle-fill', 'label': 'Cancelado'},
                'failed': {'class': 'danger', 'icon': 'x-circle-fill', 'label': 'Falhou'},
            }
            return status_map.get(payment.status, status_map['pending'])
        
        # Se não tem pagamento, verificar status do link
        link_status_map = {
            'active': {'class': 'warning', 'icon': 'clock-fill', 'label': 'Aguardando'},
            'expired': {'class': 'info', 'icon': 'hourglass-split', 'label': 'Expirado'},
            'inactive': {'class': 'secondary', 'icon': 'dash-circle', 'label': 'Inativo'},
        }
        return link_status_map.get(link.status, link_status_map['active'])
    
    def _calculate_days_ago(self, date):
        """
        Calcula quantos dias atrás foi a data.
        """
        diff = timezone.now() - date
        days = diff.days
        
        if days == 0:
            return "Hoje"
        elif days == 1:
            return "Ontem"
        else:
            return f"{days} dias"
    
    def _get_chart_data(self):
        """
        Retorna dados dos últimos 7 dias para o gráfico.
        """
        chart_data = []
        today = timezone.now().date()
        
        # Dias da semana em português
        weekdays = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        
        for i in range(6, -1, -1):  # De 6 dias atrás até hoje
            date = today - timedelta(days=i)
            
            # Contar links criados neste dia
            count = PaymentLink.objects.filter(
                created_at__date=date
            ).count()
            
            # Nome do dia
            day_label = "Hoje" if i == 0 else weekdays[date.weekday()]
            
            # Calcular altura da barra (baseado no maior valor)
            # Vamos normalizar depois
            chart_data.append({
                'day': day_label,
                'count': count,
                'is_today': i == 0
            })
        
        # Normalizar alturas (maior = 100%)
        if chart_data:
            max_count = max(d['count'] for d in chart_data) or 1
            for data in chart_data:
                data['height'] = int((data['count'] / max_count) * 100)
        
        return chart_data