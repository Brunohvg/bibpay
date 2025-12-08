from django.contrib import admin
from .models import PaymentLink, Payment


@admin.register(PaymentLink)
class PaymentLinkAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'id_link', 'url_link', 'amount', 'status',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment_link', 'payment_date', 'amount', 'status', 'created_at')