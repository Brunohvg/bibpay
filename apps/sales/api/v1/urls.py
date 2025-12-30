from django.urls import path
from .views import DailySaleListCreateAPIView, DailySaleDetailAPIView

urlpatterns = [
    path("daily-sales/", DailySaleListCreateAPIView.as_view(), name="daily-sales-list"),
    path("daily-sales/<int:pk>/", DailySaleDetailAPIView.as_view(), name="daily-sales-detail"),
]
