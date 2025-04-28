FROM python:3.12-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
  gcc \
  python3-dev \
  libffi-dev \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get purge -y --auto-remove gcc python3-dev libffi-dev build-essential

# Copy application code
COPY ./app /app/app

# Create directory for user data and set permissions
RUN mkdir -p /data/embediq/users && chmod 777 /data/embediq/users

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 