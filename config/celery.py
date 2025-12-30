# config/celery.py
"""
Configuração do Celery para processamento assíncrono.

Otimizado para Oracle Free Tier (1GB RAM):
- 1 worker com concurrency=2
- Tarefas leves (envio de mensagens)
- Redis Alpine como broker (~5MB RAM)
"""
import os
from celery import Celery

# Definir settings do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('bibpay')

# Carregar configurações do Django settings.py com prefixo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descoberta de tasks nos apps Django
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
