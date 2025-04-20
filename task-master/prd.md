# EmbedIQ Backend Architecture Document

**Version 1.0**
**Date: April 20, 2025**

## 1. Executive Summary

This document outlines the technical architecture for the EmbedIQ backend system. The backend will leverage the LightRAG framework to handle all database operations and knowledge graph construction. We will implement a multi-tenant approach using LightRAG's working directory configuration to isolate data between users authenticated via Auth0. The system will be containerized using Docker for both development and production deployment, utilizing a pre-configured PostgreSQL image (`eldoc92/postgres-rag-arm64:latest`) that already includes the necessary vector and AGE graph extensions.

## 2. LightRAG Integration

### 2.1 Overview of LightRAG

LightRAG is our core engine that handles all database operations, including:

1. Document processing and vectorization
2. Knowledge graph construction and management
3. Vector storage and similarity search
4. Graph operations for contextual enhancement
5. Combined retrieval strategies

The key advantage of using LightRAG is that it manages all the database operations internally. Our application doesn't need to create or manage database schemas, tables, indices, or query optimizations directly. Instead, we simply configure and interact with LightRAG's high-level API.

### 2.2 Multi-Tenant Data Isolation

To implement multi-tenant isolation, we will leverage LightRAG's `working_dir` parameter. Each authenticated user will have their own dedicated working directory where LightRAG will store all their data:

```python
def initialize_user_rag(user_id: str):
    # Create a unique working directory for this user
    user_dir = f"/data/embediq/users/{user_id}"
    os.makedirs(user_dir, exist_ok=True)

    # Initialize LightRAG with user-specific working directory
    rag = LightRAG(
        working_dir=user_dir,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=1536,
            max_token_size=8192,
            func=embedding_func,
        ),
    )

    return rag
```

This approach ensures complete data isolation between users, as each user's:

- Document collections
- Vector embeddings
- Knowledge graphs
- Query history
- Configuration settings

All reside in their own dedicated directory that only they can access.

## 3. Authentication and Authorization

### 3.1 Auth0 Integration

User authentication will be handled through Auth0 with:

1. JWT token validation for API requests
2. User profile synchronization with internal user registry
3. Role-based access control for different feature access
4. User ID extraction for LightRAG directory mapping

### 3.2 Authorization Flow

1. User authenticates via Auth0, receiving a JWT
2. Backend validates JWT and extracts user identifier
3. User identifier is mapped to a specific LightRAG working directory
4. All operations for that session use the user's dedicated LightRAG instance

Example authorization middleware:

```python
async def get_rag_for_user(request: Request):
    # Extract and validate user token
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Verify token with Auth0
        payload = jwt.decode(
            token,
            algorithms=["RS256"],
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )

        # Extract user ID
        user_id = payload["sub"]

        # Get or initialize user's RAG instance
        rag = get_or_create_rag_instance(user_id)

        return rag
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication: {str(e)}")
```

## 4. Docker Configuration

### 4.1 Database Container

We will use the pre-configured PostgreSQL image that already includes the vector and AGE graph extensions:

```yaml
database:
  image: eldoc92/postgres-rag-arm64:latest
  environment:
    - POSTGRES_USER=embediq
    - POSTGRES_PASSWORD=devpassword
    - POSTGRES_DB=embediq
  volumes:
    - postgres_data:/var/lib/postgresql/data
  ports:
    - '5432:5432'
```

LightRAG will connect to this database automatically and handle all schema creation and management internally. We don't need to write or maintain any SQL schemas or migrations.

### 4.2 Development Environment

For local development, we will use Docker Compose with:

```yaml
version: '3.8'

services:
  database:
    image: eldoc92/postgres-rag-arm64:latest
    environment:
      - POSTGRES_USER=embediq
      - POSTGRES_PASSWORD=devpassword
      - POSTGRES_DB=embediq
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - '5432:5432'

  backend:
    build: ./backend
    volumes:
      - ./backend:/app
      - user_data:/data/embediq/users # Mounted volume for user data
    depends_on:
      - database
    environment:
      - DATABASE_URL=postgresql://embediq:devpassword@database:5432/embediq
      - AUTH0_DOMAIN=dev-embediq.us.auth0.com
      - AUTH0_API_AUDIENCE=https://api.embediq.dev
      - DATA_DIR=/data/embediq/users
    ports:
      - '8000:8000'

volumes:
  postgres_data:
  user_data: # Persistent volume for user data across container restarts
```

### 4.3 Production Deployment

For production deployment:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app

# Create directory for user data
RUN mkdir -p /data/embediq/users && chmod 777 /data/embediq/users

# Environment variables will be provided at runtime
ENV DATABASE_URL=""
ENV AUTH0_DOMAIN=""
ENV AUTH0_API_AUDIENCE=""
ENV DATA_DIR="/data/embediq/users"

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 5. Backend API Structure

### 5.1 Core API Endpoints

The backend will expose the following RESTful endpoints:

1. **Authentication**:

   - `/api/v1/auth/token` - Validate Auth0 tokens
   - `/api/v1/auth/profile` - Get user profile information

2. **Data Management**:

   - `/api/v1/documents` - Upload and manage documents
   - `/api/v1/datasources` - Configure external data sources

3. **Retrieval & Query**:
   - `/api/v1/search` - Vector similarity search
   - `/api/v1/graph` - Knowledge graph operations
   - `/api/v1/query` - Combined RAG-powered queries

### 5.2 LightRAG Integration in API Routes

Example of how API routes will integrate with user-specific LightRAG instances:

```python
@router.post("/documents")
async def upload_document(
    file: UploadFile,
    rag: LightRAG = Depends(get_rag_for_user)
):
    # Save uploaded file temporarily
    temp_file_path = f"/tmp/{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        # Use LightRAG to process the document
        doc_id = await rag.add_document(
            document_path=temp_file_path,
            document_name=file.filename
        )

        return {"document_id": doc_id, "status": "processed"}
    finally:
        # Clean up temporary file
        os.remove(temp_file_path)

@router.post("/query")
async def query_documents(
    query: QueryRequest,
    rag: LightRAG = Depends(get_rag_for_user)
):
    # Use LightRAG to perform the query
    response = await rag.query(
        query=query.text,
        max_chunks=query.max_chunks or 5
    )

    return {
        "answer": response.answer,
        "sources": response.sources,
        "confidence": response.confidence
    }
```

## 6. LightRAG Instance Management

### 6.1 RAG Instance Factory

To efficiently manage LightRAG instances for multiple users:

```python
class RAGInstanceManager:
    def __init__(self, base_dir: str, database_url: str):
        self.base_dir = base_dir
        self.database_url = database_url
        self.instances = {}

    def get_instance(self, user_id: str) -> LightRAG:
        """Get or create a LightRAG instance for a specific user."""
        if user_id not in self.instances:
            # Create user directory if it doesn't exist
            user_dir = os.path.join(self.base_dir, user_id)
            os.makedirs(user_dir, exist_ok=True)

            # Initialize LightRAG with user-specific directory
            self.instances[user_id] = LightRAG(
                working_dir=user_dir,
                llm_model_func=get_llm_model_func(),
                embedding_func=get_embedding_func(),
                db_connection_string=self.database_url
            )

        return self.instances[user_id]
```

### 6.2 Resource Management

To prevent memory issues with many concurrent users:

```python
class LRURAGManager(RAGInstanceManager):
    def __init__(self, base_dir: str, database_url: str, max_instances: int = 100):
        super().__init__(base_dir, database_url)
        self.max_instances = max_instances
        self.lru_order = []

    def get_instance(self, user_id: str) -> LightRAG:
        """Get or create a LightRAG instance with LRU caching."""
        if user_id in self.instances:
            # Move to front of LRU list
            self.lru_order.remove(user_id)
            self.lru_order.append(user_id)
            return self.instances[user_id]

        # If we're at capacity, remove least recently used instance
        if len(self.instances) >= self.max_instances and self.lru_order:
            lru_user = self.lru_order.pop(0)
            del self.instances[lru_user]

        # Create new instance
        rag = super().get_instance(user_id)
        self.lru_order.append(user_id)
        return rag
```

## 7. Data Storage and Management

### 7.1 User Data Storage

Each user's data will be stored in their dedicated directory:

```
/data/embediq/users/
  ├── user_id_1/
  │     ├── documents/
  │     ├── embeddings/
  │     ├── graph/
  │     └── config.json
  ├── user_id_2/
  │     ├── documents/
  │     ├── embeddings/
  │     └── ...
  └── ...
```

LightRAG will automatically manage all files and database entries within these directories. Our application is responsible only for:

1. Creating the base directory structure
2. Managing access control to these directories
3. Initializing LightRAG with the correct paths
4. Backup and disaster recovery processes

### 7.2 Backup Strategy

For data durability:

1. Regular snapshots of the user data directories
2. Database backups (handled by standard PostgreSQL backup tools)
3. Data replication across availability zones in production

## 8. Development Workflow

### 8.1 Local Development

The development workflow will consist of:

1. Docker-based local environment setup
2. Hot-reload for rapid code iteration
3. Automated test suite with isolated test users
4. Performance profiling with sample datasets

### 8.2 Deployment Process

The deployment pipeline will:

1. Build Docker images for backend components
2. Perform automated testing
3. Deploy to staging environment
4. Run integration tests
5. Deploy to production with blue/green strategy

## 9. Performance Considerations

### 9.1 LightRAG Configuration Optimization

To optimize LightRAG performance:

1. Configure appropriate chunk sizes for different document types
2. Tune embedding model parameters for accuracy vs. speed tradeoffs
3. Adjust graph traversal depth based on query complexity
4. Implement caching for frequent queries
5. Configure appropriate batch sizes for document processing

### 9.2 Scaling Strategy

Initial scaling approach:

1. Vertical scaling of servers for increased user capacity
2. Instance caching with LRU eviction to manage memory usage
3. Separate worker processes for long-running ingestion jobs
4. Result caching for frequent queries
5. Eventual partition by user geography for reduced latency

## 10. Security Considerations

### 10.1 Data Security

To ensure data security:

1. Strict directory permissions to isolate user data
2. Encrypted volumes for user data storage
3. Secure deletion process when users remove their accounts
4. Regular security audits of file system access patterns
5. Principle of least privilege for service accounts

### 10.2 Authentication Security

For secure authentication:

1. Short-lived JWT tokens
2. Regular key rotation
3. IP-based rate limiting
4. Suspicious activity monitoring
5. OAuth 2.0 best practices

## 11. Future Considerations

For future expansion:

1. Distributed LightRAG instances across multiple servers
2. Shared embeddings for common documents while maintaining privacy
3. Multi-region deployment for global user base
4. Advanced caching strategies for high-traffic instances
5. Fine-tuning options for domain-specific knowledge bases

## 12. Conclusion

This backend architecture leverages LightRAG's capabilities to handle all database operations, significantly simplifying our implementation. By using the working directory configuration pattern, we achieve clean multi-tenant isolation without having to write custom database schemas or migrations. The containerized approach with the pre-configured PostgreSQL image ensures consistency across development and production environments.

The focus on directory-based isolation provides strong security boundaries between users while maintaining the flexibility to scale the system as user requirements grow. All database operations are delegated to LightRAG, allowing our team to focus on building a robust API layer and integration with authentication systems.

---

Document prepared by: EmbedIQ Engineering Team  
Last updated: April 20, 2025
