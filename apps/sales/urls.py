from django.urls import path
from apps.sales.web import views

app_name = 'sales'

urlpatterns = [
    path('mobile/', views.SellerDashboardView.as_view(), name='seller-dashboard'),
    path('mobile/add/', views.SaleCreateView.as_view(), name='sale-add'),
    path('mobile/edit/<int:pk>/', views.SaleUpdateView.as_view(), name='sale-edit'),
]
