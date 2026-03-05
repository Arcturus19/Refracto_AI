# Auth Service - API Documentation

## Overview

The Auth Service provides authentication and authorization for the Refracto AI platform using JWT tokens and bcrypt password hashing.

## Base URL

```
http://localhost:8001
```

## Endpoints

### Public Endpoints

#### 1. Root / Health Check
```http
GET /
```

**Response:**
```json
{
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
```

#### 2. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "auth_service",
  "database": "connected"
}
```

---

### Authentication Endpoints

#### 3. Register New User
```http
POST /register
```

**Request Body:**
```json
{
  "email": "doctor@example.com",
  "password": "securepassword123",
  "full_name": "Dr. John Doe",
  "role": "doctor"
}
```

**Fields:**
- `email` (required): Valid email address (must be unique)
- `password` (required): Minimum 8 characters
- `full_name` (required): User's full name
- `role` (optional): Either "doctor" or "admin" (defaults to "doctor")

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "doctor@example.com",
  "full_name": "Dr. John Doe",
  "role": "doctor",
  "created_at": "2026-01-11T21:10:00.000Z",
  "updated_at": "2026-01-11T21:10:00.000Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Email already registered. Please use a different email or login."
}
```

---

#### 4. Login
```http
POST /login
```

**Request Body:**
```json
{
  "email": "doctor@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "doctor@example.com",
    "full_name": "Dr. John Doe",
    "role": "doctor",
    "created_at": "2026-01-11T21:10:00.000Z",
    "updated_at": "2026-01-11T21:10:00.000Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Incorrect email or password"
}
```

---

### Protected Endpoints

> **Note**: All protected endpoints require a valid JWT token in the Authorization header:
> ```
> Authorization: Bearer <your_token_here>
> ```

#### 5. Get Current User
```http
GET /me
```

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "doctor@example.com",
  "full_name": "Dr. John Doe",
  "role": "doctor",
  "created_at": "2026-01-11T21:10:00.000Z",
  "updated_at": "2026-01-11T21:10:00.000Z"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Could not validate credentials"
}
```

---

#### 6. Get All Users (Admin Only)
```http
GET /admin/users
```

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "email": "doctor@example.com",
    "full_name": "Dr. John Doe",
    "role": "doctor",
    "created_at": "2026-01-11T21:10:00.000Z",
    "updated_at": "2026-01-11T21:10:00.000Z"
  },
  {
    "id": 2,
    "email": "admin@refracto.ai",
    "full_name": "Admin User",
    "role": "admin",
    "created_at": "2026-01-11T21:15:00.000Z",
    "updated_at": "2026-01-11T21:15:00.000Z"
  }
]
```

**Error Response (403 Forbidden):**
```json
{
  "detail": "Insufficient permissions. Admin access required."
}
```

---

## Testing with cURL

### 1. Register a new doctor
```bash
curl -X POST http://localhost:8001/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@example.com",
    "password": "securepass123",
    "full_name": "Dr. Jane Smith",
    "role": "doctor"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8001/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@example.com",
    "password": "securepass123"
  }'
```

Save the `access_token` from the response.

### 3. Access protected endpoint
```bash
curl http://localhost:8001/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

---

## Testing with PowerShell

### 1. Register a new doctor
```powershell
$body = @{
    email = "doctor@example.com"
    password = "securepass123"
    full_name = "Dr. Jane Smith"
    role = "doctor"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/register" -Method Post -Body $body -ContentType "application/json"
```

### 2. Login
```powershell
$loginBody = @{
    email = "doctor@example.com"
    password = "securepass123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8001/login" -Method Post -Body $loginBody -ContentType "application/json"
$token = $response.access_token
```

### 3. Access protected endpoint
```powershell
$headers = @{
    Authorization = "Bearer $token"
}

Invoke-RestMethod -Uri "http://localhost:8001/me" -Headers $headers
```

---

## Interactive API Documentation

Once the service is running, you can access interactive API documentation:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

The Swagger UI provides a user-friendly interface to test all endpoints directly in your browser.

---

## Database Schema

### Users Table

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | Primary Key, Auto Increment |
| email | String(255) | Unique, Not Null, Indexed |
| password_hash | String(255) | Not Null |
| full_name | String(255) | Not Null |
| role | Enum | 'admin' or 'doctor', Default: 'doctor' |
| created_at | DateTime | Not Null, Auto-generated |
| updated_at | DateTime | Not Null, Auto-updated |

---

## Security Features

1. **Password Hashing**: Uses bcrypt with automatic salt generation
2. **JWT Tokens**: HS256 algorithm with configurable expiration
3. **Token Validation**: Automatic validation on protected routes
4. **Role-Based Access**: Admin-only endpoints for sensitive operations
5. **Input Validation**: Pydantic schemas validate all request data

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created (registration successful) |
| 400 | Bad Request (validation error or duplicate email) |
| 401 | Unauthorized (invalid credentials or token) |
| 403 | Forbidden (insufficient permissions) |
| 422 | Unprocessable Entity (validation error) |
| 500 | Internal Server Error |
