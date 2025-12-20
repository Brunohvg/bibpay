from django.urls import path, include

urlpatterns = [
    path("v1/", include("apps.orders.api.v1.urls")),
]
