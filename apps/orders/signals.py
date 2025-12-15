# orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.orders.models import Order
from apps.payments.services import process_payment_link_for_order


@receiver(post_save, sender=Order)
def create_payment_link_for_order(sender, instance, created, **kwargs):
    """
    Signal que cria automaticamente um PaymentLink quando um Order é criado.
    
    IMPORTANTE:
    - Só executa quando created=True (novo pedido)
    - Chama process_payment_link_for_order que faz:
      1. Chama API do Pagar.me
      2. Cria PaymentLink no banco
    """
    if created:
        print(f"\n🔔 SIGNAL DISPARADO para Order ID: {instance.id}")
        print(f"   Nome: {instance.name}")
        print(f"   Total: R$ {instance.total}")
        
        # Cria o link de pagamento
        payment_link = process_payment_link_for_order(order=instance)
        
        if payment_link:
            print(f"✓ PaymentLink criado com sucesso!")
            print(f"  ID: {payment_link.id}")
            print(f"  URL: {payment_link.url_link}")
        else:
            print(f"✗ ERRO: PaymentLink NÃO foi criado!")
        
        print(f"🔔 FIM DO SIGNAL\n")