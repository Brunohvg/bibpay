from django.contrib import admin
from .models import Seller

admin.site.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address', 'city', 'state', 'zip_code', 'country', 'created_at', 'updated_at')
    list_filter = ('name', 'email', 'phone', 'address', 'city', 'state', 'zip_code', 'country', 'created_at', 'updated_at')
    search_fields = ('name', 'email', 'phone', 'address', 'city', 'state', 'zip_code', 'country', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    