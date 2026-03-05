"""
Configuration for DICOM Service
"""

import os
from dotenv import load_dotenv

load_dotenv()

# DICOM Configuration
DICOM_AE_TITLE = os.getenv("DICOM_AE_TITLE", "REFRACTO_AI")
DICOM_PORT = int(os.getenv("DICOM_PORT", "11112"))
DICOM_HOST = os.getenv("DICOM_HOST", "0.0.0.0")

# Storage
TEMP_STORAGE_DIR = os.getenv("TEMP_STORAGE_DIR", "/tmp/dicom_received")

# Service URLs (internal Docker network)
PATIENT_SERVICE_URL = os.getenv("PATIENT_SERVICE_URL", "http://patient_service:8000")
IMAGING_SERVICE_URL = os.getenv("IMAGING_SERVICE_URL", "http://imaging_service:8000")

# Feature Flags
AUTO_INGEST = os.getenv("AUTO_INGEST", "true").lower() == "true"
AUTO_CREATE_PATIENTS = os.getenv("AUTO_CREATE_PATIENTS", "true").lower() == "true"
DELETE_AFTER_UPLOAD = os.getenv("DELETE_AFTER_UPLOAD", "true").lower() == "true"

# Default patient data for auto-creation
DEFAULT_DOB = "1970-01-01"
DEFAULT_GENDER = "Unknown"
