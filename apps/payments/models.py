from django.db import models
from apps.core.models import BaseModel

PAYMENT_STATUS = (
    ("pending", "Pendente"),
    ("paid", "Pago"),
    ("failed", "Falhou"),
    ("canceled", "Cancelado"),
    ("refunded", "Reembolsado"),
    ("chargeback", "Chargeback"),
)


class Payment(BaseModel, models):
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Pedido",
    )
    payment_method = models.CharField(max_length=50, verbose_name="Método de pagamento")
    payment_type = models.CharField(max_length=50, verbose_name="Tipo de pagamento")
    payment_date = models.DateTimeField(verbose_name="Data do pagamento")
    url_link = models.URLField(max_length=500, verbose_name="Link de pagamento")
    id_link = models.CharField(max_length=255, verbose_name="ID do link de pagamento")

    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    status = models.CharField(
        max_length=50, choices=PAYMENT_STATUS, default="pending", verbose_name="Status"
    )

    def __str__(self):
        return f"Pagamento {self.id} — Pedido {self.order_id} — R$ {self.amount}"

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ["-created_at"]
        db_table = "payments"



