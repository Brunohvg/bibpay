# =================================================================
# ARQUIVO COMPLETO: apps/payments/services.py (CORRIGIDO)
# =================================================================

from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone

# Importações dos seus modelos
from apps.payments.models import PaymentLink, Payment

# =================================================================
# CORREÇÃO: Importação da classe de integração
# =================================================================
# Se sua classe de integração está em apps.core.integrations.pagarme
from apps.core.integrations.pagarme import PagarMePaymentLink 
# =================================================================


# ============================
#   CRIAÇÃO DE LINK DE PAGAMENTO
# ============================

def process_payment_link_for_order(order):
    """Gera o link de pagamento via API do Pagar.me e salva no banco."""
    try:
        # 1. Gera o link via API do Pagar.me
        link_data = generate_payment_link(order)
        if not link_data:
            print(f"✗ Erro ao gerar link para order {order.id}: API retornou vazio")
            return None

        # 2. Salva no banco
        payment_link = create_payment_link_record(order, link_data)
        if not payment_link:
            print(f"✗ Erro ao salvar link para order {order.id}")
            return None
        
        print(f"✓ Link criado com sucesso para order {order.id}: {payment_link.url_link}")
        return payment_link
        
    except Exception as e:
        print(f"✗ Erro inesperado ao processar link para order {order.id}: {e}")
        return None


def generate_payment_link(order):
    """Chama a API do Pagar.me para criar um link de pagamento."""
    try:
        # A classe PagarMePaymentLink agora está importada e definida.
        pagarme = PagarMePaymentLink( 
            customer_name=order.name,
            total_amount=int(order.total * 100),   # Pagar.me exige em centavos
            max_installments=order.installments,
            free_installments=order.installments,
        )

        # Chama o método create_link() da sua classe de integração
        response = pagarme.create_link()
        
        if not response:
            print("✗ API do Pagar.me não retornou resposta")
            return None

        link_id = response.get("id")
        link_url = response.get("url") or response.get("short_url")

        if not link_id or not link_url:
            print(f"✗ API do Pagar.me retornou dados incompletos: {response}")
            return None

        return {"id": link_id, "url": link_url}

    except Exception as e:
        # Este print agora funcionará corretamente após a correção da importação
        print(f"✗ Erro ao chamar API do Pagar.me: {e}") 
        return None


def create_payment_link_record(order, link_data):
    """Salva o PaymentLink no banco de dados."""
    try:
        return PaymentLink.objects.create(
            order=order,
            id_link=link_data["id"],
            url_link=link_data["url"],
            amount=order.total,
            status="active",
        )
    except Exception as e:
        print(f"✗ Erro ao salvar PaymentLink no banco: {e}")
        return None


# ============================
#   WEBHOOK - PROCESSAR PAGAMENTO (PRONTO PARA USO)
# ============================

def process_payment_webhook(webhook_data):
    """
    Processa o webhook, garante unicidade do Payment e sincroniza status.
    """
    try:
        data = webhook_data.get("data", {})
        charge_id = data.get("id")
        
        payment_link = PaymentLink.objects.filter(id_link=charge_id).first()
        
        if not payment_link:
            print(f"✗ PaymentLink não encontrado para charge {charge_id}")
            return None
        
        # Mapear status do Pagar.me para nosso sistema
        status_map = {
            "paid": "paid",
            "pending": "pending",
            "canceled": "canceled",
            "failed": "failed",
            "refunded": "refunded",
            "chargeback": "chargeback",
        }
        
        payment_status = status_map.get(data.get("status"), "pending")
        
        # Inicia uma transação atômica para garantir consistência
        with transaction.atomic():
            
            # Tenta buscar ou criar Payment. OneToOneField garante a unicidade.
            payment, created = Payment.objects.get_or_create(
                payment_link=payment_link,
                defaults={
                    "status": payment_status,
                    "amount": Decimal(str(data.get("amount", 0))) / 100,
                    "payment_date": data.get("paid_at") or timezone.now(),
                }
            )
            
            # 1. Se já existe, apenas atualiza status
            if not created and payment.status != payment_status:
                payment.status = payment_status
                payment.save()

            # 2. Sincroniza Status do PaymentLink
            final_statuses = ["paid", "canceled", "failed", "refunded", "chargeback"]
            
            if payment_status in final_statuses and payment_link.status != payment_status:
                payment_link.status = payment_status
                payment_link.is_active = False # Marca como inativo após a resolução
                payment_link.save()

            # 3. Sincroniza Status do Order
            order = payment_link.order
            if order.status != payment_status:
                if payment_status in ["paid", "canceled"]:
                     order.status = payment_status
                elif payment_status in ["failed", "refunded", "chargeback"]:
                     order.status = "canceled" 
                order.save()
        
        print(f"✓ Payment {'criado' if created else 'atualizado'}: {payment.id} - Status: {payment_status}")
        return payment
        
    except Exception as e:
        print(f"✗ Erro ao processar webhook: {e}")
        return None


# ============================
#   LISTAGENS / CONSULTAS
# ============================

def get_payment_links_for_order(order):
    """Retorna todos os PaymentLinks de um pedido."""
    return PaymentLink.objects.filter(
        order=order,
        is_active=True,
        is_deleted=False
    )

def list_active_payment_links():
    """Lista todos os PaymentLinks com status 'active'."""
    return PaymentLink.objects.filter(
        status="active",
        is_active=True,
        is_deleted=False
    )

def list_payments(**filters):
    """Lista pagamentos aplicando filtros opcionais."""
    qs = Payment.objects.filter(is_active=True, is_deleted=False)
    if filters:
        qs = qs.filter(**filters)
    return qs

def calculate_total_from_links(objects):
    """Soma o campo 'amount' de Payment ou PaymentLink."""
    total = Decimal("0")
    for obj in objects:
        if obj.amount:
            total += Decimal(str(obj.amount))
    return total

def get_payment_statistics(start_date=None, end_date=None):
    """Retorna estatísticas consolidadas de pagamentos."""
    qs = Payment.objects.all()
    
    if start_date:
        qs = qs.filter(payment_date__gte=start_date)
    if end_date:
        qs = qs.filter(payment_date__lte=end_date)
    
    return qs.aggregate(
        total_paid=Sum('amount', filter=Q(status='paid')) or Decimal('0'),
        total_pending=Sum('amount', filter=Q(status='pending')) or Decimal('0'),
        total_canceled=Sum('amount', filter=Q(status='canceled')) or Decimal('0'),
        total_failed=Sum('amount', filter=Q(status='failed')) or Decimal('0'),
        count_paid=Count('id', filter=Q(status='paid')),
        count_pending=Count('id', filter=Q(status='pending')),
        count_canceled=Count('id', filter=Q(status='canceled')),
        count_failed=Count('id', filter=Q(status='failed')),
    )