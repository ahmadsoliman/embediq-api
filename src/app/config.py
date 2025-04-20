import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

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
DATA_DIR = os.getenv("DATA_DIR", "/data/embediq/users")

# LightRAG configuration
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "1536"))
MAX_TOKEN_SIZE = int(os.getenv("MAX_TOKEN_SIZE", "8192"))
