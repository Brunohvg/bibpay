from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Home redirect
    path("", RedirectView.as_view(url="/dashboard/", permanent=False), name="home"),
    
    path("admin/", admin.site.urls),

    # Authentication
    path("accounts/", include("apps.accounts.urls")),

    # WEB
    path("orders/", include("apps.orders.urls")),
    path("payments/", include("apps.payments.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("sales/", include("apps.sales.urls")),
    path("reports/", include("apps.reports.urls")),

    # API
    path("api/orders/", include("apps.orders.api.urls")),
    path("api/payments/", include("apps.payments.api.urls")),
    path("api/sales/", include("apps.sales.api.urls")),
    
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
