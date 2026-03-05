# Patient Service - API Documentation

## Overview

The Patient Service manages patient records for the Refracto AI platform, providing CRUD operations with search and filtering capabilities.

## Base URL

```
http://localhost:8002
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
  "message": "Refracto AI - Patient Service 🏥",
  "service": "patient_service",
  "status": "running",
  "version": "1.0.0",
  "endpoints": {
    "docs": "/docs",
    "patients": "/patients",
    "create_patient": "/patients (POST)",
    "get_patient": "/patients/{id} (GET)"
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
  "service": "patient_service",
  "database": "connected"
}
```

---

### Patient Management Endpoints

#### 3. Create New Patient
```http
POST /patients
```

**Request Body:**
```json
{
  "full_name": "John Doe",
  "dob": "1980-05-15",
  "gender": "Male",
  "diabetes_status": false
}
```

**Fields:**
- `full_name` (required): Patient's full name (1-255 characters)
- `dob` (required): Date of birth in YYYY-MM-DD format
- `gender` (required): Gender (e.g., Male, Female, Other)
- `diabetes_status` (optional): Whether patient has diabetes (default: false)

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "John Doe",
  "dob": "1980-05-15",
  "gender": "Male",
  "diabetes_status": false,
  "created_at": "2026-01-11T21:15:00.000Z",
  "updated_at": "2026-01-11T21:15:00.000Z"
}
```

---

#### 4. List All Patients (with Search)
```http
GET /patients?search={name}&skip={offset}&limit={count}
```

**Query Parameters:**
- `search` (optional): Search by patient name (case-insensitive partial match)
- `skip` (optional): Number of records to skip for pagination (default: 0)
- `limit` (optional): Maximum number of records to return (max: 100, default: 100)

**Examples:**
```http
GET /patients                          # Get all patients
GET /patients?search=john              # Search for patients with "john" in name
GET /patients?skip=10&limit=20         # Get patients 11-30
GET /patients?search=smith&limit=5     # Search "smith", max 5 results
```

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "full_name": "John Doe",
    "dob": "1980-05-15",
    "gender": "Male",
    "diabetes_status": false,
    "created_at": "2026-01-11T21:15:00.000Z",
    "updated_at": "2026-01-11T21:15:00.000Z"
  },
  {
    "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "full_name": "Jane Smith",
    "dob": "1992-08-22",
    "gender": "Female",
    "diabetes_status": true,
    "created_at": "2026-01-11T21:16:00.000Z",
    "updated_at": "2026-01-11T21:16:00.000Z"
  }
]
```

---

#### 5. Get Single Patient
```http
GET /patients/{patient_id}
```

**Path Parameters:**
- `patient_id`: UUID of the patient

**Example:**
```http
GET /patients/550e8400-e29b-41d4-a716-446655440000
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "John Doe",
  "dob": "1980-05-15",
  "gender": "Male",
  "diabetes_status": false,
  "created_at": "2026-01-11T21:15:00.000Z",
  "updated_at": "2026-01-11T21:15:00.000Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Patient with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

---

#### 6. Update Patient
```http
PUT /patients/{patient_id}
```

**Path Parameters:**
- `patient_id`: UUID of the patient to update

**Request Body (all fields optional):**
```json
{
  "full_name": "John Michael Doe",
  "diabetes_status": true
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "full_name": "John Michael Doe",
  "dob": "1980-05-15",
  "gender": "Male",
  "diabetes_status": true,
  "created_at": "2026-01-11T21:15:00.000Z",
  "updated_at": "2026-01-11T21:18:00.000Z"
}
```

---

#### 7. Delete Patient
```http
DELETE /patients/{patient_id}
```

**Path Parameters:**
- `patient_id`: UUID of the patient to delete

**Response (204 No Content):**
No response body

**Error Response (404 Not Found):**
```json
{
  "detail": "Patient with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

---

#### 8. Get Patient Statistics
```http
GET /patients/stats/summary
```

**Response (200 OK):**
```json
{
  "total_patients": 150,
  "diabetes_patients": 45,
  "non_diabetes_patients": 105,
  "diabetes_percentage": 30.0
}
```

---

## Testing with PowerShell

### Create a New Patient

```powershell
$patientData = @{
    full_name = "Dr. Sarah Johnson"
    dob = "1985-03-20"
    gender = "Female"
    diabetes_status = $false
} | ConvertTo-Json

$newPatient = Invoke-RestMethod -Uri "http://localhost:8002/patients" `
    -Method Post `
    -Body $patientData `
    -ContentType "application/json"

Write-Host "Created patient with ID: $($newPatient.id)"
```

### List All Patients

```powershell
$patients = Invoke-RestMethod -Uri "http://localhost:8002/patients"
$patients | Format-Table id, full_name, dob, gender, diabetes_status
```

### Search Patients by Name

```powershell
$searchResults = Invoke-RestMethod -Uri "http://localhost:8002/patients?search=sarah"
$searchResults | Format-Table full_name, dob, gender
```

### Get Single Patient

```powershell
$patientId = "550e8400-e29b-41d4-a716-446655440000"
$patient = Invoke-RestMethod -Uri "http://localhost:8002/patients/$patientId"
Write-Host "Patient: $($patient.full_name), DOB: $($patient.dob)"
```

### Update Patient

```powershell
$updateData = @{
    diabetes_status = $true
} | ConvertTo-Json

$updated = Invoke-RestMethod -Uri "http://localhost:8002/patients/$patientId" `
    -Method Put `
    -Body $updateData `
    -ContentType "application/json"

Write-Host "Updated diabetes status to: $($updated.diabetes_status)"
```

### Delete Patient

```powershell
Invoke-RestMethod -Uri "http://localhost:8002/patients/$patientId" `
    -Method Delete

Write-Host "Patient deleted successfully"
```

### Get Statistics

```powershell
$stats = Invoke-RestMethod -Uri "http://localhost:8002/patients/stats/summary"
Write-Host "Total Patients: $($stats.total_patients)"
Write-Host "Diabetes Patients: $($stats.diabetes_patients) ($($stats.diabetes_percentage)%)"
```

---

## Testing with cURL

### Create Patient
```bash
curl -X POST http://localhost:8002/patients \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "dob": "1980-05-15",
    "gender": "Male",
    "diabetes_status": false
  }'
```

### List Patients
```bash
curl http://localhost:8002/patients
```

### Search Patients
```bash
curl "http://localhost:8002/patients?search=john"
```

### Get Single Patient
```bash
curl http://localhost:8002/patients/550e8400-e29b-41d4-a716-446655440000
```

### Update Patient
```bash
curl -X PUT http://localhost:8002/patients/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{"diabetes_status": true}'
```

### Delete Patient
```bash
curl -X DELETE http://localhost:8002/patients/550e8400-e29b-41d4-a716-446655440000
```

---

## Interactive API Documentation

Access interactive Swagger UI documentation:

- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

---

## Database Schema

### Patients Table

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | Primary Key, Auto-generated |
| full_name | String(255) | Not Null, Indexed |
| dob | Date | Not Null |
| gender | String(50) | Not Null |
| diabetes_status | Boolean | Not Null, Default: False |
| created_at | DateTime | Not Null, Auto-generated |
| updated_at | DateTime | Not Null, Auto-updated |

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created (patient created successfully) |
| 204 | No Content (patient deleted successfully) |
| 400 | Bad Request (validation error) |
| 404 | Not Found (patient not found) |
| 422 | Unprocessable Entity (validation error) |
| 500 | Internal Server Error |

---

## Features

- ✅ UUID-based patient IDs for security and scalability
- ✅ Full CRUD operations (Create, Read, Update, Delete)
- ✅ Case-insensitive patient name search
- ✅ Pagination support for large datasets
- ✅ Automatic timestamps (created_at, updated_at)
- ✅ Input validation with Pydantic
- ✅ Interactive API documentation
- ✅ Health check endpoint for monitoring
- ✅ Statistics endpoint for analytics
