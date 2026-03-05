"""
Pydantic Schemas for Request/Response Validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from models import UserRole


# ============ Request Schemas ============

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.DOCTOR


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


# ============ Response Schemas ============

class UserResponse(BaseModel):
    """Schema for user data in responses (without password)"""
    id: int
    email: str
    full_name: str
    role: UserRole
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for data stored in JWT token"""
    email: Optional[str] = None
    user_id: Optional[int] = None


class LoginResponse(BaseModel):
    """Schema for login response with user data and token"""
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
