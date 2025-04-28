# Deployment

This document describes how to deploy the EmbedIQ backend to various environments.

## Deployment Options

The EmbedIQ backend can be deployed in several ways:

1. **Docker Deployment**: Deploy using Docker and Docker Compose.
2. **Kubernetes Deployment**: Deploy to a Kubernetes cluster.
3. **Cloud Platform Deployment**: Deploy to cloud platforms like AWS, Azure, or Google Cloud.
4. **Traditional Server Deployment**: Deploy to a traditional server.

## Prerequisites

- Python 3.10 or later
- PostgreSQL 14 or later with the following extensions:
  - `pgvector` for vector operations
  - `uuid-ossp` for UUID generation
  - `pg_trgm` for text search
- Docker (for containerized deployment)
- Kubernetes (for Kubernetes deployment)

## Docker Deployment

### Building the Docker Image

```bash
# From the project root
docker build -t embediq-backend:latest -f src/Dockerfile .
```

### Running with Docker Compose

1. Create a `docker-compose.yml` file:

```yaml
version: '3'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: devpassword
      POSTGRES_DB: embediq
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    image: embediq-backend:latest
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://postgres:devpassword@db:5432/embediq
      - AUTH0_DOMAIN=your-auth0-domain.auth0.com
      - AUTH0_API_AUDIENCE=your-auth0-api-audience
      - DATA_DIR=/data/embediq/users
    volumes:
      - embediq_data:/data/embediq
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  embediq_data:
```

2. Start the services:

```bash
docker-compose up -d
```

3. Check the logs:

```bash
docker-compose logs -f api
```

### Running with Docker Swarm

1. Initialize Docker Swarm:

```bash
docker swarm init
```

2. Deploy the stack:

```bash
docker stack deploy -c docker-compose.yml embediq
```

3. Check the services:

```bash
docker service ls
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster
- kubectl
- Helm (optional)

### Deploying with kubectl

1. Create a namespace:

```bash
kubectl create namespace embediq
```

2. Create a ConfigMap for environment variables:

```yaml
# embediq-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: embediq-config
  namespace: embediq
data:
  DATABASE_URL: "postgresql://postgres:devpassword@embediq-db:5432/embediq"
  AUTH0_DOMAIN: "your-auth0-domain.auth0.com"
  AUTH0_API_AUDIENCE: "your-auth0-api-audience"
  DATA_DIR: "/data/embediq/users"
```

```bash
kubectl apply -f embediq-configmap.yaml
```

3. Create a Secret for sensitive information:

```bash
kubectl create secret generic embediq-secrets \
  --namespace embediq \
  --from-literal=postgres-password=devpassword
```

4. Create a PostgreSQL deployment:

```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: embediq-db
  namespace: embediq
spec:
  replicas: 1
  selector:
    matchLabels:
      app: embediq-db
  template:
    metadata:
      labels:
        app: embediq-db
    spec:
      containers:
      - name: postgres
        image: postgres:14
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_USER
          value: postgres
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: embediq-secrets
              key: postgres-password
        - name: POSTGRES_DB
          value: embediq
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-data
        persistentVolumeClaim:
          claimName: postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: embediq-db
  namespace: embediq
spec:
  selector:
    app: embediq-db
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: embediq
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

```bash
kubectl apply -f postgres-deployment.yaml
```

5. Create an EmbedIQ backend deployment:

```yaml
# embediq-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: embediq-api
  namespace: embediq
spec:
  replicas: 3
  selector:
    matchLabels:
      app: embediq-api
  template:
    metadata:
      labels:
        app: embediq-api
    spec:
      containers:
      - name: api
        image: embediq-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: embediq-config
        volumeMounts:
        - name: embediq-data
          mountPath: /data/embediq
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: embediq-data
        persistentVolumeClaim:
          claimName: embediq-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: embediq-api
  namespace: embediq
spec:
  selector:
    app: embediq-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: embediq-pvc
  namespace: embediq
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: embediq-ingress
  namespace: embediq
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: api.embediq.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: embediq-api
            port:
              number: 80
```

```bash
kubectl apply -f embediq-deployment.yaml
```

### Deploying with Helm

1. Create a Helm chart:

```bash
helm create embediq
```

2. Customize the chart files according to your needs.

3. Install the chart:

```bash
helm install embediq ./embediq --namespace embediq --create-namespace
```

## Cloud Platform Deployment

### AWS Deployment

#### Using AWS ECS (Elastic Container Service)

1. Create an ECR repository:

```bash
aws ecr create-repository --repository-name embediq-backend
```

2. Build and push the Docker image:

```bash
# Get the ECR login command
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account-id.dkr.ecr.us-east-1.amazonaws.com

# Build the image
docker build -t embediq-backend:latest -f src/Dockerfile .

# Tag the image
docker tag embediq-backend:latest your-account-id.dkr.ecr.us-east-1.amazonaws.com/embediq-backend:latest

# Push the image
docker push your-account-id.dkr.ecr.us-east-1.amazonaws.com/embediq-backend:latest
```

3. Create an ECS cluster, task definition, and service using the AWS Management Console or AWS CLI.

#### Using AWS Elastic Beanstalk

1. Create a `Dockerrun.aws.json` file:

```json
{
  "AWSEBDockerrunVersion": "1",
  "Image": {
    "Name": "your-account-id.dkr.ecr.us-east-1.amazonaws.com/embediq-backend:latest",
    "Update": "true"
  },
  "Ports": [
    {
      "ContainerPort": 8000,
      "HostPort": 8000
    }
  ],
  "Volumes": [
    {
      "HostDirectory": "/data/embediq",
      "ContainerDirectory": "/data/embediq"
    }
  ],
  "Logging": "/var/log/embediq"
}
```

2. Create an Elastic Beanstalk application and environment using the AWS Management Console or AWS CLI.

### Azure Deployment

#### Using Azure Container Instances

1. Create an Azure Container Registry:

```bash
az acr create --resource-group myResourceGroup --name embediqregistry --sku Basic
```

2. Build and push the Docker image:

```bash
# Log in to the registry
az acr login --name embediqregistry

# Build the image
docker build -t embediq-backend:latest -f src/Dockerfile .

# Tag the image
docker tag embediq-backend:latest embediqregistry.azurecr.io/embediq-backend:latest

# Push the image
docker push embediqregistry.azurecr.io/embediq-backend:latest
```

3. Create an Azure Container Instance:

```bash
az container create \
  --resource-group myResourceGroup \
  --name embediq-api \
  --image embediqregistry.azurecr.io/embediq-backend:latest \
  --registry-login-server embediqregistry.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --dns-name-label embediq-api \
  --ports 8000 \
  --environment-variables \
    DATABASE_URL=postgresql://username:password@hostname:5432/embediq \
    AUTH0_DOMAIN=your-auth0-domain.auth0.com \
    AUTH0_API_AUDIENCE=your-auth0-api-audience \
    DATA_DIR=/data/embediq/users
```

#### Using Azure App Service

1. Create an Azure App Service plan:

```bash
az appservice plan create --name embediq-plan --resource-group myResourceGroup --sku B1 --is-linux
```

2. Create an Azure Web App:

```bash
az webapp create \
  --resource-group myResourceGroup \
  --plan embediq-plan \
  --name embediq-api \
  --deployment-container-image-name embediqregistry.azurecr.io/embediq-backend:latest
```

3. Configure environment variables:

```bash
az webapp config appsettings set \
  --resource-group myResourceGroup \
  --name embediq-api \
  --settings \
    DATABASE_URL=postgresql://username:password@hostname:5432/embediq \
    AUTH0_DOMAIN=your-auth0-domain.auth0.com \
    AUTH0_API_AUDIENCE=your-auth0-api-audience \
    DATA_DIR=/data/embediq/users
```

### Google Cloud Deployment

#### Using Google Cloud Run

1. Build and push the Docker image:

```bash
# Configure Docker to use the gcloud command-line tool as a credential helper
gcloud auth configure-docker

# Build the image
docker build -t gcr.io/your-project-id/embediq-backend:latest -f src/Dockerfile .

# Push the image
docker push gcr.io/your-project-id/embediq-backend:latest
```

2. Deploy to Cloud Run:

```bash
gcloud run deploy embediq-api \
  --image gcr.io/your-project-id/embediq-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars \
    DATABASE_URL=postgresql://username:password@hostname:5432/embediq,\
    AUTH0_DOMAIN=your-auth0-domain.auth0.com,\
    AUTH0_API_AUDIENCE=your-auth0-api-audience,\
    DATA_DIR=/data/embediq/users
```

#### Using Google Kubernetes Engine (GKE)

1. Create a GKE cluster:

```bash
gcloud container clusters create embediq-cluster \
  --zone us-central1-a \
  --num-nodes 3
```

2. Get credentials for the cluster:

```bash
gcloud container clusters get-credentials embediq-cluster --zone us-central1-a
```

3. Follow the Kubernetes deployment instructions above.

## Traditional Server Deployment

### Prerequisites

- Ubuntu 20.04 or later
- Python 3.10 or later
- PostgreSQL 14 or later
- Nginx
- Supervisor

### Installation

1. Update the system:

```bash
sudo apt update
sudo apt upgrade -y
```

2. Install dependencies:

```bash
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx supervisor
```

3. Install PostgreSQL extensions:

```bash
sudo apt install -y postgresql-14-pgvector
```

4. Create a database and user:

```bash
sudo -u postgres psql -c "CREATE DATABASE embediq;"
sudo -u postgres psql -c "CREATE USER embediq_user WITH ENCRYPTED PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE embediq TO embediq_user;"
```

5. Enable PostgreSQL extensions:

```bash
sudo -u postgres psql -d embediq -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -d embediq -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
sudo -u postgres psql -d embediq -c "CREATE EXTENSION IF NOT EXISTS uuid-ossp;"
```

6. Create a user for the application:

```bash
sudo useradd -m -s /bin/bash embediq
```

7. Clone the repository:

```bash
sudo -u embediq git clone https://github.com/yourusername/embediq-backend.git /home/embediq/embediq-backend
```

8. Create a virtual environment:

```bash
sudo -u embediq python3 -m venv /home/embediq/embediq-backend/venv
```

9. Install dependencies:

```bash
sudo -u embediq /home/embediq/embediq-backend/venv/bin/pip install -r /home/embediq/embediq-backend/requirements.txt
```

10. Create a configuration file:

```bash
sudo -u embediq mkdir -p /home/embediq/embediq-backend/config
sudo -u embediq cat > /home/embediq/embediq-backend/config/.env << EOF
DATABASE_URL=postgresql://embediq_user:your_password@localhost:5432/embediq
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_API_AUDIENCE=your-auth0-api-audience
DATA_DIR=/home/embediq/data/embediq/users
EOF
```

11. Create data directories:

```bash
sudo -u embediq mkdir -p /home/embediq/data/embediq/users
```

12. Configure Supervisor:

```bash
sudo cat > /etc/supervisor/conf.d/embediq.conf << EOF
[program:embediq]
command=/home/embediq/embediq-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
directory=/home/embediq/embediq-backend/src
user=embediq
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/embediq/stderr.log
stdout_logfile=/var/log/embediq/stdout.log
EOF
```

13. Create log directories:

```bash
sudo mkdir -p /var/log/embediq
sudo chown -R embediq:embediq /var/log/embediq
```

14. Configure Nginx:

```bash
sudo cat > /etc/nginx/sites-available/embediq << EOF
server {
    listen 80;
    server_name api.embediq.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
```

15. Enable the Nginx site:

```bash
sudo ln -s /etc/nginx/sites-available/embediq /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

16. Start the application:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start embediq
```

17. Set up SSL with Let's Encrypt:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.embediq.com
```

## Continuous Deployment

### GitHub Actions

1. Create a `.github/workflows/deploy.yml` file:

```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v1
    
    - name: Login to DockerHub
      uses: docker/login-action@v1
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
    
    - name: Build and push
      uses: docker/build-push-action@v2
      with:
        context: .
        file: src/Dockerfile
        push: true
        tags: yourusername/embediq-backend:latest
    
    - name: Deploy to server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SSH_HOST }}
        username: ${{ secrets.SSH_USERNAME }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /home/embediq/embediq-backend
          git pull
          docker-compose pull
          docker-compose up -d
```

### GitLab CI/CD

1. Create a `.gitlab-ci.yml` file:

```yaml
stages:
  - build
  - deploy

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE:latest -f src/Dockerfile .
    - docker push $CI_REGISTRY_IMAGE:latest

deploy:
  stage: deploy
  image: alpine:latest
  script:
    - apk add --no-cache openssh-client
    - mkdir -p ~/.ssh
    - echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
    - chmod 600 ~/.ssh/id_rsa
    - ssh-keyscan -H $SSH_HOST >> ~/.ssh/known_hosts
    - ssh $SSH_USER@$SSH_HOST "cd /home/embediq/embediq-backend && git pull && docker-compose pull && docker-compose up -d"
  only:
    - main
```

## Monitoring and Logging

### Prometheus and Grafana

1. Add Prometheus metrics to the application:

```python
from prometheus_client import Counter, Histogram, start_http_server

# Define metrics
REQUEST_COUNT = Counter('request_count', 'App Request Count', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency', ['method', 'endpoint'])

# Start metrics server
start_http_server(8001)
```

2. Configure Prometheus to scrape metrics:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'embediq'
    static_configs:
      - targets: ['embediq-api:8001']
```

3. Set up Grafana dashboards for monitoring.

### ELK Stack (Elasticsearch, Logstash, Kibana)

1. Configure logging to output in JSON format:

```python
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
        }
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

# Configure logging
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
```

2. Configure Logstash to collect and process logs.

3. Set up Kibana dashboards for log visualization.

## Scaling

### Horizontal Scaling

1. Increase the number of replicas in Kubernetes:

```bash
kubectl scale deployment embediq-api --replicas=5 -n embediq
```

2. Use a load balancer to distribute traffic across instances.

### Vertical Scaling

1. Increase resources for the application:

```yaml
# In Kubernetes
resources:
  requests:
    cpu: 1
    memory: 2Gi
  limits:
    cpu: 2
    memory: 4Gi
```

### Database Scaling

1. Use connection pooling with PgBouncer:

```bash
# Install PgBouncer
sudo apt install -y pgbouncer

# Configure PgBouncer
sudo cat > /etc/pgbouncer/pgbouncer.ini << EOF
[databases]
embediq = host=localhost port=5432 dbname=embediq

[pgbouncer]
listen_addr = *
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
EOF
```

2. Update the application to use PgBouncer:

```
DATABASE_URL=postgresql://embediq_user:your_password@localhost:6432/embediq
```

## Backup and Restore

See the [Resource Management and Monitoring](resource_management_monitoring.md) documentation for information on backup and restore procedures.
