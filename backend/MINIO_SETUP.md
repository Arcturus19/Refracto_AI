# MinIO Object Storage Setup Guide

## Overview

MinIO is an S3-compatible object storage service perfect for storing medical images, DICOM files, and scan results.

## Access Information

Once running, you can access:
- **MinIO API**: http://localhost:9000
- **MinIO Console UI**: http://localhost:9001

## Login Credentials

- **Username**: `admin`
- **Password**: `password123`

⚠️ **Change these credentials in production!**

## Quick Start

### 1. Start MinIO Service

```powershell
cd "c:\Users\VICTUS\Desktop\Refracto AI\Refracto-AI-Backend"
docker-compose up -d minio
```

### 2. Access the Console

Open your browser and go to: **http://localhost:9001**

Login with:
- Username: `admin`
- Password: `password123`

### 3. Create a Bucket

In the MinIO console:
1. Click "Buckets" in the left sidebar
2. Click "Create Bucket"
3. Name it `medical-images` or `patient-scans`
4. Click "Create Bucket"

## Using MinIO in Python

### Install the client

Already added to `requirements.txt`:
```
minio==7.2.3
```

### Example Usage

```python
from shared.minio_client import get_minio_client

# Get client instance
minio = get_minio_client()

# Ensure bucket exists
minio.ensure_bucket_exists("medical-images")

# Upload an image
minio.upload_file(
    bucket_name="medical-images",
    object_name="scans/patient_123/retina_scan.jpg",
    file_path="/path/to/scan.jpg",
    content_type="image/jpeg"
)

# Upload bytes (useful for API uploads)
image_bytes = request.files['scan'].read()
minio.upload_bytes(
    bucket_name="medical-images",
    object_name=f"scans/{patient_id}/{filename}",
    data=image_bytes,
    content_type="image/jpeg"
)

# Get a presigned URL (temporary access link)
url = minio.get_object_url(
    bucket_name="medical-images",
    object_name="scans/patient_123/retina_scan.jpg",
    expires_seconds=3600  # 1 hour
)
# Share this URL with frontend to display the image

# Download a file
minio.download_file(
    bucket_name="medical-images",
    object_name="scans/patient_123/retina_scan.jpg",
    file_path="/tmp/downloaded_scan.jpg"
)

# List all objects in bucket
objects = minio.list_objects(
    bucket_name="medical-images",
    prefix="scans/patient_123/"
)

# Delete an object
minio.delete_object(
    bucket_name="medical-images",
    object_name="scans/patient_123/old_scan.jpg"
)
```

## Bucket Structure Recommendation

Organize your medical images hierarchically:

```
medical-images/
├── scans/
│   ├── patient_<uuid>/
│   │   ├── retina_scan_2026_01_11.jpg
│   │   ├── retina_scan_2026_01_15.jpg
│   │   └── metadata.json
│   └── patient_<uuid>/
│       └── ...
├── reports/
│   ├── patient_<uuid>/
│   │   ├── analysis_report_2026_01_11.pdf
│   │   └── ...
└── thumbnails/
    └── patient_<uuid>/
        └── thumb_retina_scan_2026_01_11.jpg
```

## Integration with FastAPI

### Upload Endpoint Example

```python
from fastapi import FastAPI, UploadFile, File
from shared.minio_client import get_minio_client
import uuid

app = FastAPI()
minio = get_minio_client()

@app.post("/upload-scan/{patient_id}")
async def upload_scan(patient_id: str, file: UploadFile = File(...)):
    # Ensure bucket exists
    minio.ensure_bucket_exists("medical-images")
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1]
    object_name = f"scans/{patient_id}/{uuid.uuid4()}.{file_extension}"
    
    # Read file content
    content = await file.read()
    
    # Upload to MinIO
    success = minio.upload_bytes(
        bucket_name="medical-images",
        object_name=object_name,
        data=content,
        content_type=file.content_type
    )
    
    if success:
        # Generate accessible URL
        url = minio.get_object_url(
            bucket_name="medical-images",
            object_name=object_name,
            expires_seconds=86400  # 24 hours
        )
        
        return {
            "message": "Scan uploaded successfully",
            "object_name": object_name,
            "url": url
        }
    else:
        return {"error": "Upload failed"}, 500
```

### Retrieve Image URL

```python
@app.get("/scan/{patient_id}/{scan_id}")
async def get_scan_url(patient_id: str, scan_id: str):
    object_name = f"scans/{patient_id}/{scan_id}"
    
    url = minio.get_object_url(
        bucket_name="medical-images",
        object_name=object_name,
        expires_seconds=3600
    )
    
    if url:
        return {"url": url}
    else:
        return {"error": "Scan not found"}, 404
```

## Volume Mapping

MinIO data is stored in: `./minio_data`

This folder is:
- ✅ Mapped to `/data` inside the container
- ✅ Persistent across container restarts
- ✅ Excluded from git (in `.gitignore`)

## Health Check

MinIO includes a health check endpoint:
```
http://localhost:9000/minio/health/live
```

Docker Compose uses this to verify MinIO is healthy before starting dependent services.

## Environment Variables

Add to your `.env` file (optional, has defaults):

```env
# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=password123
MINIO_SECURE=false
```

## Common Use Cases

### 1. Store Patient Retinal Scans
```python
scan_path = f"scans/{patient_id}/retina_{datetime.now().isoformat()}.jpg"
minio.upload_file("medical-images", scan_path, local_file)
```

### 2. Store AI Analysis Results
```python
result_path = f"analyses/{patient_id}/{analysis_id}.json"
minio.upload_bytes("medical-images", result_path, json.dumps(results).encode())
```

### 3. Generate Shareable Links
```python
# 1-hour temporary link for viewing
url = minio.get_object_url("medical-images", scan_path, expires_seconds=3600)
# Send this URL to frontend
```

### 4. Batch Upload DICOM Files
```python
for dicom_file in dicom_files:
    minio.upload_file(
        "medical-images",
        f"dicom/{patient_id}/{dicom_file.name}",
        dicom_file.path,
        content_type="application/dicom"
    )
```

## Security Best Practices

### Production Configuration

1. **Change default credentials**:
   ```yaml
   environment:
     MINIO_ROOT_USER: ${MINIO_ROOT_USER}
     MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
   ```

2. **Enable HTTPS**:
   - Use nginx reverse proxy with SSL
   - Set `secure=True` in MinIO client

3. **Bucket Policies**:
   - Set private buckets
   - Use presigned URLs for access
   - Never make medical data public

4. **Access Keys**:
   - Create separate access keys for each service
   - Don't use root credentials in code
   - Rotate keys regularly

## Monitoring

View real-time metrics in the console:
- Storage usage
- Upload/download traffic
- API requests
- Bucket sizes

## Troubleshooting

### Container won't start
```powershell
# Check logs
docker logs refracto_minio

# Verify port availability
netstat -ano | findstr :9000
netstat -ano | findstr :9001
```

### Can't access console
1. Verify container is running: `docker ps`
2. Check if port 9001 is mapped correctly
3. Try http://localhost:9001 (not https)

### Upload fails
1. Check bucket exists
2. Verify credentials are correct
3. Check available disk space

## Next Steps

1. **Imaging Service**: Build a dedicated service for medical image processing
2. **Integration**: Connect upload endpoints to frontend
3. **Image Processing**: Add thumbnail generation, format conversion
4. **DICOM Support**: Integrate with medical imaging standards
5. **Backup**: Set up automated backup to cloud storage

---

**MinIO is now ready for storing medical images!** 🏥📸
