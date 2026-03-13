"""
Week 4: Security Hardening Module
Implements JWT authentication, encryption, rate limiting, input validation
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthCredential
import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
from functools import wraps
import time

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration"""
    
    def __init__(self):
        self.JWT_SECRET = secrets.token_urlsafe(32)
        self.JWT_ALGORITHM = "HS256"
        self.JWT_EXPIRATION_HOURS = 24
        self.ACCESS_CONTROL_MAX_REQUESTS = 100
        self.ACCESS_CONTROL_WINDOW_SECONDS = 60
        self.ENCRYPTION_KEY = secrets.token_bytes(32)  # For AES-256
    
    @classmethod
    def from_env(cls):
        """Load from environment variables"""
        import os
        config = cls()
        config.JWT_SECRET = os.getenv('JWT_SECRET', config.JWT_SECRET)
        config.ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', config.ENCRYPTION_KEY).encode()
        return config


class JWTAuthenticationManager:
    """JWT token generation and validation"""
    
    def __init__(self, secret: str, algorithm: str = "HS256", expiration_hours: int = 24):
        self.secret = secret
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours
    
    def create_token(self, user_id: str, clinician_id: Optional[str] = None,
                    scopes: Optional[list] = None) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'clinician_id': clinician_id,
            'scopes': scopes or [],
            'exp': datetime.utcnow() + timedelta(hours=self.expiration_hours),
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(16),  # JWT ID for logout/revocation
        }
        
        token = jwt.encode(payload, self.secret, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def is_token_revoked(self, jti: str, revocation_list: set) -> bool:
        """Check if token is revoked"""
        return jti in revocation_list


class EncryptionManager:
    """Symmetric encryption for sensitive data"""
    
    def __init__(self, key: bytes):
        from cryptography.fernet import Fernet
        # For production: use AES-256-GCM
        self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt sensitive string"""
        encrypted = self.cipher.encrypt(plaintext.encode())
        return encrypted.decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt sensitive string"""
        decrypted = self.cipher.decrypt(ciphertext.encode())
        return decrypted.decode()
    
    def hash_pii(self, pii: str, salt: Optional[str] = None) -> str:
        """Hash PII for audit logs"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        hashed = hashlib.sha256(f"{pii}{salt}".encode()).hexdigest()
        return f"{salt}${hashed}"
    
    def verify_pii_hash(self, actual_hash: str, pii: str) -> bool:
        """Verify PII hash"""
        salt, stored_hash = actual_hash.split('$')
        computed_hash = hashlib.sha256(f"{pii}{salt}".encode()).hexdigest()
        return stored_hash == computed_hash


class RateLimiter:
    """Token bucket rate limiting"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {client_id: [(timestamp, count)]}
    
    def is_rate_limited(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        now = time.time()
        window_start = now - self.window_seconds
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove old requests outside window
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        # Check if over limit
        if len(self.requests[client_id]) >= self.max_requests:
            return True
        
        # Add current request
        self.requests[client_id].append(now)
        return False
    
    def get_rate_limit_headers(self, client_id: str) -> Dict:
        """Get X-RateLimit headers for response"""
        now = time.time()
        window_start = now - self.window_seconds
        
        count = len([
            t for t in self.requests.get(client_id, [])
            if t > window_start
        ])
        
        return {
            'X-RateLimit-Limit': str(self.max_requests),
            'X-RateLimit-Remaining': str(max(0, self.max_requests - count)),
            'X-RateLimit-Reset': str(int(now + self.window_seconds)),
        }


class InputValidator:
    """Input validation and sanitization"""
    
    @staticmethod
    def validate_patient_id(patient_id: str) -> bool:
        """Validate anonymized patient ID format"""
        # Should be 64-char hex (SHA-256 hash)
        return len(patient_id) == 64 and all(c in '0123456789abcdef' for c in patient_id)
    
    @staticmethod
    def validate_dr_prediction(prediction: int) -> bool:
        """Validate DR classification (0-4)"""
        return 0 <= prediction <= 4
    
    @staticmethod
    def validate_refraction(sphere: float, cylinder: float, axis: float) -> bool:
        """Validate refraction values"""
        # Sphere: -20 to +20 D (diopters)
        # Cylinder: -10 to +10 D
        # Axis: 0 to 180 degrees
        return (-20 <= sphere <= 20 and 
                -10 <= cylinder <= 10 and
                0 <= axis <= 180)
    
    @staticmethod
    def validate_confidence_score(score: float) -> bool:
        """Validate confidence score (0-1)"""
        return 0.0 <= score <= 1.0
    
    @staticmethod
    def validate_likert_scale(value: int) -> bool:
        """Validate Likert scale (1-5)"""
        return 1 <= value <= 5


class SecurityMiddleware:
    """Security middleware for FastAPI"""
    
    def __init__(self, app: FastAPI, auth_manager: JWTAuthenticationManager,
                 rate_limiter: RateLimiter):
        self.app = app
        self.auth_manager = auth_manager
        self.rate_limiter = rate_limiter
    
    async def __call__(self, request: Request, call_next):
        """Process request through security checks"""
        client_ip = request.client.host if request.client else "unknown"
        
        # Rate limiting
        if self.rate_limiter.is_rate_limited(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"}
            )
        
        # Verify JWT for protected endpoints
        if self._is_protected_route(request.url.path):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Missing or invalid authorization header"}
                )
            
            token = auth_header.split(" ")[1]
            try:
                payload = self.auth_manager.verify_token(token)
                request.state.user_id = payload['user_id']
                request.state.clinician_id = payload.get('clinician_id')
            except HTTPException as e:
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail}
                )
        
        # Add security headers
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Add rate limit headers
        rate_limit_headers = self.rate_limiter.get_rate_limit_headers(client_ip)
        for header, value in rate_limit_headers.items():
            response.headers[header] = value
        
        return response
    
    def _is_protected_route(self, path: str) -> bool:
        """Check if route requires authentication"""
        # Public endpoints
        public_routes = ['/health', '/login', '/api/auth/login', '/docs', '/openapi.json']
        return not any(path.startswith(route) for route in public_routes)


class AuditLogger:
    """Security audit logging"""
    
    def __init__(self, encryption_manager: EncryptionManager):
        self.encryption_manager = encryption_manager
        self.logger = logging.getLogger('audit')
    
    def log_access(self, user_id: str, clinician_id: Optional[str], 
                   action: str, resource: str, result: str = "success"):
        """Log access event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'clinician_id': clinician_id,
            'action': action,
            'resource': resource,
            'result': result,
        }
        
        self.logger.info(json.dumps(event))
    
    def log_security_event(self, event_type: str, details: str, 
                          severity: str = "warning"):
        """Log security event (unauthorized access, rate limit, etc.)"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details,
            'severity': severity,
        }
        
        if severity == "critical":
            self.logger.critical(json.dumps(event))
        elif severity == "warning":
            self.logger.warning(json.dumps(event))
        else:
            self.logger.info(json.dumps(event))


def create_secure_app(config: SecurityConfig) -> FastAPI:
    """Create FastAPI app with security middleware"""
    app = FastAPI(title="Refracto AI - Secure API")
    
    # Initialize security components
    auth_manager = JWTAuthenticationManager(
        secret=config.JWT_SECRET,
        expiration_hours=config.JWT_EXPIRATION_HOURS
    )
    rate_limiter = RateLimiter(
        max_requests=config.ACCESS_CONTROL_MAX_REQUESTS,
        window_seconds=config.ACCESS_CONTROL_WINDOW_SECONDS
    )
    encryption_manager = EncryptionManager(config.ENCRYPTION_KEY)
    audit_logger = AuditLogger(encryption_manager)
    
    # Add middleware
    security_middleware = SecurityMiddleware(app, auth_manager, rate_limiter)
    app.middleware("http")(security_middleware)
    
    # Store in app state for route handlers
    app.state.auth_manager = auth_manager
    app.state.encryption_manager = encryption_manager
    app.state.audit_logger = audit_logger
    app.state.input_validator = InputValidator()
    
    return app


import json
