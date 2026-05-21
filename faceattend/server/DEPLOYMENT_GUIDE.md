# Deployment Guide - Smart Attendance System

Complete guide for deploying the separated Backend API and ML Service.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Serverless Deployment](#serverless-deployment)
6. [Load Balancing](#load-balancing)
7. [Monitoring & Logging](#monitoring--logging)
8. [Troubleshooting](#troubleshooting)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│                 http://localhost:5173                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├─── Load Balancer (Optional)
                     │
      ┌──────────────┴──────────────┐
      │                             │
┌─────▼──────────┐         ┌────────▼─────────┐
│  Backend API   │◄────────│   ML Service     │
│  Port: 8000    │  HTTP   │   Port: 8001     │
└─────┬──────────┘         └──────────────────┘
      │
      ├─────────────┬
      │             │
┌─────▼─────┐  ┌───▼────┐
│  MongoDB  │  │ Cloud  │
│           │  │ inary  │
└───────────┘  └────────┘
```

## Local Development

### Prerequisites

- Python 3.10+
- MongoDB 5.0+
- Docker & Docker Compose (optional)

### Step 1: Setup MongoDB

**Option A: Local MongoDB**
```bash
# macOS
brew install mongodb-community
brew services start mongodb-community

# Ubuntu
sudo apt-get install mongodb
sudo systemctl start mongodb

# Windows
# Download from mongodb.com and install
```

**Option B: MongoDB Atlas (Cloud)**
1. Create account at mongodb.com/atlas
2. Create cluster
3. Get connection string
4. Update MONGO_URI in .env

### Step 2: Setup ML Service

```bash
cd server/ml-service

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run service
python -m app.main
```

ML Service will run on http://localhost:8001

### Step 3: Setup Backend API

```bash
cd server/backend-api

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Configure .env (see Configuration section)
# IMPORTANT: Set ML_SERVICE_URL=http://localhost:8001

# Run service
python -m app.main
```

Backend API will run on http://localhost:8000

### Step 4: Verify Services

```bash
# Check ML Service
curl http://localhost:8001/health

# Check Backend API
curl http://localhost:8000/

# Test ML integration
# (requires authenticated request with image)
```

## Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Quick Start

```bash
cd server

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services Started

- **MongoDB**: Port 27017
- **ML Service**: Port 8001
- **Backend API**: Port 8000

### Configuration

1. **Create .env file** for backend-api:
```bash
cd backend-api
cp .env.example .env
# Edit .env with your credentials
```

2. **Update docker-compose.yml** if needed:
```yaml
environment:
  - MONGO_URI=mongodb://mongodb:27017/smart_attendance
  - ML_SERVICE_URL=http://ml-service:8001
```

### Scaling Services

```bash
# Scale ML service to 3 instances
docker-compose up -d --scale ml-service=3

# Scale backend API to 2 instances
docker-compose up -d --scale backend-api=2
```

Note: You'll need a load balancer for multiple instances.

## Cloud Deployment

### AWS Deployment

#### Option 1: ECS with Fargate

**1. Build and Push Images**
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build and push ML Service
cd server/ml-service
docker build -t ml-service .
docker tag ml-service:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ml-service:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ml-service:latest

# Build and push Backend API
cd ../backend-api
docker build -t backend-api .
docker tag backend-api:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/backend-api:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/backend-api:latest
```

**2. Create ECS Task Definitions**

ML Service Task Definition:
```json
{
  "family": "ml-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "ml-service",
      "image": "YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ml-service:latest",
      "portMappings": [
        {
          "containerPort": 8001,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "LOG_LEVEL", "value": "info"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ml-service",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**3. Create ECS Services**
```bash
# Create ML Service
aws ecs create-service \
  --cluster smart-attendance \
  --service-name ml-service \
  --task-definition ml-service \
  --desired-count 2 \
  --launch-type FARGATE

# Create Backend API Service
aws ecs create-service \
  --cluster smart-attendance \
  --service-name backend-api \
  --task-definition backend-api \
  --desired-count 2 \
  --launch-type FARGATE
```

**4. Setup Load Balancer**
```bash
# Create Application Load Balancer
aws elbv2 create-load-balancer \
  --name smart-attendance-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# Create target groups for each service
# Configure health checks
# Update ECS services to use ALB
```

#### Option 2: EC2 with Docker

**1. Launch EC2 Instances**
```bash
# Launch instance
aws ec2 run-instances \
  --image-id ami-xxx \
  --instance-type t3.medium \
  --key-name your-key \
  --security-group-ids sg-xxx
```

**2. Install Docker**
```bash
# SSH into instance
ssh -i your-key.pem ec2-user@instance-ip

# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**3. Deploy Services**
```bash
# Clone repository
git clone https://github.com/your-repo/SmartAttendanceSeparated.git
cd SmartAttendanceSeparated/server

# Setup .env
nano backend-api/.env

# Start services
docker-compose up -d
```

### Google Cloud Platform

#### Cloud Run Deployment

**1. Build and Deploy ML Service**
```bash
cd server/ml-service

# Build and submit to Cloud Build
gcloud builds submit --tag gcr.io/PROJECT_ID/ml-service

# Deploy to Cloud Run
gcloud run deploy ml-service \
  --image gcr.io/PROJECT_ID/ml-service \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --allow-unauthenticated
```

**2. Build and Deploy Backend API**
```bash
cd server/backend-api

# Build and submit
gcloud builds submit --tag gcr.io/PROJECT_ID/backend-api

# Deploy to Cloud Run
gcloud run deploy backend-api \
  --image gcr.io/PROJECT_ID/backend-api \
  --platform managed \
  --region us-central1 \
  --memory 1Gi \
  --set-env-vars ML_SERVICE_URL=https://ml-service-xxx.run.app \
  --allow-unauthenticated
```

**3. Setup MongoDB Atlas**
```bash
# Create MongoDB Atlas cluster
# Get connection string
# Update backend-api environment variables
gcloud run services update backend-api \
  --set-env-vars MONGO_URI=mongodb+srv://...
```

### Azure Deployment

#### Azure Container Instances

```bash
# Login to Azure
az login

# Create resource group
az group create --name smart-attendance --location eastus

# Create container registry
az acr create --resource-group smart-attendance \
  --name smartattendanceacr --sku Basic

# Build and push ML Service
cd server/ml-service
az acr build --registry smartattendanceacr \
  --image ml-service:v1 .

# Deploy ML Service
az container create \
  --resource-group smart-attendance \
  --name ml-service \
  --image smartattendanceacr.azurecr.io/ml-service:v1 \
  --cpu 2 --memory 4 \
  --ports 8001

# Deploy Backend API
cd ../backend-api
az acr build --registry smartattendanceacr \
  --image backend-api:v1 .

az container create \
  --resource-group smart-attendance \
  --name backend-api \
  --image smartattendanceacr.azurecr.io/backend-api:v1 \
  --cpu 1 --memory 2 \
  --ports 8000 \
  --environment-variables \
    ML_SERVICE_URL=http://ml-service:8001
```

## Serverless Deployment

### AWS Lambda + API Gateway

**ML Service as Lambda Function**

1. **Create Lambda-compatible handler**
```python
# ml-service/app/lambda_handler.py
from mangum import Mangum
from app.main import app

handler = Mangum(app)
```

2. **Create Dockerfile for Lambda**
```dockerfile
# Dockerfile.lambda
FROM public.ecr.aws/lambda/python:3.10

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install mangum

COPY app/ ${LAMBDA_TASK_ROOT}/app/

CMD ["app.lambda_handler.handler"]
```

3. **Deploy to Lambda**
```bash
# Build image
docker build -f Dockerfile.lambda -t ml-service-lambda .

# Tag for ECR
docker tag ml-service-lambda:latest \
  YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ml-service-lambda:latest

# Push to ECR
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ml-service-lambda:latest

# Create Lambda function
aws lambda create-function \
  --function-name ml-service \
  --package-type Image \
  --code ImageUri=YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ml-service-lambda:latest \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --memory-size 3008 \
  --timeout 300
```

4. **Setup API Gateway**
```bash
# Create REST API
aws apigateway create-rest-api --name ml-service-api

# Create integration with Lambda
# Configure routes
# Deploy API
```

**Considerations for Lambda:**
- Cold start: ~5-10s for first request
- Memory: At least 3GB for face_recognition
- Timeout: Set to 5 minutes for batch operations
- Cost: Pay per request (very cost-effective)

### Google Cloud Functions

```bash
# Deploy ML Service
gcloud functions deploy ml-service \
  --gen2 \
  --runtime python310 \
  --source server/ml-service \
  --entry-point app \
  --memory 2048MB \
  --timeout 300s \
  --trigger-http \
  --allow-unauthenticated
```

## Load Balancing

### Nginx Configuration

```nginx
# /etc/nginx/conf.d/smart-attendance.conf

upstream backend-api {
    least_conn;
    server backend-api-1:8000;
    server backend-api-2:8000;
    server backend-api-3:8000;
}

upstream ml-service {
    least_conn;
    server ml-service-1:8001 max_fails=3 fail_timeout=30s;
    server ml-service-2:8001 max_fails=3 fail_timeout=30s;
    server ml-service-3:8001 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.smartattendance.com;

    # Backend API
    location /api/ {
        proxy_pass http://backend-api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Health check
    location /health {
        access_log off;
        proxy_pass http://backend-api;
    }
}

server {
    listen 80;
    server_name ml.smartattendance.com;

    # ML Service (internal only)
    location / {
        proxy_pass http://ml-service;
        proxy_set_header Host $host;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Deny external access
    allow 10.0.0.0/8;
    deny all;
}
```

### HAProxy Configuration

```haproxy
# /etc/haproxy/haproxy.cfg

global
    maxconn 4096
    log 127.0.0.1 local0

defaults
    mode http
    timeout connect 5s
    timeout client 50s
    timeout server 50s

frontend backend-api-frontend
    bind *:8000
    default_backend backend-api-servers

backend backend-api-servers
    balance roundrobin
    option httpchk GET /
    server api1 backend-api-1:8000 check
    server api2 backend-api-2:8000 check
    server api3 backend-api-3:8000 check

frontend ml-service-frontend
    bind *:8001
    default_backend ml-service-servers

backend ml-service-servers
    balance leastconn
    option httpchk GET /health
    server ml1 ml-service-1:8001 check
    server ml2 ml-service-2:8001 check
    server ml3 ml-service-3:8001 check
```

## Monitoring & Logging

### Prometheus + Grafana

**1. Add Prometheus metrics to services**

```python
# requirements.txt
prometheus-client

# app/main.py
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('requests_total', 'Total requests')
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

**2. Prometheus configuration**

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend-api'
    static_configs:
      - targets: ['backend-api:8000']

  - job_name: 'ml-service'
    static_configs:
      - targets: ['ml-service:8001']
```

**3. Grafana dashboards**
- Import pre-built FastAPI dashboard
- Create custom dashboard for ML metrics
- Setup alerts for high latency, errors

### ELK Stack (Elasticsearch, Logstash, Kibana)

**1. Structured logging**

```python
import structlog

logger = structlog.get_logger()

logger.info("attendance_marked", 
           user_id=user_id, 
           subject_id=subject_id,
           faces_detected=len(faces))
```

**2. Ship logs to Elasticsearch**
- Use Filebeat or Fluentd
- Configure index patterns
- Create Kibana visualizations

### CloudWatch (AWS)

```bash
# Create log groups
aws logs create-log-group --log-group-name /ecs/backend-api
aws logs create-log-group --log-group-name /ecs/ml-service

# Create alarms
aws cloudwatch put-metric-alarm \
  --alarm-name high-error-rate \
  --alarm-description "Alert on high error rate" \
  --metric-name Errors \
  --namespace AWS/ECS \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

## Troubleshooting

### Common Issues

**1. ML Service Connection Timeout**
```
Error: ML Service timeout after 3 retries
```
Solutions:
- Increase `ML_SERVICE_TIMEOUT` (default: 30s)
- Scale ML service horizontally
- Check ML service logs for errors
- Reduce `num_jitters` parameter

**2. Out of Memory (OOM)**
```
Container killed due to OOM
```
Solutions:
- Increase container memory
- Reduce concurrent requests
- Optimize image processing
- Use smaller detection model (HOG vs CNN)

**3. Slow Face Detection**
```
Request taking >10 seconds
```
Solutions:
- Use HOG model instead of CNN
- Reduce image resolution
- Scale ML service
- Implement request caching

**4. Database Connection Pool Exhausted**
```
Error: Too many connections to MongoDB
```
Solutions:
- Increase MongoDB connection pool size
- Scale backend API instances
- Review connection cleanup
- Use connection pooling properly

### Performance Optimization

**1. ML Service:**
- Use HOG model for CPU deployments
- Reduce `num_jitters` to 1-3
- Implement result caching
- Use GPU instances for CNN model

**2. Backend API:**
- Enable database connection pooling
- Cache frequently accessed data
- Use async/await properly
- Implement request queuing

**3. Infrastructure:**
- Deploy services in same region
- Use private networking
- Enable HTTP/2
- Use CDN for static assets

### Health Check Endpoints

**Backend API:**
```bash
curl http://localhost:8000/
# Should return: {"service": "Smart Attendance API", ...}
```

**ML Service:**
```bash
curl http://localhost:8001/health
# Should return: {"status": "healthy", "models_loaded": true, ...}
```

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Set strong JWT_SECRET
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable firewall rules
- [ ] Restrict ML service to private network
- [ ] Implement rate limiting
- [ ] Regular security updates
- [ ] Enable audit logging
- [ ] Backup database regularly

## Maintenance

### Backup Strategy

**MongoDB:**
```bash
# Daily automated backup
mongodump --uri="mongodb://..." --out=/backup/$(date +%Y%m%d)

# Upload to S3
aws s3 cp /backup/$(date +%Y%m%d) s3://backups/mongodb/
```

**Cloudinary:**
- Enable automated backups in Cloudinary dashboard
- Or periodically sync to S3

### Update Procedure

1. Test in staging environment
2. Backup database
3. Deploy new version (blue-green)
4. Run smoke tests
5. Monitor for errors
6. Rollback if needed

### Rollback Plan

```bash
# Docker Compose
docker-compose down
git checkout previous-version
docker-compose up -d

# ECS
aws ecs update-service \
  --cluster smart-attendance \
  --service backend-api \
  --task-definition backend-api:previous-version
```

## Support

For deployment issues:
1. Check service logs
2. Verify environment variables
3. Test health endpoints
4. Review this guide
5. Open GitHub issue

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-20  
**Maintained By**: Development Team
