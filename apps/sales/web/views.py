from datetime import timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied

from apps.sales.models import DailySale
from apps.sales.forms import DailySaleForm
from apps.sellers.models import Seller

class SellerRequiredMixin(LoginRequiredMixin):
    """Garante que o usuário é um vendedor."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not hasattr(request.user, 'seller_profile'):
            messages.error(request, "Você não tem perfil de vendedor configurado.")
            return redirect('dashboard:dashboard-home')
            
        return super().dispatch(request, *args, **kwargs)

class SellerDashboardView(SellerRequiredMixin, TemplateView):
    """
    Dashboard Mobile do Vendedor.
    Mostra resumo do mês e lista de vendas recentes.
    """
    template_name = "sales/mobile/dashboard.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seller = self.request.user.seller_profile
        today = timezone.now().date()
        first_day_month = today.replace(day=1)
        
        # Vendas do mês atual
        monthly_sales = DailySale.objects.filter(
            seller=seller,
            date__gte=first_day_month
        ).order_by('-date')
        
        total_month = monthly_sales.aggregate(total=Sum('amount'))['total'] or 0
        
        # Verificar se já lançou hoje
        sale_today = monthly_sales.filter(date=today).first()
        
        context.update({
            'seller': seller,
            'total_month': total_month,
            'recent_sales': monthly_sales[:50], # Últimas 50
            'sale_today': sale_today,
            'today': today,
        })
        return context

class SaleCreateView(SellerRequiredMixin, CreateView):
    """Lançamento de venda diária."""
    model = DailySale
    form_class = DailySaleForm
    template_name = "sales/mobile/sale_form.html"
    success_url = reverse_lazy('sales:seller-dashboard')
    
    def form_valid(self, form):
        form.instance.seller = self.request.user.seller_profile
        
        # Verificar duplicidade manualmente para dar mensagem melhor
        exists = DailySale.objects.filter(
            seller=form.instance.seller, 
            date=form.cleaned_data['date']
        ).exists()
        
        if exists:
            messages.warning(self.request, "Já existe um lançamento para esta data. Edite o existente.")
            return redirect('sales:seller-dashboard')
            
        messages.success(self.request, "Venda lançada com sucesso!")
        return super().form_valid(form)

class SaleUpdateView(SellerRequiredMixin, UpdateView):
    """Edição de venda (apenas as próprias)."""
    model = DailySale
    form_class = DailySaleForm
    template_name = "sales/mobile/sale_form.html"
    success_url = reverse_lazy('sales:seller-dashboard')
    
    def get_queryset(self):
        # Garante que só edita suas próprias vendas
        return super().get_queryset().filter(seller=self.request.user.seller_profile)
    
    def form_valid(self, form):
        messages.success(self.request, "Venda atualizada com sucesso!")
        return super().form_valid(form)
