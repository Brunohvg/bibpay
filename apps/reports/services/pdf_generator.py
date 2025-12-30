from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from django.db.models import Sum
from apps.sales.models import DailySale

def generate_sales_report_pdf(start_date, end_date):
    """
    Gera relatório de vendas mensal em PDF.
    Retorna objeto BytesIO com o arquivo.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1  # Center
    
    # Título
    month_str = start_date.strftime("%B/%Y")
    elements.append(Paragraph(f"Relatório de Vendas - {month_str}", title_style))
    elements.append(Spacer(1, 20))
    
    # Dados Agregados
    sales = DailySale.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    )
    
    total_general = sales.aggregate(Sum('amount'))['amount__sum'] or 0
    
    elements.append(Paragraph(f"<b>Total Geral: R$ {total_general:,.2f}</b>", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Tabela Resumo Vendedores
    elements.append(Paragraph("Resumo por Vendedor", styles['Heading2']))
    
    ranking = (
        sales.values('seller__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    
    data = [["Vendedor", "Total Vendido", "Participação"]]
    
    for item in ranking:
        percent = (item['total'] / total_general) if total_general else 0
        data.append([
            item['seller__name'],
            f"R$ {item['total']:,.2f}",
            f"{percent:.1%}"
        ])
        
    t = Table(data, colWidths=[200, 150, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
    ]))
    elements.append(t)
    
    elements.append(Spacer(1, 30))
    
    # Detalhamento Diário (Top 20 para não ficar gigante no exemplo)
    elements.append(Paragraph("Últimos Lançamentos", styles['Heading2']))
    
    daily_data = [["Data", "Vendedor", "Valor"]]
    
    recent_sales = sales.select_related('seller').order_by('-date')[:50]
    
    for sale in recent_sales:
        daily_data.append([
            sale.date.strftime("%d/%m/%Y"),
            sale.seller.name,
            f"R$ {sale.amount:,.2f}"
        ])
        
    t2 = Table(daily_data, colWidths=[100, 250, 100])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
    ]))
    elements.append(t2)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
