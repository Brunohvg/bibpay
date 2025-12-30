import logging
import time
from typing import Optional

from decouple import config
from evolutionapi.client import EvolutionClient
from evolutionapi.exceptions import (
    EvolutionAPIError,
    EvolutionAuthenticationError,
)

# Logger
logger = logging.getLogger("integrations")

# Variáveis de ambiente (com fallback para compatibilidade)
URL_SERVE = config("EVOLUTION_API_URL", default=config("URL_SERVE", default=""))
API_KEY = config("EVOLUTION_API_KEY", default=config("API_KEY", default=""))
MAX_RETRIES = config("MAX_RETRIES", default=3, cast=int)
RETRY_DELAY = config("RETRY_DELAY", default=2, cast=int)


class EvolutionClientManager:
    """
    Gerencia a conexão com a Evolution API.
    Conecta sob demanda e tenta reconectar se cair.
    """

    def __init__(
        self,
        base_url: str,
        api_token: str,
        max_retries: int,
        retry_delay: int,
    ):
        if not base_url or not api_token:
            raise EnvironmentError(
                "Variáveis de ambiente URL_SERVE ou API_KEY não configuradas."
            )

        self.base_url = base_url
        self.api_token = api_token
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client: Optional[EvolutionClient] = None

    def _connect(self) -> None:
        """Cria a conexão com retentativas."""
        logger.info("Conectando à Evolution API...")

        for attempt in range(1, self.max_retries + 1):
            try:
                self._client = EvolutionClient(
                    base_url=self.base_url,
                    api_token=self.api_token,
                )
                logger.info("EvolutionClient conectado com sucesso.")
                return

            except (EvolutionAuthenticationError, EvolutionAPIError) as e:
                logger.warning(
                    f"Tentativa {attempt}/{self.max_retries} falhou: {e}"
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    self._client = None
                    raise

            except Exception as e:
                self._client = None
                logger.error(f"Erro inesperado ao conectar: {e}")
                raise

    def get_client(self) -> Optional[EvolutionClient]:
        """
        Retorna o cliente ativo.
        Se não existir, tenta criar.
        """
        if self._client is None:
            self._connect()

        return self._client


# ============================
# Lazy Singleton (CORRETO)
# ============================
_client_manager: Optional[EvolutionClientManager] = None


def get_evolution_client() -> Optional[EvolutionClient]:
    """
    Ponto único para obter o cliente da Evolution API.
    Só conecta quando alguém chama.
    """
    global _client_manager

    try:
        if _client_manager is None:
            _client_manager = EvolutionClientManager(
                base_url=URL_SERVE,
                api_token=API_KEY,
                max_retries=MAX_RETRIES,
                retry_delay=RETRY_DELAY,
            )

        return _client_manager.get_client()

    except Exception as e:
        logger.error(f"Falha ao obter cliente Evolution API: {e}")
        return None
