# Database Setup

This document describes how to set up and configure the PostgreSQL database for the EmbedIQ backend.

## Prerequisites

- PostgreSQL 14 or later
- PostgreSQL extensions:
  - `pgvector` for vector operations
  - `uuid-ossp` for UUID generation
  - `pg_trgm` for text search

## Database Creation

### Local Development

1. Install PostgreSQL:

   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # macOS with Homebrew
   brew install postgresql
   
   # Windows
   # Download and install from https://www.postgresql.org/download/windows/
   ```

2. Start PostgreSQL service:

   ```bash
   # Ubuntu/Debian
   sudo systemctl start postgresql
   
   # macOS with Homebrew
   brew services start postgresql
   
   # Windows
   # PostgreSQL is installed as a service and should start automatically
   ```

3. Create a database and user:

   ```bash
   # Connect to PostgreSQL
   sudo -u postgres psql
   
   # Create a database
   CREATE DATABASE embediq;
   
   # Create a user with password
   CREATE USER embediq_user WITH ENCRYPTED PASSWORD 'your_password';
   
   # Grant privileges to the user
   GRANT ALL PRIVILEGES ON DATABASE embediq TO embediq_user;
   
   # Exit PostgreSQL
   \q
   ```

4. Install required extensions:

   ```bash
   # Install pgvector
   # Ubuntu/Debian
   sudo apt install postgresql-14-pgvector
   
   # macOS with Homebrew
   brew install pgvector
   
   # Windows
   # Download and install from https://github.com/pgvector/pgvector/releases
   ```

5. Enable extensions in the database:

   ```bash
   # Connect to the embediq database
   sudo -u postgres psql -d embediq
   
   # Enable extensions
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "pg_trgm";
   CREATE EXTENSION IF NOT EXISTS "vector";
   
   # Exit PostgreSQL
   \q
   ```

### Docker Development

When using Docker Compose for development, the database is automatically set up with the required extensions. See the `docker-compose.yml` file for details.

### Production Deployment

For production deployment, you should use a managed PostgreSQL service like:

- Amazon RDS for PostgreSQL
- Azure Database for PostgreSQL
- Google Cloud SQL for PostgreSQL
- Heroku Postgres

Make sure to enable the required extensions in your managed PostgreSQL instance.

## Database Schema

The EmbedIQ backend uses a schema-less approach for document storage, with metadata stored in JSON format. However, some tables are created for specific features:

### Vector Store

The vector store table is used to store document chunks and their embeddings:

```sql
CREATE TABLE vector_store (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    document_id UUID NOT NULL,
    chunk_id TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient queries
CREATE INDEX idx_vector_store_user_id ON vector_store(user_id);
CREATE INDEX idx_vector_store_document_id ON vector_store(document_id);
CREATE INDEX idx_vector_store_content_trgm ON vector_store USING GIN (content gin_trgm_ops);
CREATE INDEX idx_vector_store_embedding ON vector_store USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### Graph Store

The graph store tables are used to store nodes and edges for the knowledge graph:

```sql
-- Nodes table
CREATE TABLE graph_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    label TEXT NOT NULL,
    properties JSONB NOT NULL DEFAULT '{}'::JSONB,
    embedding VECTOR(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Edges table
CREATE TABLE graph_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    source_id UUID NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    properties JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_id, target_id, type)
);

-- Create indexes for efficient queries
CREATE INDEX idx_graph_nodes_user_id ON graph_nodes(user_id);
CREATE INDEX idx_graph_nodes_type ON graph_nodes(type);
CREATE INDEX idx_graph_nodes_label_trgm ON graph_nodes USING GIN (label gin_trgm_ops);
CREATE INDEX idx_graph_nodes_embedding ON graph_nodes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_graph_edges_user_id ON graph_edges(user_id);
CREATE INDEX idx_graph_edges_source_id ON graph_edges(source_id);
CREATE INDEX idx_graph_edges_target_id ON graph_edges(target_id);
CREATE INDEX idx_graph_edges_type ON graph_edges(type);
```

### Data Sources

The data sources table is used to store data source configurations:

```sql
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    config JSONB NOT NULL,
    credentials JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    last_sync TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient queries
CREATE INDEX idx_data_sources_user_id ON data_sources(user_id);
CREATE INDEX idx_data_sources_type ON data_sources(type);
CREATE INDEX idx_data_sources_status ON data_sources(status);
```

## Connection Configuration

The database connection is configured using the `DATABASE_URL` environment variable:

```
DATABASE_URL=postgresql://username:password@hostname:port/database
```

Example:

```
DATABASE_URL=postgresql://embediq_user:your_password@localhost:5432/embediq
```

See the [Environment Variables](environment_variables.md) documentation for more details.

## Database Migrations

The EmbedIQ backend does not currently use a migration tool. The database schema is created automatically when the application starts. However, for production deployments, it is recommended to use a migration tool like Alembic or Flyway to manage database schema changes.

## Backup and Restore

See the [Resource Management and Monitoring](resource_management_monitoring.md) documentation for information on database backup and restore procedures.
