from django.contrib import admin
from .models import Order


admin.site.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'status', 'installments', 'seller')
    list_filter = ('status', 'seller')
    search_fields = ('name', 'seller__name')
    ordering = ('-created_at',)
    
    
