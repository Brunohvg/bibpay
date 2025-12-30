from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from .excel_generator import generate_sales_report_excel
from .pdf_generator import generate_sales_report_pdf

def send_monthly_report_email(year, month, to_email=None):
    """
    Gera relatórios (Excel, PDF) e envia por email para a contabilidade.
    """
    if not to_email:
        to_email = settings.config('ACCOUNTANT_EMAIL', default=None)
        
    if not to_email:
        raise ValueError("Email da contabilidade não configurado (ACCOUNTANT_EMAIL).")
        
    # Calcular datas
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    start_date = timezone.datetime(year, month, 1).date()
    end_date = timezone.datetime(year, month, last_day).date()
    
    month_str = start_date.strftime("%B/%Y")
    
    # Gerar arquivos
    excel_file = generate_sales_report_excel(start_date, end_date)
    pdf_file = generate_sales_report_pdf(start_date, end_date)
    
    # Montar Email
    subject = f"[BibPay] Relatório Mensal de Vendas - {month_str}"
    body = f"""
    Olá,
    
    Segue em anexo o relatório de vendas referente a {month_str}.
    
    Arquivos anexados:
    1. Relatório Geral (PDF)
    2. Detalhamento (Excel)
    
    Atenciosamente,
    Equipe BibPay
    """
    
    email = EmailMessage(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
    )
    
    # Anexar
    email.attach(f'relatorio_vendas_{month}_{year}.xlsx', excel_file.read(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    email.attach(f'relatorio_vendas_{month}_{year}.pdf', pdf_file.read(), 'application/pdf')
    
    email.send()
    return True
