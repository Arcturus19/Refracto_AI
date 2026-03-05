"""
Auth Service - FastAPI Application
Main entry point for the authentication microservice
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

# Import local modules
from database import engine, get_db, Base
from models import User, UserRole
from schemas import UserCreate, UserLogin, UserResponse, LoginResponse
from security import hash_password, verify_password, create_access_token
from dependencies import get_current_user, get_current_active_admin


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
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with specific origins in production
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
    - **role**: User role (admin or doctor, defaults to doctor)
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
        role=user_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/login", response_model=LoginResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT access token.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns user data and JWT access token.
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    # Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role.value}
    )
    
    return {
        "user": user,
        "access_token": access_token,
        "token_type": "bearer"
    }


# ============ Protected Endpoints ============

@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    
    **Requires authentication**: Include JWT token in Authorization header.
    """
    return current_user


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

