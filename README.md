# EmbedIQ Backend

An open-source multi-tenant RAG (Retrieval-Augmented Generation) backend system powered by LightRAG for efficient document processing, knowledge graph construction, and intelligent query processing.

## 🚀 Features

- **Multi-tenant architecture** - Complete data isolation between users through LightRAG's working directory configuration
- **Document processing & vectorization** - Seamless document ingestion and embedding generation
- **Knowledge graph construction** - Automatic extraction of relationships between entities
- **Vector similarity search** - Find semantically relevant information across your data
- **Combined retrieval strategies** - Leverage both vector and graph-based approaches for comprehensive context retrieval
- **Auth0 integration** - Secure user authentication and authorization
- **Containerized deployment** - Docker-based setup for both development and production

## 🏗️ Architecture

EmbedIQ backend leverages LightRAG to handle all database operations and knowledge graph construction. The system employs a multi-tenant approach using LightRAG's working directory configuration to isolate data between users.

Key components:

- **LightRAG Core** - Manages all database operations internally, eliminating the need to manually create schemas or migrations
- **Multi-tenant Data Isolation** - Each user gets a dedicated working directory
- **Auth0 Authentication** - Handles user authentication and authorization
- **PostgreSQL with Extensions** - Pre-configured with vector and AGE graph extensions

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Auth0 account for authentication (or modify to use your preferred auth provider)

## ⚙️ Installation

### Development Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/embediq-backend.git
cd embediq-backend
```

2. Create a `.env` file with the following variables:

```
DATABASE_URL=postgresql://embediq:devpassword@database:5432/embediq
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_API_AUDIENCE=your-api-audience
DATA_DIR=/data/embediq/users
```

3. Start the development environment:

```bash
docker-compose up -d
```

## 🔍 Usage

### API Endpoints

#### Authentication

- `POST /api/v1/auth/token` - Validate Auth0 tokens
- `GET /api/v1/auth/profile` - Get user profile information

#### Data Management

- `POST /api/v1/documents` - Upload and manage documents
- `GET /api/v1/documents` - List uploaded documents
- `POST /api/v1/datasources` - Configure external data sources

#### Retrieval & Query

- `POST /api/v1/search` - Vector similarity search
- `GET /api/v1/graph` - Knowledge graph operations
- `POST /api/v1/query` - Combined RAG-powered queries

### Example: Uploading a Document

```python
import requests

# Authenticate and get token from Auth0
# ...

# Upload document
headers = {
    "Authorization": f"Bearer {token}"
}
files = {
    "file": open("document.pdf", "rb")
}
response = requests.post("http://localhost:8000/api/v1/documents", headers=headers, files=files)
print(response.json())
```

### Example: Querying Documents

```python
import requests

# Authenticate and get token from Auth0
# ...

# Query documents
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
data = {
    "text": "What are the key benefits of RAG systems?",
    "max_chunks": 5
}
response = requests.post("http://localhost:8000/api/v1/query", headers=headers, json=data)
print(response.json())
```

## 🛠️ Development

### Project Structure

```
embediq-backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── documents.py
│   │   │   ├── query.py
│   │   │   └── ...
│   │   └── dependencies.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── ...
│   ├── rag/
│   │   ├── manager.py
│   │   └── ...
│   └── main.py
├── docker/
│   ├── Dockerfile
│   └── ...
├── tests/
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [LightRAG](https://github.com/link-to-lightrag) for the core RAG functionality
- The PostgreSQL community for vector and graph extension support
- Auth0 for authentication services

## 📚 Documentation

For more detailed documentation, please visit our [Wiki](https://github.com/yourusername/embediq-backend/wiki) or check the `docs/` directory in this repository.
