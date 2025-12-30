FROM python:3.14-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY pyproject.toml uv.lock ./

# Instalar uv e dependências Python
RUN pip install uv && \
    uv pip install --system -e .

# Copiar código do projeto
COPY . .

# Criar diretórios necessários
RUN mkdir -p logs static media

# Coletar arquivos estáticos
RUN python manage.py collectstatic --noinput || true

# Expor porta
EXPOSE 8000

# Comando padrão
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
