from django.urls import path

from . import views


urlpatterns = [
    #path('payment-link/create/', views.PaymentLinkCreateView.as_view(), name='payment-link-create'),
    #path('payment/<int:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('webhook/', views.WebhookAPIView.as_view(), name='payment-webhook'),
]
