# 🐳 Guia de Deploy com Docker

## Pré-requisitos

- Docker instalado
- Docker Compose instalado
- Arquivo `.env` configurado

## 🚀 Deploy Rápido

### 1. Configurar Variáveis de Ambiente

```bash
# Copiar template
cp .env.example .env

# Editar .env com valores de produção
nano .env
```

**Variáveis importantes:**
```env
SECRET_KEY=sua-chave-super-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
DATABASE_URL=postgresql://bibpay:senha-forte@db:5432/bibpay
```

### 2. Build e Start

```bash
# Build das imagens
docker-compose build

# Iniciar serviços
docker-compose up -d

# Ver logs
docker-compose logs -f web
```

### 3. Executar Migrações

```bash
# Rodar migrações
docker-compose exec web python manage.py migrate

# Criar superusuário
docker-compose exec web python manage.py createsuperuser

# Coletar static files
docker-compose exec web python manage.py collectstatic --noinput
```

### 4. Acessar Aplicação

- **Web:** http://localhost:8000
- **Admin:** http://localhost:8000/admin/
- **API Docs:** http://localhost:8000/api/docs/

---

## 📋 Comandos Úteis

### Gerenciamento de Containers

```bash
# Parar serviços
docker-compose down

# Parar e remover volumes
docker-compose down -v

# Reiniciar serviço específico
docker-compose restart web

# Ver status
docker-compose ps
```

### Executar Comandos Django

```bash
# Shell Django
docker-compose exec web python manage.py shell

# Criar app
docker-compose exec web python manage.py startapp nome_app

# Rodar testes
docker-compose exec web python manage.py test

# Coverage
docker-compose exec web coverage run --source='apps' manage.py test
docker-compose exec web coverage report
```

### Logs e Debug

```bash
# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs apenas do web
docker-compose logs -f web

# Ver logs do banco
docker-compose logs -f db

# Acessar bash do container
docker-compose exec web bash
```

### Backup do Banco de Dados

```bash
# Backup
docker-compose exec db pg_dump -U bibpay bibpay > backup.sql

# Restore
cat backup.sql | docker-compose exec -T db psql -U bibpay bibpay
```

---

## 🔧 Configuração de Produção

### Com Nginx (Recomendado)

```bash
# Iniciar com Nginx
docker-compose --profile production up -d

# Nginx estará em http://localhost:80
```

### Variáveis de Ambiente de Produção

```env
# .env para produção
SECRET_KEY=chave-super-secreta-gerada-aleatoriamente
DEBUG=False
ALLOWED_HOSTS=meusite.com,www.meusite.com

# Database
DATABASE_URL=postgresql://bibpay:senha-forte@db:5432/bibpay

# Email (para password reset)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-app

# Payment Gateways
PAGARME_API_KEY=sua-chave-pagarme
SGPWEB_API_KEY=sua-chave-sgpweb

# WhatsApp
EVOLUTION_API_URL=https://sua-evolution-api.com
EVOLUTION_API_KEY=sua-chave-evolution
```

---

## 🔒 Segurança

### Checklist de Segurança

- [ ] SECRET_KEY única e aleatória
- [ ] DEBUG=False em produção
- [ ] ALLOWED_HOSTS configurado
- [ ] Usar HTTPS (certificado SSL)
- [ ] Senhas fortes no banco de dados
- [ ] Backup regular do banco
- [ ] Logs de acesso configurados
- [ ] Firewall configurado

### Gerar SECRET_KEY

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

---

## 📊 Monitoramento

### Health Check

```bash
# Verificar saúde dos containers
docker-compose ps

# Verificar logs de erro
docker-compose logs web | grep ERROR
```

### Métricas

```bash
# Uso de recursos
docker stats

# Espaço em disco
docker system df
```

---

## 🔄 Atualização

### Deploy de Nova Versão

```bash
# 1. Pull do código
git pull origin main

# 2. Rebuild
docker-compose build web

# 3. Parar serviços
docker-compose down

# 4. Iniciar com nova versão
docker-compose up -d

# 5. Rodar migrações
docker-compose exec web python manage.py migrate

# 6. Coletar static files
docker-compose exec web python manage.py collectstatic --noinput
```

---

## 🐛 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker-compose logs web

# Verificar configuração
docker-compose config
```

### Erro de conexão com banco

```bash
# Verificar se banco está rodando
docker-compose ps db

# Testar conexão
docker-compose exec web python manage.py dbshell
```

### Problemas com static files

```bash
# Recriar static files
docker-compose exec web python manage.py collectstatic --clear --noinput
```

---

## 📝 Notas

> [!IMPORTANT]
> **Produção vs Desenvolvimento**
> 
> - Em desenvolvimento: use `docker-compose up` (sem `-d`) para ver logs
> - Em produção: use `docker-compose --profile production up -d` com Nginx

> [!WARNING]
> **Backup Regular**
> 
> Configure backup automático do banco de dados PostgreSQL!

> [!TIP]
> **Performance**
> 
> - Use `gunicorn` com múltiplos workers (configurado no Dockerfile)
> - Configure cache (Redis) para melhor performance
> - Use CDN para static files em produção
