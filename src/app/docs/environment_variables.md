# Environment Variables

This document describes the environment variables used to configure the EmbedIQ backend.

## Core Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:devpassword@localhost:5432/embediq` | Yes |
| `DATA_DIR` | Directory for storing user data | `/data/embediq/users` | Yes |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` | No |
| `PORT` | Port for the API server | `8000` | No |
| `HOST` | Host for the API server | `0.0.0.0` | No |

## Authentication

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AUTH0_DOMAIN` | Auth0 domain | None | Yes |
| `AUTH0_API_AUDIENCE` | Auth0 API audience | None | Yes |
| `AUTH_DISABLED` | Disable authentication (for development) | `false` | No |
| `ADMIN_USER_ID` | User ID with admin privileges | None | No |

## LightRAG Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LIGHTRAG_MODEL` | Embedding model for LightRAG | `sentence-transformers/all-MiniLM-L6-v2` | No |
| `LIGHTRAG_CHUNK_SIZE` | Chunk size for document splitting | `512` | No |
| `LIGHTRAG_CHUNK_OVERLAP` | Chunk overlap for document splitting | `128` | No |
| `LIGHTRAG_VECTOR_SIZE` | Vector size for embeddings | `384` | No |
| `LIGHTRAG_SIMILARITY_THRESHOLD` | Similarity threshold for search | `0.7` | No |
| `LIGHTRAG_MAX_CHUNKS` | Maximum chunks to return in search | `5` | No |
| `LIGHTRAG_CACHE_SIZE` | Size of the embedding cache | `1000` | No |

## Monitoring

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MONITORING_ENABLED` | Enable system monitoring | `true` | No |
| `MONITORING_INTERVAL` | Interval for collecting metrics (seconds) | `60` | No |
| `MONITORING_RETENTION_DAYS` | Days to retain monitoring data | `30` | No |

## Backup

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BACKUP_ENABLED` | Enable automatic backups | `true` | No |
| `BACKUP_INTERVAL` | Interval for automatic backups (hours) | `24` | No |
| `BACKUP_RETENTION_COUNT` | Number of backups to retain | `7` | No |
| `BACKUP_DIR` | Directory for storing backups | `/data/embediq/backups` | No |

## External Services

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM features | None | No |
| `S3_BUCKET` | S3 bucket for remote storage | None | No |
| `S3_ACCESS_KEY` | S3 access key | None | No |
| `S3_SECRET_KEY` | S3 secret key | None | No |
| `S3_REGION` | S3 region | `us-east-1` | No |

## Example Configuration

### Development Environment

```bash
# Core Configuration
DATABASE_URL=postgresql://postgres:devpassword@localhost:5432/embediq
DATA_DIR=./data/embediq/users
LOG_LEVEL=DEBUG

# Authentication
AUTH0_DOMAIN=dev-example.auth0.com
AUTH0_API_AUDIENCE=https://api.embediq.com
AUTH_DISABLED=true

# LightRAG Configuration
LIGHTRAG_MODEL=sentence-transformers/all-MiniLM-L6-v2
LIGHTRAG_CHUNK_SIZE=512
LIGHTRAG_CHUNK_OVERLAP=128

# Monitoring
MONITORING_ENABLED=true
MONITORING_INTERVAL=60

# Backup
BACKUP_ENABLED=true
BACKUP_INTERVAL=24
BACKUP_DIR=./data/embediq/backups
```

### Production Environment

```bash
# Core Configuration
DATABASE_URL=postgresql://embediq_user:strong_password@db.example.com:5432/embediq_prod
DATA_DIR=/data/embediq/users
LOG_LEVEL=INFO

# Authentication
AUTH0_DOMAIN=embediq.auth0.com
AUTH0_API_AUDIENCE=https://api.embediq.com
AUTH_DISABLED=false

# LightRAG Configuration
LIGHTRAG_MODEL=sentence-transformers/all-MiniLM-L6-v2
LIGHTRAG_CHUNK_SIZE=512
LIGHTRAG_CHUNK_OVERLAP=128

# Monitoring
MONITORING_ENABLED=true
MONITORING_INTERVAL=60
MONITORING_RETENTION_DAYS=90

# Backup
BACKUP_ENABLED=true
BACKUP_INTERVAL=6
BACKUP_RETENTION_COUNT=28
BACKUP_DIR=/data/embediq/backups

# External Services
OPENAI_API_KEY=sk-...
S3_BUCKET=embediq-backups
S3_ACCESS_KEY=AKIA...
S3_SECRET_KEY=...
S3_REGION=us-east-1
```

## Setting Environment Variables

### Local Development

For local development, you can set environment variables in a `.env` file in the project root:

```bash
# .env
DATABASE_URL=postgresql://postgres:devpassword@localhost:5432/embediq
AUTH0_DOMAIN=dev-example.auth0.com
AUTH0_API_AUDIENCE=https://api.embediq.com
```

### Docker

When using Docker, you can set environment variables in the `docker-compose.yml` file:

```yaml
services:
  api:
    image: embediq/backend
    environment:
      - DATABASE_URL=postgresql://postgres:devpassword@db:5432/embediq
      - AUTH0_DOMAIN=dev-example.auth0.com
      - AUTH0_API_AUDIENCE=https://api.embediq.com
```

### Production Deployment

In production, you should set environment variables using your deployment platform's configuration:

- **Kubernetes**: Use ConfigMaps and Secrets
- **AWS ECS**: Use Task Definitions
- **Heroku**: Use Config Vars
- **Azure App Service**: Use Application Settings
