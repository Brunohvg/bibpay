from django.contrib import admin
from .models import DailySale


@admin.register(DailySale)
class DailySaleAdmin(admin.ModelAdmin):
    list_display = ['seller', 'date', 'amount', 'created_at']
    list_filter = ['seller', 'date']
    search_fields = ['seller__name', 'notes']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações da Venda', {
            'fields': ('seller', 'date', 'amount')
        }),
        ('Observações', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
