"""
Auth Service - FastAPI Application
Main entry point for the authentication microservice
"""

import json
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Import local modules
from config import settings
from database import engine, get_db, Base
from models import User, UserRole, UserSettings
from schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    LoginResponse,
    UserProfileUpdate,
    PasswordChangeRequest,
    UserSettingsPayload,
    MessageResponse,
)
from security import hash_password, verify_password, create_access_token
from dependencies import get_current_user, get_current_active_admin


failed_login_attempts: dict[str, list[float]] = {}


def _cors_origins() -> list[str]:
    return [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]


def _rate_limit_key(request: Request, email: str) -> str:
    client_host = request.client.host if request.client else "unknown"
    return f"{client_host}:{email.lower()}"


def _prune_attempts(key: str, now: float) -> list[float]:
    window_start = now - settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    attempts = [timestamp for timestamp in failed_login_attempts.get(key, []) if timestamp >= window_start]
    if attempts:
        failed_login_attempts[key] = attempts
    else:
        failed_login_attempts.pop(key, None)
    return attempts


def _record_failed_attempt(key: str) -> None:
    now = time.time()
    attempts = _prune_attempts(key, now)
    attempts.append(now)
    failed_login_attempts[key] = attempts


def _clear_failed_attempts(key: str) -> None:
    failed_login_attempts.pop(key, None)


def _set_access_cookie(response: Response, access_token: str) -> None:
    cookie_kwargs = {
        "key": settings.ACCESS_COOKIE_NAME,
        "value": access_token,
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "max_age": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "path": "/",
    }
    if settings.COOKIE_DOMAIN:
        cookie_kwargs["domain"] = settings.COOKIE_DOMAIN
    response.set_cookie(**cookie_kwargs)


# ============ Database Initialization ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown.
    Creates database tables on startup.
    """
    # Startup: Create tables
    print("🔧 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    yield
    
    # Shutdown: Clean up resources
    print("👋 Shutting down...")


# ============ FastAPI Application ============

app = FastAPI(
    title="Refracto AI - Auth Service",
    description="Authentication and Authorization Service for Refracto AI Medical Imaging Platform",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Root & Health Endpoints ============

@app.get("/")
async def root():
    """Root endpoint - Health check and welcome message"""
    return {
        "message": "Hello World from Refracto AI Auth Service! 🚀",
        "service": "auth_service",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "register": "/register",
            "login": "/login",
            "me": "/me"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "auth_service",
        "database": "connected"
    }


# ============ Authentication Endpoints ============

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 8 characters)
    - **full_name**: User's full name
    New self-service registrations are created as doctors.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please use a different email or login."
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        role=UserRole.DOCTOR
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/login", response_model=LoginResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT access token.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns user data and JWT access token.
    """
    key = _rate_limit_key(request, credentials.email)
    attempts = _prune_attempts(key, time.time())
    if len(attempts) >= settings.LOGIN_RATE_LIMIT_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later."
        )

    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    # Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.password_hash):
        _record_failed_attempt(key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _clear_failed_attempts(key)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role.value}
    )

    _set_access_cookie(response, access_token)
    
    return {
        "user": user,
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    """Clear the authentication cookie for the current session."""
    response.delete_cookie(
        key=settings.ACCESS_COOKIE_NAME,
        path="/",
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )
    return {"message": "Logged out successfully"}


# ============ Protected Endpoints ============

@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    
    **Requires authentication**: Include JWT token in Authorization header.
    """
    return current_user


@app.put("/me/profile", response_model=UserResponse)
async def update_current_user_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current authenticated user's profile.

    - **full_name**: Updated display name
    - **email**: Updated email (must remain unique)
    """
    existing_user = db.query(User).filter(User.email == payload.email, User.id != current_user.id).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered by another user"
        )

    current_user.full_name = payload.full_name
    current_user.email = payload.email
    db.commit()
    db.refresh(current_user)
    return current_user


@app.put("/me/password", response_model=MessageResponse)
async def change_current_user_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current authenticated user's password.

    - **current_password**: Existing password for verification
    - **new_password**: New password (minimum 8 chars)
    """
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@app.get("/me/settings", response_model=UserSettingsPayload)
async def get_current_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve current user's settings blob.
    """
    settings_row = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings_row:
        return {"settings": {}}

    try:
        data = json.loads(settings_row.settings_json or "{}")
    except json.JSONDecodeError:
        data = {}

    return {"settings": data}


@app.put("/me/settings", response_model=UserSettingsPayload)
async def update_current_user_settings(
    payload: UserSettingsPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save current user's settings blob.
    """
    settings_row = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()

    if not settings_row:
        settings_row = UserSettings(
            user_id=current_user.id,
            settings_json=json.dumps(payload.settings)
        )
        db.add(settings_row)
    else:
        settings_row.settings_json = json.dumps(payload.settings)

    db.commit()

    return {"settings": payload.settings}


@app.get("/admin/users", response_model=list[UserResponse])
async def get_all_users(
    current_user: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db)
):
    """
    Get all users (admin only).
    
    **Requires authentication**: Admin role required.
    """
    users = db.query(User).all()
    return users


# ============ Development Server ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

