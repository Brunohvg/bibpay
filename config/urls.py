
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('orders/', include('apps.orders.urls')),
    #path('sellers/', include('apps.sellers.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

