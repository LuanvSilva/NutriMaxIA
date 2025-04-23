# Implantação e Operação

## Visão Geral

Este documento descreve os procedimentos para implantação, configuração e operação do sistema NutriMaxIA em ambientes de desenvolvimento e produção.

## Pré-requisitos

- Python 3.9+
- PostgreSQL 14+ com extensão pgVector instalada
- Redis 6+
- Docker e Docker Compose (opcional, para implantação containerizada)
- Chave de API do Google Cloud (para acesso ao Gemini)

## Configuração do Ambiente

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```
# Configurações de Banco de Dados
DATABASE_URL=postgresql://user:password@localhost/nutritrain_db

# Configurações Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-1.5-flash

# Segurança
SECRET_KEY=your_secure_secret_key_for_jwt
```

### Banco de Dados

1. Crie o banco de dados PostgreSQL:
```bash
createdb nutritrain_db
```

2. Instale a extensão pgVector:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

3. Execute os scripts de inicialização:
```bash
psql -d nutritrain_db -f app/init-db.sql
```

## Instalação

### Método 1: Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/sua-organizacao/nutrimax-ia.git
cd nutrimax-ia
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r app/requirements.txt
```

4. Execute as migrações do banco de dados (se necessário):
```bash
flask db upgrade
```

### Método 2: Implantação com Docker

1. Construa e inicie os contêineres:
```bash
docker-compose up -d
```

Esta configuração inicia:
- Aplicação Flask
- Servidor de workers Celery
- PostgreSQL com pgVector
- Redis

## Inicialização e Operação

### Iniciar o Servidor de Desenvolvimento

```bash
python app/run.py
```

### Iniciar Worker Celery

```bash
cd app
celery -A celery_worker.celery worker --loglevel=info
```

## Indexação da Base de Conhecimento

Para indexar ou atualizar a base de conhecimento vetorial:

```bash
flask index-knowledge-base
```

Este comando:
1. Lê o arquivo JSON da base de conhecimento
2. Gera embeddings para cada chunk
3. Armazena os chunks e seus embeddings no banco de dados

## Manutenção

### Backup do Banco de Dados

Regularmente faça backup do banco de dados:

```bash
pg_dump -Fc nutritrain_db > nutrimax_backup_$(date +%Y%m%d).dump
```

### Monitoramento dos Workers Celery

Para monitoramento em tempo real das tarefas Celery:

1. Instale o Flower:
```bash
pip install flower
```

2. Execute:
```bash
celery -A app.celery_worker.celery flower
```

3. Acesse o dashboard em `http://localhost:5555`

## Atualização do Sistema

1. Pare os serviços:
```bash
docker-compose down  # Se usando Docker
```

2. Atualize o código fonte:
```bash
git pull origin main
```

3. Atualize as dependências:
```bash
pip install -r app/requirements.txt --upgrade
```

4. Execute migrações pendentes (se houver):
```bash
flask db upgrade
```

5. Reinicie os serviços:
```bash
docker-compose up -d  # Se usando Docker
```

## Verificação de Saúde do Sistema

### Endpoints de Diagnóstico

- **Verificar API**: `GET /api/v1/health`
- **Verificar Banco de Dados**: `GET /api/v1/health/db`
- **Verificar Celery**: `GET /api/v1/health/celery`

### Logs

Os logs do sistema são armazenados em:
- Aplicação: `/var/log/nutrimax-api.log`
- Celery: `/var/log/nutrimax-celery.log`

## Resolução de Problemas Comuns

### Falhas na Geração de Planos

1. Verifique se o worker Celery está em execução
2. Confirme se a chave da API Gemini é válida
3. Verifique os logs de erro da tarefa

### Problemas de Busca Vetorial

1. Confirme se a extensão pgVector está corretamente instalada
2. Verifique se a base de conhecimento foi devidamente indexada
3. Teste a busca direta no banco de dados:

```sql
SELECT chunk_text FROM kb_chunks
ORDER BY embedding <-> '<vector_de_busca>' LIMIT 5;
```