# Week 4 Implementation Guide: Production Hardening & Deployment

**Objective**: Harden system for production, conduct security/performance testing, and deploy to staging.

**Timeline**: 7 days  
**Dependencies**: Week 1-3 complete (modules + tests + validation)  
**Deliverables**: Production-ready system + staging deployment + audit-ready documentation

---

## Production Hardening Checklist

### Security Requirements

- [ ] Secrets management (no hardcoded credentials)
- [ ] HTTPS/TLS enforcement
- [ ] API authentication (JWT/OAuth2)
- [ ] Database encryption
- [ ] Docker image security
- [ ] Input validation + Rate limiting
- [ ] AUDIT/COMPLIANCE logging (immutable)
- [ ] Data residency compliance

### Performance Requirements

- [ ] Model inference < 500ms
- [ ] API p99 latency < 1s
- [ ] Throughput: 100+ concurrent requests
- [ ] Database query optimization
- [ ] Cache layer (Redis)
- [ ] Load balancing

### Infrastructure Requirements

- [ ] Kubernetes manifests
- [ ] Auto-scaling configuration
- [ ] Health checks
- [ ] Monitoring/logging (ELK/Prometheus)
- [ ] CI/CD pipeline
- [ ] Backup/disaster recovery

---

## Week 4 Monday: Security Hardening

### Task 4.1: Implement Secrets Management

**Option A: Environment Variables (Dev/Staging)**

```bash
# File: backend/.env.production
DATABASE_URL=postgresql://user:password@db-prod:5432/refracto_ai
MINIO_ACCESS_KEY=${MINIO_KEY}  # Set at deployment time
MINIO_SECRET_KEY=${MINIO_SECRET}
JWT_SECRET=${JWT_SECRET_PROD}
REDIS_URL=redis://redis-prod:6379
```

**Option B: HashiCorp Vault (Enterprise)**

```python
# File: backend/services/ml_service/vault_secrets.py
from hvac import Client

class VaultSecretManager:
    def __init__(self, vault_addr: str, role_id: str, secret_id: str):
        self.client = Client(url=vault_addr)
        # AppRole authentication
        self.client.auth.approle.login(role_id, secret_id)
    
    def get_secret(self, path: str, key: str):
        """Retrieve secret from Vault"""
        secret = self.client.secrets.kv.read_secret_version(path)
        return secret['data']['data'][key]
    
    def get_all_production_secrets(self):
        """Load all required secrets"""
        return {
            'db_password': self.get_secret('secret/data/prod/db', 'password'),
            'minio_key': self.get_secret('secret/data/prod/minio', 'access_key'),
            'jwt_secret': self.get_secret('secret/data/prod/api', 'jwt_secret'),
            'redis_password': self.get_secret('secret/data/prod/redis', 'password')
        }

# Usage in main.py
if ENVIRONMENT == 'production':
    vault = VaultSecretManager(
        vault_addr='https://vault.company.com',
        role_id=os.getenv('VAULT_ROLE_ID'),
        secret_id=os.getenv('VAULT_SECRET_ID')
    )
    secrets = vault.get_all_production_secrets()
```

### Task 4.2: Implement API Authentication (JWT)

```python
# File: backend/services/auth_service/jwt_handler.py
from datetime import datetime, timedelta
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

class JWTHandler:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.security = HTTPBearer()
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        """Generate JWT token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def verify_token(self, token: str):
        """Verify and decode JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            clinician_id: str = payload.get("sub")
            if clinician_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return {"clinician_id": clinician_id, "role": payload.get("role")}
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    async def get_current_user(self, credentials: HTTPAuthCredentials = Depends(self.security)):
        """Dependency for FastAPI routes"""
        return self.verify_token(credentials.credentials)

# Usage in routes
@app.post("/api/ml/expert-review/submit")
async def submit_expert_review(
    review: ExpertReviewSubmission,
    current_user = Depends(jwt_handler.get_current_user)
):
    """Only authenticated clinicians can submit reviews"""
    clinician_id = current_user['clinician_id']
    # ... process review
```

### Task 4.3: Database Encryption + Connection Security

```python
# File: backend/services/auth_service/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import ssl

def create_production_db_engine(db_url: str):
    """Create database engine with SSL and connection pooling"""
    
    # SSL context for production
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    engine = create_engine(
        db_url,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,  # Test connections before use
        connect_args={
            'connect_timeout': 10,
            'sslmode': 'require',
            'ssl_context': ssl_context  # PostgreSQL SSL
        },
        echo=False  # Disable SQL logging in production
    )
    
    return engine

# Database encryption at rest: Enable in PostgreSQL
# ALTER DATABASE refracto_ai WITH pgcrypto;
# CREATE EXTENSION IF NOT EXISTS pgcrypto;

# For sensitive columns:
class PredictionAuditLog(Base):
    __tablename__ = 'prediction_audit_log'
    
    log_id = Column(String, primary_key=True)
    # Encrypt sensitive columns
    anonymized_patient_hash = Column(
        String,
        # Encrypted via AES-256 in PostgreSQL
    )
    prediction = Column(String)  # Could be encrypted if extra paranoid
```

### Task 4.4: Input Validation + Rate Limiting

```python
# File: backend/services/ml_service/security.py
from fastapi import Request, HTTPException
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.util import get_remote_address
from fastapi_limiter.depends import RateLimiter
from redis.asyncio import from_url
from pydantic import BaseModel, validator

class MedicalImageInput(BaseModel):
    """Input validation with constraints"""
    
    fundus_image_path: str
    oct_image_path: str
    
    @validator('fundus_image_path')
    def validate_fundus_path(cls, v):
        if not v.endswith(('.png', '.jpg', '.jpeg', '.dicom')):
            raise ValueError('Invalid fundus image format')
        if len(v) > 255:
            raise ValueError('Path too long')
        return v
    
    @validator('oct_image_path')
    def validate_oct_path(cls, v):
        if not v.endswith(('.png', '.jpg', '.jpeg', '.dicom')):
            raise ValueError('Invalid OCT image format')
        if len(v) > 255:
            raise ValueError('Path too long')
        return v

# Initialize rate limiting
async def init_rate_limiter(redis_url: str):
    """Setup rate limiter with Redis backend"""
    redis = await from_url(redis_url)
    await FastAPILimiter.init(redis)

# Apply to endpoints
@app.post("/api/ml/analyze/mtl")
@limiter.limit("100/minute")  # 100 requests per minute per IP
async def analyze_images(
    request: Request,
    inputs: MedicalImageInput,
    current_user = Depends(jwt_handler.get_current_user)
):
    """Rate-limited ML analysis endpoint"""
    # Rate limiter checked automatically by FastAPI
    pass
```

### Task 4.5: Docker Image Security Scanning

```dockerfile
# File: backend/services/ml_service/Dockerfile.production
FROM python:3.11-slim-bookworm AS base

# Security: Run as non-root user
RUN groupadd -r refracto && useradd -r -g refracto refracto

FROM base AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM base

WORKDIR /app

# Copy only necessary artifacts
COPY --from=builder /root/.local /home/refracto/.local
COPY --chown=refracto:refracto . .

# Non-root user
USER refracto

ENV PATH=/home/refracto/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')"

# Security: Read-only filesystem
VOLUME ["/tmp", "/app/data"]

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Security scanning**:
```bash
# Scan Docker image for vulnerabilities
docker scan ml-service:1.0.0
trivy image ml-service:1.0.0

# Expected: Zero critical vulnerabilities
```

---

## Week 4 Tuesday-Wednesday: Performance Optimization

### Task 4.6: Model Inference Optimization

```python
# File: backend/services/ml_service/inference_optimization.py
import torch
from torchvision import models
import onnx
import onnxruntime as rt

class OptimizedMLInference:
    """Production-optimized model inference"""
    
    def __init__(self, model_path: str, device: str = 'cuda'):
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.model = self._load_optimized_model(model_path)
        self.onnx_session = None
    
    def _load_optimized_model(self, model_path: str):
        """Load model with optimizations"""
        model = torch.load(model_path, map_location=self.device)
        
        # Enable inference optimizations
        model.eval()
        
        # TorchScript compilation for faster inference
        if not hasattr(model, 'forward_traced'):
            model.forward_traced = torch.jit.trace(model, example_input)
            torch.jit.save(model.forward_traced, f"{model_path}.traced")
        
        return model
    
    def infer_with_caching(self, fundus_tensor, oct_tensor, cache_key: str):
        """Inference with result caching"""
        import redis
        
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Check cache
        cached_result = r.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        # Compute
        with torch.no_grad():
            results = self.model(fundus_tensor.to(self.device), oct_tensor.to(self.device))
        
        # Cache for 1 hour
        r.setex(cache_key, 3600, json.dumps(results))
        
        return results
    
    def convert_to_onnx(self, model_path: str):
        """Convert PyTorch to ONNX for faster inference"""
        model = torch.load(model_path)
        
        dummy_fundus = torch.randn(1, 3, 224, 224)
        dummy_oct = torch.randn(1, 3, 224, 224)
        
        torch.onnx.export(
            model,
            (dummy_fundus, dummy_oct),
            f"{model_path}.onnx",
            export_params=True,
            opset_version=13,
            do_constant_folding=True,
            input_names=['fundus', 'oct'],
            output_names=['dr', 'glaucoma', 'refraction']
        )
    
    def infer_onnx(self, fundus_array, oct_array):
        """ONNX inference (30-40% faster)"""
        if self.onnx_session is None:
            self.onnx_session = rt.InferenceSession("model.onnx")
        
        inputs = {
            'fundus': fundus_array,
            'oct': oct_array
        }
        
        outputs = self.onnx_session.run(None, inputs)
        
        return outputs
```

**Performance targets**:
- Inference < 500ms (PyTorch)
- Inference < 300ms (ONNX)
- Total request latency < 1s (including I/O)

### Task 4.7: Database Query Optimization

```python
# File: backend/services/ml_service/database_optimization.py
from sqlalchemy import Index, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Create strategic indexes
class OptimizedQueries:
    @staticmethod
    def create_indexes(engine):
        """Create production indexes"""
        
        # Frequently queried fields
        Index('idx_patient_hash', LocalPatientRecord.anonymized_patient_id).create(engine)
        Index('idx_log_patient', PredictionAuditLog.anonymized_patient_hash).create(engine)
        Index('idx_log_task', PredictionAuditLog.task).create(engine)
        Index('idx_review_patient', ExpertReview.patient_hash).create(engine)
        Index('idx_ccr_status', CCRMetrics.h3_hypothesis_status).create(engine)
        
        # Composite indexes for common queries
        Index('idx_patient_task', 
              PredictionAuditLog.anonymized_patient_hash,
              PredictionAuditLog.task
        ).create(engine)
    
    @staticmethod
    def get_optimized_session(db_url: str):
        """Session with connection pooling"""
        engine = create_engine(
            db_url,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,
            echo=False
        )
        return sessionmaker(bind=engine)
    
    @staticmethod
    def query_patient_ccr(session, patient_id: str):
        """Optimized: Fetch CCR for single patient"""
        from sqlalchemy import select
        
        query = select(ExpertReview).where(
            ExpertReview.patient_hash == patient_id
        ).limit(100)  # Pagination
        
        return session.execute(query).scalars()
```

### Task 4.8: Redis Caching Layer

```python
# File: backend/shared/redis_cache.py
import redis
from functools import wraps
import json
from datetime import timedelta

class RedisCache:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True
        )
    
    def cache_result(self, expiration: timedelta = timedelta(hours=1)):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function name + arguments
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # Try cache
                cached = self.client.get(cache_key)
                if cached:
                    return json.loads(cached)
                
                # Compute
                result = func(*args, **kwargs)
                
                # Store in cache
                self.client.setex(
                    cache_key,
                    int(expiration.total_seconds()),
                    json.dumps(result)
                )
                
                return result
            return wrapper
        return decorator
    
    def invalidate_cache(self, pattern: str):
        """Clear cache entries matching pattern"""
        for key in self.client.scan_iter(match=pattern):
            self.client.delete(key)

# Usage
redis_cache = RedisCache()

@redis_cache.cache_result(expiration=timedelta(hours=1))
def get_ccr_metrics():
    """CCR calculation (expensive, cache for 1 hour)"""
    return calculate_global_ccr()

# Invalidate on new review
def submit_expert_review(review):
    # ... process review
    redis_cache.invalidate_cache('ccr:*')  # Clear CCR cache
```

---

## Week 4 Thursday: Kubernetes Deployment

### Task 4.9: Create Kubernetes Manifests

```yaml
# File: backend/k8s/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-service
  namespace: refracto-ai
spec:
  replicas: 3  # High availability
  selector:
    matchLabels:
      app: ml-service
  template:
    metadata:
      labels:
        app: ml-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8001"
    spec:
      serviceAccountName: ml-service
      
      # Security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsReadOnlyRootFilesystem: true
      
      containers:
      - name: ml-service
        image: ml-service:1.0.0
        imagePullPolicy: IfNotPresent
        
        ports:
        - containerPort: 8001
          name: http
        
        # Environment variables from secrets
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ml-secrets
              key: db-url
        - name: MINIO_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: ml-secrets
              key: minio-key
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: ml-secrets
              key: jwt-secret
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: ml-config
              key: redis-url
        
        # Resource requests/limits
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
            gpu: "1"  # Requires GPU node
          limits:
            cpu: "4"
            memory: "8Gi"
            gpu: "1"
        
        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 5
        
        # Security
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        
        # Volumes
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/cache
      
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: ml-service
  namespace: refracto-ai
spec:
  type: ClusterIP
  ports:
  - port: 8001
    targetPort: 8001
    protocol: TCP
    name: http
  selector:
    app: ml-service

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ml-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Task 4.10: Deploy to Staging

```bash
# 1. Build Docker image
docker build -t ml-service:1.0.0 \
  -f backend/services/ml_service/Dockerfile.production \
  backend/services/ml_service/

# 2. Push to registry
docker push registry.company.com/ml-service:1.0.0

# 3. Create namespace
kubectl create namespace refracto-ai-staging

# 4. Create secrets
kubectl create secret generic ml-secrets \
  --from-literal=db-url=$DATABASE_URL_STAGING \
  --from-literal=minio-key=$MINIO_KEY_STAGING \
  --from-literal=jwt-secret=$(openssl rand -hex 32) \
  -n refracto-ai-staging

# 5. Create configmap
kubectl create configmap ml-config \
  --from-literal=redis-url=redis://redis-staging:6379 \
  -n refracto-ai-staging

# 6. Deploy
kubectl apply -f backend/k8s/deployment.yml -n refracto-ai-staging

# 7. Wait for rollout
kubectl rollout status deployment/ml-service -n refracto-ai-staging

# 8. Port forward for testing
kubectl port-forward -n refracto-ai-staging svc/ml-service 8001:8001
```

---

## Week 4 Friday: Monitoring, Load Testing, & Handoff

### Task 4.11: Setup Monitoring (Prometheus + Grafana)

```yaml
# File: backend/k8s/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ml-service'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - refracto-ai-staging
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true

# Deploy Prometheus
kubectl apply -f backend/k8s/prometheus-deployment.yml -n refracto-ai-staging
```

**Key metrics to monitor**:
- Inference latency (p50, p95, p99)
- Request throughput (req/sec)
- Error rate (5xx, 4xx)
- GPU utilization
- Memory usage
- Model cache hit ratio

### Task 4.12: Load Testing

```bash
# Install Apache JMeter or use k6
npm install -g k6

# File: backend/k8s/load-test.js
import http from 'k6/http';
import { check, sleep, group } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp-up
    { duration: '5m', target: 100 },  // Stay at 100
    { duration: '2m', target: 0 },    // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],  // 1s p95, 2s p99
    http_req_failed: ['rate<0.1'],  // <10% error rate
  },
};

export default function () {
  group('Analyze Images', function () {
    let res = http.post('http://localhost:8001/api/ml/analyze/mtl', {
      fundus_image: 'test_fundus.jpg',
      oct_image: 'test_oct.jpg',
    }, {
      headers: {
        'Authorization': 'Bearer ' + __ENV.JWT_TOKEN,
      },
    });
    
    check(res, {
      'status is 200': (r) => r.status === 200,
      'inference < 500ms': (r) => r.timings.duration < 500,
    });
  });
  
  sleep(1);
}

# Run load test
k6 run backend/k8s/load-test.js --vus 100 --duration 10m
```

**Expected results**:
- p50 < 200ms
- p95 < 1s
- p99 < 2s
- Error rate < 1%
- Throughput > 100 req/sec

### Task 4.13: Documentation & Handoff

**Create runbooks**:

```markdown
# File: docs/RUNBOOKS.md

## Deployment Runbook

### Pre-deployment checks
- [ ] All tests passing (100%)
- [ ] Security scan: zero critical vulnerabilities
- [ ] Load test: meets performance targets
- [ ] H1/H2/H3 validation: all PASS

### Deployment steps
1. Build Docker image
2. Push to registry
3. Update Kubernetes manifests
4. Apply to staging
5. Run smoke tests
6. Monitor metrics (30 mins)
7. Promote to production

## Incident Response

### Service Down
1. Check pod status: `kubectl get pods -n refracto-ai-staging`
2. View logs: `kubectl logs deployment/ml-service -n refracto-ai-staging`
3. Restart: `kubectl rollout restart deployment/ml-service`

### High Latency
1. Check GPU utilization: `nvidia-smi`
2. Increase replicas: `kubectl scale deployment ml-service --replicas=5`
3. Check database connections

### Data Breach Alert
1. Audit all logs: `SELECT * FROM prediction_audit_log WHERE timestamp > NOW() - INTERVAL 1 HOUR`
2. Check PII exposure: `grep -r 'patient_id\|phone\|email' logs/`
3. Trigger incident response protocol
```

---

## Week 4 Deliverables Checklist

### Security
- [ ] Secrets management configured (Vault/env vars)
- [ ] JWT authentication implemented
- [ ] Database encryption enabled
- [ ] API rate limiting active
- [ ] Docker image security scan: PASS (zero critical)
- [ ] Input validation on all endpoints

### Performance
- [ ] Model inference optimized (< 500ms)
- [ ] ONNX inference available (< 300ms)
- [ ] Database queries optimized
- [ ] Redis caching layer integrated
- [ ] Load test passing (>100 req/sec, p99<2s)

### Infrastructure
- [ ] Kubernetes manifests created
- [ ] Auto-scaling configured (min 3, max 10)
- [ ] Health checks implemented
- [ ] Prometheus monitoring setup
- [ ] Staging deployment successful

### Compliance
- [ ] Immutable audit logs verified
- [ ] HIPAA compliance checklist
- [ ] Data residency verified (local data only)
- [ ] Backup/disaster recovery plan

### Documentation
- [ ] Deployment runbook
- [ ] Incident response procedures
- [ ] API documentation (Swagger)
- [ ] Architecture diagram
- [ ] Secrets management guide

---

## Production Deployment Checklist (Final)

| Item | Status | Notes |
|------|--------|-------|
| Code Review | ⏳ | All PRs approved |
| Security Audit | ⏳ | OWASP Top 10 verified |
| Penetration Testing | ⏳ | Third-party audit |
| Performance Baseline | ⏳ | Load test complete |
| H1/H2/H3 Validation | ⏳ | All pass criteria met |
| Disaster Recovery Test | ⏳ | RTO < 1 hour |
| Staff Training | ⏳ | Ops team ready |
| Legal/Compliance Sign-off | ⏳ | HIPAA, local law compliance |
| Go-live Approval | ⏳ | Stakeholders approved |

---

## Post-Deployment (Week 5+)

### Ongoing Responsibilities

1. **Daily**:
   - Monitor alerts (Prometheus)
   - Check error rates
   - Verify backup completion

2. **Weekly**:
   - Review inference latency trends
   - Check model accuracy drift
   - Audit access logs

3. **Monthly**:
   - Re-validate H1/H2/H3 on new data
   - Security patches
   - Performance optimization review

4. **Quarterly**:
   - Full security audit
   - Disaster recovery drill
   - Capacity planning

---

## Success Metrics (Week 4 Complete)

| Metric | Target | Pass |
|--------|--------|------|
| Security Score (OWASP) | A+ | ⏳ |
| Inference Latency (p99) | < 2s | ⏳ |
| Availability | ≥99.5% | ⏳ |
| Error Rate | <1% | ⏳ |
| Hypothesis Validation (H1/H2/H3) | 100% PASS | ⏳ |
| Code Coverage | ≥80% | ⏳ |
| Deployment Downtime | <5 mins | ⏳ |

---

**🎉 End of 4-Week Implementation Sprint**

All Phase 1 features complete and production-ready!

---

## Appendix: Troubleshooting Production Issues

### Issue: Model inference timeout (>5s)
```bash
# Check GPU availability
nvidia-smi

# Profile inference
python -m cProfile -s cumulative inference.py

# Increase pod resource limits
kubectl set resources deployment ml-service --limits=cpu=4,memory=8Gi -n refracto-ai-staging
```

### Issue: Database connection pool exhausted
```sql
-- Check active connections
SELECT count(*) as total_active_connections
FROM pg_stat_activity
WHERE state = 'active';

-- Kill idle connections (if needed)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle' AND query_start < now() - interval '30 minutes';
```

### Issue: High memory usage
```bash
# Check Python memory
python -m memory_profiler inference.py

# Check Redis size
redis-cli INFO memory

# Clear old cache entries
redis-cli FLUSHDB
```

---

