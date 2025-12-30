from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.utils import timezone
from .services.email_sender import send_monthly_report_email

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def send_report_view(request):
    """View para disparar envio de relatório manual."""
    try:
        now = timezone.now()
        # Envia relatório do mês atual (ou anterior se for dia 1)
        target_date = now
        if now.day == 1:
             # Se for dia 1, manda do mês passado
             import datetime
             target_date = now - datetime.timedelta(days=1)
             
        send_monthly_report_email(target_date.year, target_date.month)
        messages.success(request, f"Relatório de {target_date.strftime('%B/%Y')} enviado com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro ao enviar relatório: {str(e)}")
        
    return redirect('dashboard:dashboard-home')
