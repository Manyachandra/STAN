# Deployment Guide

Complete guide for deploying the chatbot system to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Scaling](#scaling)
8. [Security](#security)

## Prerequisites

### Required

- Python 3.11+
- Redis 6.0+
- Google Gemini API key
- 2GB RAM minimum (4GB+ recommended)

### Optional

- MongoDB 7.0+ (for advanced analytics)
- Docker & Docker Compose
- Kubernetes cluster (for large-scale deployment)

## Local Development

### 1. Setup Environment

```bash
# Clone repository
cd chatbot_system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create `.env` file:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
REDIS_URL=redis://localhost:6379/0
MONGODB_URI=mongodb://localhost:27017
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### 3. Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install locally
# macOS: brew install redis && redis-server
# Ubuntu: sudo apt install redis-server && sudo service redis-server start
```

### 4. Run the Application

```bash
# Run basic example
python examples/basic_conversation.py

# Or start API server
python examples/api_server.py
```

Access API docs at: http://localhost:8000/docs

## Docker Deployment

### Build and Run with Docker Compose

```bash
# Set environment variables
export GEMINI_API_KEY=your_api_key

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f chatbot-api

# Stop services
docker-compose down
```

### Individual Container

```bash
# Build image
docker build -t chatbot-system:latest .

# Run container
docker run -d \
  --name chatbot \
  -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e REDIS_URL=redis://redis:6379/0 \
  chatbot-system:latest
```

## Cloud Deployment

### Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/chatbot-system

# Deploy
gcloud run deploy chatbot-system \
  --image gcr.io/PROJECT_ID/chatbot-system \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key,REDIS_URL=redis://... \
  --memory 2Gi \
  --cpu 2
```

### AWS ECS

1. Push image to ECR:

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

docker tag chatbot-system:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/chatbot-system:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/chatbot-system:latest
```

2. Create ECS task definition with:

   - 2GB memory
   - Environment variables for API keys
   - Redis endpoint from ElastiCache

3. Deploy service with load balancer

### Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chatbot-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chatbot-system
  template:
    metadata:
      labels:
        app: chatbot-system
    spec:
      containers:
        - name: chatbot
          image: gcr.io/PROJECT_ID/chatbot-system:latest
          ports:
            - containerPort: 8000
          env:
            - name: GEMINI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: chatbot-secrets
                  key: gemini-api-key
            - name: REDIS_URL
              value: "redis://redis-service:6379/0"
          resources:
            requests:
              memory: "2Gi"
              cpu: "1000m"
            limits:
              memory: "4Gi"
              cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: chatbot-service
spec:
  type: LoadBalancer
  selector:
    app: chatbot-system
  ports:
    - port: 80
      targetPort: 8000
```

Deploy:

```bash
kubectl apply -f deployment.yaml
```

## Configuration

### Production Settings

Update `config/settings.yaml`:

```yaml
api:
  gemini:
    temperature: 0.9
    max_output_tokens: 500

memory:
  retention_days: 90
  compress_after_messages: 10

safety:
  hallucination_prevention:
    enabled: true
  content_filtering:
    enabled: true
  rate_limiting:
    enabled: true
    requests_per_minute: 60

logging:
  level: "INFO"
  log_conversations: true
  anonymize_pii: true
```

### Persona Customization

Edit `config/persona.yaml` to customize:

- Name and personality
- Speaking style
- Response strategies
- Boundaries and values

## Monitoring

### Health Checks

```bash
# Check system health
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "checks": {
    "gemini_api": true,
    "redis": true,
    "persona": true,
    "overall": true
  }
}
```

### Metrics

Access Prometheus metrics at: http://localhost:9090

Key metrics to monitor:

- Request rate and latency
- Token usage per conversation
- Error rates
- Memory usage
- Active sessions

### Logging

Logs are structured JSON by default:

```json
{
	"timestamp": "2026-01-10T12:00:00Z",
	"level": "INFO",
	"message": "Message processed",
	"user_id": "user_123",
	"session_id": "session_456",
	"response_time_ms": 245,
	"tokens_used": 187
}
```

View logs:

```bash
# Docker
docker-compose logs -f chatbot-api

# Kubernetes
kubectl logs -f deployment/chatbot-system

# Local file
tail -f logs/chatbot.log
```

## Scaling

### Horizontal Scaling

The system is stateless and can scale horizontally:

**Docker Compose:**

```bash
docker-compose up -d --scale chatbot-api=5
```

**Kubernetes:**

```bash
kubectl scale deployment chatbot-system --replicas=10
```

**Cloud Run:**

```bash
gcloud run services update chatbot-system \
  --min-instances=2 \
  --max-instances=100
```

### Database Scaling

**Redis:**

- Use Redis Cluster for high availability
- Enable AOF persistence
- Configure memory limits appropriately

**MongoDB:**

- Use replica sets for reliability
- Enable sharding for large datasets
- Regular backups

### Load Balancing

Use a load balancer to distribute traffic:

- AWS ALB
- Google Cloud Load Balancer
- Nginx
- Traefik

## Security

### API Security

1. **Authentication:**

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/chat")
async def chat(credentials: HTTPAuthorizationCredentials = Security(security)):
    # Verify token
    if not verify_token(credentials.credentials):
        raise HTTPException(status_code=401)
```

2. **Rate Limiting:**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat")
@limiter.limit("60/minute")
async def chat():
    pass
```

### Environment Security

- Never commit API keys
- Use secrets management (AWS Secrets Manager, GCP Secret Manager)
- Rotate credentials regularly
- Enable TLS/SSL for all connections
- Use VPC/private networks

### Data Privacy

- Implement data retention policies
- Support user data export (GDPR)
- Enable data anonymization
- Regular security audits
- Encryption at rest and in transit

### Network Security

```yaml
# docker-compose with network isolation
networks:
  frontend:
  backend:

services:
  chatbot-api:
    networks:
      - frontend
      - backend

  redis:
    networks:
      - backend # Not accessible from outside
```

## Troubleshooting

### Common Issues

**1. Redis Connection Failed**

```bash
# Check Redis is running
redis-cli ping

# Check connection
telnet localhost 6379
```

**2. High Memory Usage**

- Reduce `max_conversation_history` in settings
- Enable memory compression
- Increase summarization frequency

**3. Slow Response Times**

- Check Gemini API latency
- Enable response caching
- Optimize prompt length
- Scale horizontally

**4. Safety Validation Failures**

- Review persona configuration
- Check safety layer rules
- Adjust validation thresholds

## Backup and Recovery

### Redis Backup

```bash
# Enable AOF
redis-cli CONFIG SET appendonly yes

# Manual backup
redis-cli BGSAVE

# Copy RDB file
cp /var/lib/redis/dump.rdb /backup/
```

### MongoDB Backup

```bash
# Backup
mongodump --uri="mongodb://localhost:27017" --out=/backup/

# Restore
mongorestore --uri="mongodb://localhost:27017" /backup/
```

## Performance Tuning

### Redis Optimization

```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
tcp-backlog 511
timeout 300
```

### Application Tuning

- Adjust `max_prompt_tokens` based on needs
- Enable connection pooling
- Use async/await throughout
- Implement request caching

## Support

For issues or questions:

- Check logs first
- Review health endpoint
- Check system metrics
- Contact AI engineering team

---

**Last Updated:** 2026-01-10
**Version:** 1.0.0
