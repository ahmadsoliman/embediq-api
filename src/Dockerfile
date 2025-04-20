FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app/app

# Create directory for user data and set permissions
RUN mkdir -p /data/embediq/users && chmod 777 /data/embediq/users

# Environment variables will be provided at runtime by docker-compose
ENV DATABASE_URL=""
ENV AUTH0_DOMAIN=""
ENV AUTH0_API_AUDIENCE=""
ENV DATA_DIR="/data/embediq/users"

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 