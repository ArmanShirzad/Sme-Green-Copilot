# Green SME Compliance Co-Pilot - Deployment Guide

## Quick Deployment Options

### Option 1: Local Development (Fastest for Hackathon)

```bash
# 1. Setup (one-time)
./setup.sh

# 2. Run
./run.sh

# 3. Test
./test_endpoints.sh
```

**Access**:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

**Time**: 5 minutes

---

### Option 2: Docker Compose (Full Stack)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Stop all
docker-compose down
```

**Services**:
- API: http://localhost:8000
- MinIO Console: http://localhost:9001
- n8n: http://localhost:5678
- OpenWebUI: http://localhost:3000

**Time**: 10 minutes

---

### Option 3: Kubernetes (Production)

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: green-sme-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: green-sme-api
  template:
    metadata:
      labels:
        app: green-sme-api
    spec:
      containers:
      - name: api
        image: your-registry/green-sme-copilot:latest
        ports:
        - containerPort: 8000
        env:
        - name: DB_PATH
          value: "/app/data/db.sqlite"
        - name: OPENWEATHER_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openweather-key
        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: outputs
          mountPath: /app/outputs
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: green-sme-data
      - name: outputs
        persistentVolumeClaim:
          claimName: green-sme-outputs
---
apiVersion: v1
kind: Service
metadata:
  name: green-sme-api-service
spec:
  selector:
    app: green-sme-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy:

```bash
kubectl apply -f k8s-deployment.yaml
kubectl get pods
kubectl logs -f <pod-name>
```

---

## Cloud Platform Deployment

### AWS (Elastic Beanstalk)

1. Install EB CLI:
```bash
pip install awsebcli
```

2. Initialize:
```bash
eb init -p docker green-sme-copilot
```

3. Create environment:
```bash
eb create green-sme-prod
```

4. Deploy updates:
```bash
eb deploy
```

5. Configure environment variables:
```bash
eb setenv OPENWEATHER_API_KEY=your_key
eb setenv MISTRAL_API_KEY=your_key
```

### Google Cloud Run

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/green-sme-copilot

# Deploy
gcloud run deploy green-sme-copilot \
  --image gcr.io/PROJECT_ID/green-sme-copilot \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars OPENWEATHER_API_KEY=your_key
```

### Azure Container Instances

```bash
# Create resource group
az group create --name green-sme --location westeurope

# Deploy container
az container create \
  --resource-group green-sme \
  --name copilot-api \
  --image your-registry.azurecr.io/green-sme-copilot:latest \
  --dns-name-label green-sme-copilot \
  --ports 8000 \
  --environment-variables \
    OPENWEATHER_API_KEY=your_key \
    DB_PATH=/app/data/db.sqlite
```

---

## Environment Configuration

### Production .env Template

```bash
# Application
APP_ENV=production
APP_PORT=8000
LOG_LEVEL=INFO

# Database (use PostgreSQL for production)
DB_TYPE=postgresql
DB_HOST=db.example.com
DB_PORT=5432
DB_NAME=green_sme
DB_USER=app_user
DB_PASSWORD=secure_password

# Storage (use cloud storage for production)
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET=compliance-documents
S3_REGION=eu-central-1

# APIs
OPENWEATHER_API_KEY=your_key
MISTRAL_API_KEY=your_key

# n8n (production webhook)
N8N_WEBHOOK_URL=https://n8n.example.com/webhook/compliance-email

# Security
SECRET_KEY=generate_with_openssl_rand_hex_32
ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com

# Email (for n8n)
SMTP_HOST=smtp.eu.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@mg.example.com
SMTP_PASSWORD=smtp_password

# Monitoring
SENTRY_DSN=https://sentry.io/your-dsn
```

### Secrets Management

**AWS Secrets Manager**:
```bash
aws secretsmanager create-secret \
  --name green-sme/prod/api-keys \
  --secret-string '{"openweather":"key","mistral":"key"}'
```

**Google Secret Manager**:
```bash
echo -n "your_api_key" | gcloud secrets create openweather-key --data-file=-
```

**Azure Key Vault**:
```bash
az keyvault secret set \
  --vault-name green-sme-vault \
  --name openweather-key \
  --value your_api_key
```

---

## Database Migration (SQLite → PostgreSQL)

For production, migrate from SQLite to PostgreSQL:

1. Install PostgreSQL adapter:
```bash
pip install psycopg2-binary
```

2. Update `db_init.py`:
```python
# Change from:
conn = sqlite3.connect('db.sqlite')

# To:
import psycopg2
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
```

3. Export data:
```bash
sqlite3 db.sqlite .dump > dump.sql
```

4. Import to PostgreSQL:
```bash
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f dump.sql
```

---

## Scaling Considerations

### Horizontal Scaling

**Load Balancer Config** (nginx):
```nginx
upstream green_sme_backend {
    least_conn;
    server api1.example.com:8000;
    server api2.example.com:8000;
    server api3.example.com:8000;
}

server {
    listen 80;
    server_name api.greensme.example.com;
    
    location / {
        proxy_pass http://green_sme_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Caching

Add Redis for caching:

```python
# In utils.py
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)

def get_weather_data(city: str, country: str = "DE"):
    cache_key = f"weather:{city}:{country}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fetch from API
    result = fetch_weather_api(city, country)
    
    # Cache for 1 hour
    cache.setex(cache_key, 3600, json.dumps(result))
    return result
```

### Message Queue

Add Celery for async tasks:

```python
# tasks.py
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task
def generate_pdf_async(form_id, field_values):
    return fill_pdf_template(form_id, field_values)
```

---

## Monitoring & Logging

### Prometheus Metrics

Add to `main.py`:

```python
from prometheus_client import Counter, Histogram, make_asgi_app

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

@app.middleware("http")
async def monitor_requests(request, call_next):
    REQUEST_COUNT.inc()
    with REQUEST_LATENCY.time():
        response = await call_next(request)
    return response

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### Grafana Dashboard

Import JSON from monitoring templates.

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

@app.post("/tools/detectIntent")
async def detect_intent(request: DetectIntentRequest):
    logger.info("intent_detection_started", text=request.text[:50])
    result = detect_intent_with_llm(request.text)
    logger.info("intent_detection_completed", 
                intent=result.intentType, 
                confidence=result.confidence)
    return result
```

---

## Security Hardening

### 1. Enable HTTPS

Use Let's Encrypt:
```bash
certbot --nginx -d api.example.com
```

### 2. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/tools/detectIntent")
@limiter.limit("10/minute")
async def detect_intent(request: Request, body: DetectIntentRequest):
    pass
```

### 3. API Authentication

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials):
    # Verify JWT or API key
    pass

@app.post("/tools/detectIntent", dependencies=[Depends(verify_token)])
async def detect_intent():
    pass
```

### 4. Input Validation

Already implemented via Pydantic models. Ensure all endpoints use typed models.

---

## Backup & Recovery

### Database Backup

```bash
# Automated daily backup (cron)
0 2 * * * pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
```

### Document Storage Backup

```bash
# S3 to S3 replication
aws s3 sync s3://compliance-documents s3://compliance-documents-backup --region eu-west-1
```

---

## Health Checks

Enhanced health endpoint:

```python
@app.get("/health")
async def health_check():
    checks = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": check_database(),
            "storage": check_storage(),
            "ml_models": app_state.get('embed_model') is not None
        }
    }
    
    if not all(checks["checks"].values()):
        raise HTTPException(status_code=503, detail=checks)
    
    return checks
```

---

## Troubleshooting

### Common Issues

**1. Models not loading**
```bash
# Check available memory
free -h

# Reduce model size or use quantized version
pip install sentence-transformers[onnx]
```

**2. PDF generation fails**
```bash
# Check ReportLab fonts
python -c "from reportlab.pdfbase import pdfmetrics; print(pdfmetrics.getRegisteredFontNames())"
```

**3. OCR errors**
```bash
# Verify Tesseract installation
tesseract --version
tesseract --list-langs
```

**4. Database locks (SQLite)**
```bash
# Switch to PostgreSQL for production
# Or increase timeout:
conn = sqlite3.connect('db.sqlite', timeout=30)
```

---

## Performance Optimization

### 1. Pre-compute Embeddings

```python
# At startup, embed all form templates
def precompute_form_embeddings():
    forms = get_all_forms()
    for form in forms:
        embeddings = embed_model.encode(form.labels)
        faiss_index.add(embeddings)
        save_to_db(form.id, embeddings)
```

### 2. Async Operations

```python
import asyncio

@app.post("/tools/generateCompliancePack")
async def generate_pack(request: GenerateCompliancePackRequest):
    # Run tasks in parallel
    tasks = [
        generate_pdf_async(form_id, values),
        calculate_emissions_async(data),
        fetch_weather_async(city)
    ]
    results = await asyncio.gather(*tasks)
    return combine_results(results)
```

### 3. Connection Pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10
)
```

---

## Cost Optimization

### API Usage

- Cache weather API responses (1 hour TTL)
- Use Mistral API only for complex intent detection
- Fallback to rule-based detection for common patterns

### Storage

- Compress PDFs before storage
- Set lifecycle policies (delete after 90 days)
- Use S3 Intelligent-Tiering

### Compute

- Scale down during off-hours
- Use spot instances for non-critical workloads
- Cold start optimization for serverless

---

## Compliance & Auditing

### GDPR Compliance

- Log all data access
- Implement data deletion endpoints
- Maintain processing records (Art. 30)

### EU AI Act Compliance

- Generate system cards automatically
- Maintain audit logs for 6 months
- Implement human oversight gates

### Data Retention

```python
# Automated cleanup job
def cleanup_old_submissions():
    cutoff_date = datetime.now() - timedelta(days=90)
    db.execute("DELETE FROM Submission WHERE created_at < ?", (cutoff_date,))
    # Also delete associated files from storage
```

---

## Support & Maintenance

### Monitoring Checklist

- [ ] API response times < 500ms (p95)
- [ ] Error rate < 1%
- [ ] Database connections < 80% pool size
- [ ] Storage usage alerts at 80%
- [ ] Daily backup verification
- [ ] Security patch updates weekly

### Update Process

```bash
# 1. Backup
./scripts/backup.sh

# 2. Pull updates
git pull origin main

# 3. Update dependencies
pip install -r requirements.txt --upgrade

# 4. Run migrations
python migrate.py

# 5. Test
./test_endpoints.sh

# 6. Deploy
docker-compose up -d --build

# 7. Verify
curl http://localhost:8000/health
```

---

**For hackathon**: Use Option 1 (Local Development)  
**For production**: Use Option 2 (Docker Compose) or Option 3 (Kubernetes)

Questions? Check `README.md` or raise an issue.
