# Deployment Guide

This guide covers deploying the Docs2Vector Pipeline API to various environments.

## Table of Contents

- [Deployment Options](#deployment-options)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Deployment Options

| Option | Complexity | Cost | Best For |
|--------|-----------|------|----------|
| **Local** | Low | Free | Development, Testing |
| **Docker Compose** | Medium | Low | Small deployments, VPS |
| **Cloud Run** | Medium | Pay-per-use | Production, Auto-scaling |
| **AWS Fargate** | Medium | Pay-per-use | Production, AWS ecosystem |
| **VPS (Droplet/EC2)** | Medium | Fixed | Predictable workloads |

---

## Local Development

### Prerequisites

- Python 3.11+
- pip
- virtualenv (recommended)

### Setup

1. **Clone Repository**
   ```bash
   cd /path/to/docs2vector-pipeline
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Run API Server**
   ```bash
   python scripts/run_api_server.py
   ```

6. **Test**
   ```bash
   # Health check
   curl http://localhost:8000/api/v1/health
   
   # View API docs
   open http://localhost:8000/docs
   ```

---

## Docker Deployment

### Option 1: Docker Compose (Recommended for VPS)

**Prerequisites:**
- Docker 20.10+
- Docker Compose 2.0+

**Steps:**

1. **Configure Environment**
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```

2. **Build and Start**
   ```bash
   docker-compose up -d
   ```

3. **Check Logs**
   ```bash
   docker-compose logs -f pipeline-api
   ```

4. **Test**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

5. **Stop**
   ```bash
   docker-compose down
   ```

### Option 2: Docker Only

**Build Image:**
```bash
docker build -t docs2vector-pipeline .
```

**Run Container:**
```bash
docker run -d \
  --name pipeline-api \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env:ro \
  docs2vector-pipeline
```

**View Logs:**
```bash
docker logs -f pipeline-api
```

---

## Cloud Deployment

### Option 1: Google Cloud Run (Serverless)

**Advantages:**
- ✅ Auto-scaling
- ✅ Pay only for usage
- ✅ Zero maintenance
- ✅ HTTPS automatically

**Steps:**

1. **Install Google Cloud SDK**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Build and Push Image**
   ```bash
   # Build for Cloud Run
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/docs2vector-pipeline
   ```

4. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy docs2vector-pipeline \
     --image gcr.io/YOUR_PROJECT_ID/docs2vector-pipeline \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="$(cat .env | grep -v '^#' | tr '\n' ',')" \
     --memory 2Gi \
     --timeout 3600 \
     --cpu 2
   ```

5. **Get URL**
   ```bash
   gcloud run services describe docs2vector-pipeline \
     --platform managed \
     --region us-central1 \
     --format 'value(status.url)'
   ```

**Note:** Cloud Run has a 60-minute timeout. For longer pipelines, use Cloud Run Jobs or other options.

---

### Option 2: AWS Fargate (Serverless Containers)

**Advantages:**
- ✅ Integrates with AWS services
- ✅ No server management
- ✅ VPC networking

**Steps:**

1. **Install AWS CLI**
   ```bash
   brew install awscli
   aws configure
   ```

2. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name docs2vector-pipeline
   ```

3. **Build and Push Image**
   ```bash
   # Get login credentials
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
   
   # Build image
   docker build -t docs2vector-pipeline .
   
   # Tag image
   docker tag docs2vector-pipeline:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/docs2vector-pipeline:latest
   
   # Push image
   docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/docs2vector-pipeline:latest
   ```

4. **Create ECS Task Definition**
   
   Create `task-definition.json`:
   ```json
   {
     "family": "docs2vector-pipeline",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "2048",
     "memory": "4096",
     "containerDefinitions": [{
       "name": "api",
       "image": "YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/docs2vector-pipeline:latest",
       "portMappings": [{
         "containerPort": 8000,
         "protocol": "tcp"
       }],
       "environment": [
         {"name": "USE_PINECONE", "value": "true"},
         {"name": "PINECONE_API_KEY", "value": "YOUR_KEY"}
       ],
       "logConfiguration": {
         "logDriver": "awslogs",
         "options": {
           "awslogs-group": "/ecs/docs2vector-pipeline",
           "awslogs-region": "us-east-1",
           "awslogs-stream-prefix": "ecs"
         }
       }
     }]
   }
   ```

5. **Register Task Definition**
   ```bash
   aws ecs register-task-definition --cli-input-json file://task-definition.json
   ```

6. **Create ECS Service**
   ```bash
   aws ecs create-service \
     --cluster default \
     --service-name docs2vector-pipeline \
     --task-definition docs2vector-pipeline \
     --desired-count 1 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
   ```

---

### Option 3: VPS (DigitalOcean, AWS EC2, etc.)

**Advantages:**
- ✅ Full control
- ✅ Predictable costs
- ✅ Simple setup

**Steps:**

1. **Create VPS**
   - Choose Ubuntu 22.04 LTS
   - Minimum: 2 CPU, 4GB RAM, 20GB disk
   - Recommended: 4 CPU, 8GB RAM, 50GB disk

2. **SSH into Server**
   ```bash
   ssh root@your-server-ip
   ```

3. **Install Docker**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Install Docker Compose
   apt install docker-compose-plugin
   ```

4. **Clone Repository**
   ```bash
   git clone https://github.com/your-repo/docs2vector-pipeline.git
   cd docs2vector-pipeline
   ```

5. **Configure**
   ```bash
   cp env.example .env
   nano .env  # Edit with your credentials
   ```

6. **Start Services**
   ```bash
   docker-compose up -d
   ```

7. **Setup Reverse Proxy (Optional)**
   
   Install Nginx:
   ```bash
   apt install nginx
   ```
   
   Create `/etc/nginx/sites-available/pipeline`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
   
   Enable site:
   ```bash
   ln -s /etc/nginx/sites-available/pipeline /etc/nginx/sites-enabled/
   nginx -t
   systemctl restart nginx
   ```

8. **Setup SSL with Certbot**
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d your-domain.com
   ```

---

## Configuration

### Required Environment Variables

```bash
# Pinecone (Required)
USE_PINECONE=true
PINECONE_API_KEY=your-api-key
PINECONE_INDEX_NAME=your-index-name
PINECONE_ENVIRONMENT=us-west1-gcp

# Pipeline Settings
PIPELINE_MODE=streaming
STORAGE_MODE=auto

# Embedding Settings
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_BATCH_SIZE=32
```

### Optional Variables

```bash
# AWS S3 (for data backup)
S3_BUCKET_NAME=your-bucket
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# N8N Webhook (for notifications)
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/abc123

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

### Pinecone Index Setup

**Create Index:**
1. Go to [Pinecone Console](https://app.pinecone.io/)
2. Click **"Create Index"**
3. Configure:
   - **Name**: `amazon-seller-docs` (or your choice)
   - **Dimensions**: `384` (for `BAAI/bge-small-en-v1.5`)
   - **Metric**: `cosine`
   - **Environment**: Choose closest to your deployment
4. Copy **API Key** and **Environment** to `.env`

---

## Monitoring

### Health Checks

**API Health:**
```bash
curl http://your-server/api/v1/health
```

**Container Health (Docker):**
```bash
docker ps
docker inspect pipeline-api | grep Health
```

### Logs

**Docker Compose:**
```bash
docker-compose logs -f pipeline-api
```

**Docker:**
```bash
docker logs -f pipeline-api
```

**Cloud Run:**
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=docs2vector-pipeline" --limit 50
```

### Monitoring Services

**Recommended:**
- **Uptime Monitoring**: UptimeRobot, Pingdom
- **Log Management**: Papertrail, Logtail
- **Error Tracking**: Sentry
- **Metrics**: Prometheus + Grafana

---

## Troubleshooting

### Issue: Container Won't Start

**Check logs:**
```bash
docker-compose logs pipeline-api
```

**Common causes:**
- Missing `.env` file
- Invalid Pinecone credentials
- Port 8000 already in use

**Solution:**
```bash
# Check if port is in use
lsof -i :8000

# Kill process using port
kill -9 $(lsof -t -i :8000)

# Restart
docker-compose restart
```

### Issue: Pipeline Fails During Execution

**Check API logs:**
```bash
docker-compose logs -f pipeline-api | grep ERROR
```

**Check pipeline logs:**
```bash
docker exec pipeline-api tail -f /app/logs/pipeline.log
```

**Common causes:**
- Pinecone index doesn't exist
- Wrong embedding dimensions
- Network connectivity issues
- Out of memory

### Issue: Can't Access API Externally

**Check firewall:**
```bash
# Ubuntu/Debian
ufw status
ufw allow 8000

# Or for HTTPS
ufw allow 80
ufw allow 443
```

**Check if API is listening:**
```bash
netstat -tlnp | grep 8000
```

### Issue: Slow Performance

**Increase resources:**

Docker Compose (`docker-compose.yml`):
```yaml
services:
  pipeline-api:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

**Or scale workers:**

Update `src/api/server.py`:
```python
executor = ThreadPoolExecutor(max_workers=2)  # Increase if needed
```

---

## Security Best Practices

### 1. Use Environment Variables
- Never commit `.env` to git
- Use secret management (AWS Secrets Manager, etc.)

### 2. Add Authentication (Production)
```python
# In server.py, add API key check
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
```

### 3. Use HTTPS
- Always use SSL in production
- Use Certbot for free certificates

### 4. Limit Access
- Use firewall rules
- Restrict to known IPs if possible
- Use VPN for internal services

### 5. Regular Updates
```bash
# Update base image regularly
docker pull python:3.11-slim

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

---

## Cost Estimation

### Google Cloud Run
- **Compute**: ~$0.10/hour when running (2 CPU, 2GB RAM)
- **Monthly** (1 run/month, 30 mins): ~$0.05
- **Free tier**: 180,000 vCPU-seconds/month

### AWS Fargate
- **Compute**: ~$0.08/hour (2 vCPU, 4GB RAM)
- **Monthly** (1 run/month, 30 mins): ~$0.04
- **Data transfer**: $0.09/GB

### VPS (DigitalOcean)
- **Basic Droplet**: $12/month (2 vCPU, 2GB RAM)
- **Recommended**: $24/month (2 vCPU, 4GB RAM)

### Pinecone
- **Starter**: Free (1 index, 100K vectors)
- **Standard**: $70/month (5M vectors)

---

## Next Steps

- **N8N Integration**: See [N8N_WORKFLOW.md](./N8N_WORKFLOW.md)
- **API Reference**: See [API_INTEGRATION.md](./API_INTEGRATION.md)
- **Set up monitoring and alerts**
- **Test end-to-end workflow**

