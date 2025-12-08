from apps.core.models import BaseModel
from django.db import models

PAYMENT_STATUS = (
    ("pending", "Pendente"),
    ("paid", "Pago"),
    ("failed", "Falhou"),
    ("canceled", "Cancelado"),
    ("refunded", "Reembolsado"),
    ("chargeback", "Chargeback"),
)

PAYMENT_LINK_STATUS = (
    ("active", "Ativo"),
    ("inactive", "Inativo"),
    ("expired", "Expirado"),
)


class PaymentLink(BaseModel):
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payment_links",
        verbose_name="Pedido",
    )
    url_link = models.URLField(max_length=500, verbose_name="Link de pagamento")
    id_link = models.CharField(max_length=255, verbose_name="ID do link de pagamento")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor", null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=PAYMENT_LINK_STATUS,
        default="active",
        verbose_name="Status",
    )

    def __str__(self):
        return f"Link {self.id} — Pedido {self.order_id} — R$ {self.amount}"

    class Meta:
        verbose_name = "Link de Pagamento"
        verbose_name_plural = "Links de Pagamento"
        ordering = ["-created_at"]
        db_table = "payment_links"


class Payment(BaseModel):

    payment_link = models.ForeignKey(
        "payments.PaymentLink",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Link de pagamento",
    )
    status = models.CharField(
        max_length=50, choices=PAYMENT_STATUS, default="pending", verbose_name="Status"
    )
    payment_date = models.DateTimeField(verbose_name="Data do pagamento")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor", null=True, blank=True)

    def __str__(self):
        return f"Pagamento {self.id} — Link {self.payment_link_id} — R$ {self.amount}"
    
    @property
    def order(self):
        return self.payment_link.order
    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ["-created_at"]
        db_table = "payments"
