from django.urls import path, include

urlpatterns = [
    path("v1/", include("apps.payments.api.v1.urls")),
]
