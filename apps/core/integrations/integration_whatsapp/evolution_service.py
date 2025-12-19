# evolution_service.py
import logging
from typing import List
from apps.core.integrations.integration_whatsapp.whatsapp import get_evolution_client
from evolutionapi.models.message import TextMessage

# Logger
logger = logging.getLogger("integrations")

# Singleton global do client
CLIENT = get_evolution_client()

# Busca instâncias apenas uma vez
if CLIENT:
    INSTANCES = CLIENT.instances.fetch_instances()
else:
    INSTANCES = []

CONTEXT = {"instances": INSTANCES}



