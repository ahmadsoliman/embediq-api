"""
Application configuration module for EmbedIQ backend.

This module provides configuration options for the application.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Determine if we're running in Docker or locally
IN_DOCKER = os.path.exists("/.dockerenv")

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://embediq:devpassword@database:5432/embediq"
)

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "dev-embediq.us.auth0.com")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE", "https://api.embediq.dev")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "")  # No default for security
AUTH0_ALGORITHMS = ["RS256"]  # Auth0 uses RS256 by default

# Data directory configuration
# Use a path that's accessible for local development when not in Docker
if IN_DOCKER:
    DATA_DIR = os.getenv("DATA_DIR", "/data/embediq/users")
else:
    # Use a local directory for development
    DATA_DIR = os.getenv(
        "DATA_DIR",
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data"
        ),
    )

# LightRAG configuration
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "1536"))
MAX_TOKEN_SIZE = int(os.getenv("MAX_TOKEN_SIZE", "8192"))

# Monitoring configuration
ADMIN_USER_IDS = os.getenv("ADMIN_USER_IDS", "").split(",")
MONITORING_ENABLED = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
MONITORING_LOG_LEVEL = os.getenv("MONITORING_LOG_LEVEL", "INFO")

# Backup configuration
BACKUP_ENABLED = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
BACKUP_DIR = os.getenv("BACKUP_DIR", "/data/embediq/backups")
BACKUP_FREQUENCY = int(
    os.getenv("BACKUP_FREQUENCY", "86400")
)  # Default: daily (in seconds)
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))  # Default: 7 days

# LightRAG tuning parameters
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
GRAPH_TRAVERSAL_DEPTH = int(os.getenv("GRAPH_TRAVERSAL_DEPTH", "3"))
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_SIZE = int(os.getenv("CACHE_SIZE", "1000"))  # Number of items to cache
