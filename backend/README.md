# Refracto AI Backend - Microservices Architecture

A modern microservices-based backend for the Refracto AI Medical Imaging Platform, built with FastAPI and PostgreSQL.

## 🏗️ Project Structure

```
backend/
├── services/
│   ├── auth_service/        # Authentication & Authorization
│   ├── patient_service/     # Patient Management (planned)
│   └── imaging_service/     # Medical Imaging Processing (planned)
├── shared/                  # Common schemas and utilities
├── docker-compose.yml       # Docker orchestration
├── .env                     # Environment variables (DO NOT COMMIT)
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop installed and running
- Docker Compose v3.8 or higher
- Git (optional, for version control)

### Step 1: Clone or Navigate to Project

```powershell
cd "c:\Users\VICTUS\Desktop\Refracto AI\backend"
```

### Step 2: Environment Setup

The `.env` file is already configured with default credentials:
- **PostgreSQL User**: `refracto_admin`
- **PostgreSQL Password**: `refracto_secure_password_2026`
- **Database Name**: `refracto_ai_db`
- **pgAdmin Email**: `admin@refracto.ai`
- **pgAdmin Password**: `admin_secure_pass_2026`

> ⚠️ **Security Note**: Change these credentials in production!

### Step 3: Start Docker Containers

```powershell
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### Step 4: Verify Services

Once the containers are running, verify the services:

| Service | URL | Description |
|---------|-----|-------------|
| **Auth Service** | http://localhost:8001 | FastAPI application |
| **Auth API Docs** | http://localhost:8001/docs | Swagger UI documentation |
| **PostgreSQL** | localhost:5432 | Database server |
| **pgAdmin** | http://localhost:5050 | Database management UI |

## 📡 Testing the Auth Service

### Using Browser
1. Open http://localhost:8001 - See "Hello World" message
2. Open http://localhost:8001/docs - Interactive API documentation
3. Open http://localhost:8001/health - Health check endpoint

### Using PowerShell
```powershell
# Test root endpoint
curl http://localhost:8001

# Test health check
curl http://localhost:8001/health

# Test auth status
curl http://localhost:8001/api/v1/auth/status
```

## 🗄️ Database Management with pgAdmin

1. Open pgAdmin: http://localhost:5050
2. Login with credentials from `.env`:
   - Email: `admin@refracto.ai`
   - Password: `admin_secure_pass_2026`
3. Add new server:
   - **Name**: Refracto AI DB
   - **Host**: `postgres` (container name)
   - **Port**: `5432`
   - **Username**: `refracto_admin`
   - **Password**: `refracto_secure_password_2026`
   - **Database**: `refracto_ai_db`

## 🛠️ Development Commands

### Docker Management
```powershell
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (⚠️ deletes database data)
docker-compose down -v

# Rebuild specific service
docker-compose build auth_service

# View logs for specific service
docker-compose logs -f auth_service

# Restart a service
docker-compose restart auth_service
```

### Service Development
```powershell
# Access auth service container
docker exec -it refracto_auth_service bash

# Run auth service locally (without Docker)
cd services/auth_service
pip install -r requirements.txt
python main.py
```

## 📦 Services Overview

### ✅ Auth Service (Active)
- **Status**: Operational
- **Port**: 8001
- **Framework**: FastAPI
- **Endpoints**:
  - `GET /` - Hello World
  - `GET /health` - Health check
  - `GET /api/v1/auth/status` - Service status

### 🚧 Patient Service (Planned)
- Patient registration and management
- Medical history tracking
- Patient data CRUD operations

### 🚧 Imaging Service (Planned)
- Medical image upload and storage
- AI-powered image analysis
- DICOM format support

## 🔧 Troubleshooting

### Port Already in Use
If you get a port conflict error:
```powershell
# Check what's using the port
netstat -ano | findstr :5432
netstat -ano | findstr :5050
netstat -ano | findstr :8001

# Stop the process or change ports in docker-compose.yml
```

### Container Won't Start
```powershell
# View detailed logs
docker-compose logs auth_service
docker-compose logs postgres

# Remove containers and try again
docker-compose down
docker-compose up -d --force-recreate
```

### Database Connection Issues
1. Ensure PostgreSQL is healthy: `docker-compose ps`
2. Wait for health check to pass (may take 10-30 seconds)
3. Check logs: `docker-compose logs postgres`

## 🏗️ Next Steps

1. **Add Database Models**: Create SQLAlchemy models in auth_service
2. **Implement Authentication**: Add JWT-based authentication
3. **Build Patient Service**: Create patient management microservice
4. **Add API Gateway**: Implement API gateway for routing
5. **Setup CI/CD**: Configure GitHub Actions or similar

## 📝 Environment Variables

Key environment variables (defined in `.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | Database username | `refracto_admin` |
| `POSTGRES_PASSWORD` | Database password | `refracto_secure_password_2026` |
| `POSTGRES_DB` | Database name | `refracto_ai_db` |
| `DATABASE_URL` | Full connection string | Auto-generated |
| `PGADMIN_DEFAULT_EMAIL` | pgAdmin login email | `admin@refracto.ai` |
| `PGADMIN_DEFAULT_PASSWORD` | pgAdmin password | `admin_secure_pass_2026` |

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and test locally
3. Commit changes: `git commit -m "Add new feature"`
4. Push to branch: `git push origin feature/new-feature`
5. Create pull request

## 📄 License

This project is part of the Refracto AI Medical Imaging Platform.

---

**Built with ❤️ using FastAPI, PostgreSQL, and Docker**
