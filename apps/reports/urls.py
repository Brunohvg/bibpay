from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('send-monthly/', views.send_report_view, name='send-monthly'),
]
