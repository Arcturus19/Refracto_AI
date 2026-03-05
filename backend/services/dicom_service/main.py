from pynetdicom import AE, evt, AllStoragePresentationContexts
from pynetdicom.sop_class import Verification
from pydicom import dcmread
import os
import logging
from datetime import datetime
from pathlib import Path
import requests
from config import (
    DICOM_AE_TITLE, DICOM_PORT, DICOM_HOST, TEMP_STORAGE_DIR,
    PATIENT_SERVICE_URL, IMAGING_SERVICE_URL,
    AUTO_INGEST, AUTO_CREATE_PATIENTS, DELETE_AFTER_UPLOAD,
    DEFAULT_DOB, DEFAULT_GENDER
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create temp storage directory
os.makedirs(TEMP_STORAGE_DIR, exist_ok=True)


def find_or_create_patient(patient_id: str, patient_name: str) -> str:
    """
    Find existing patient or create new one
    
    Args:
        patient_id: DICOM Patient ID
        patient_name: DICOM Patient Name
        
    Returns:
        Patient UUID from patient service
    """
    try:
        # Step A1: Search for existing patient
        logger.info(f"🔍 Searching for patient: {patient_id}")
        search_url = f"{PATIENT_SERVICE_URL}/patients"
        params = {"search": patient_id}
        
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        
        patients = response.json()
        
        if patients and len(patients) > 0:
            # Patient found
            patient_uuid = patients[0]['id']
            logger.info(f"✓ Found existing patient: {patient_uuid}")
            return patient_uuid
        
        # Step A2: Create new patient
        if AUTO_CREATE_PATIENTS:
            logger.info(f"📝 Creating new patient: {patient_name} ({patient_id})")
            
            create_url = f"{PATIENT_SERVICE_URL}/patients"
            patient_data = {
                "full_name": patient_name.replace("^", " ").strip(),
                "dob": DEFAULT_DOB,
                "gender": DEFAULT_GENDER,
                "diabetes_status": False,
                "external_id": patient_id  # Store DICOM ID
            }
            
            response = requests.post(create_url, json=patient_data, timeout=10)
            response.raise_for_status()
            
            patient_uuid = response.json()['id']
            logger.info(f"✓ Created new patient: {patient_uuid}")
            return patient_uuid
        else:
            logger.warning(f"⚠️  Patient not found and auto-create disabled")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error finding/creating patient: {str(e)}")
        return None


def upload_to_imaging_service(patient_uuid: str, filepath: str, modality: str) -> bool:
    """
    Upload DICOM file to imaging service
    
    Args:
        patient_uuid: Patient UUID
        filepath: Path to DICOM file
        modality: Image modality
        
    Returns:
        True if successful
    """
    try:
        logger.info(f"📤 Uploading to imaging service: {patient_uuid}")
        
        # Map DICOM modality to imaging service type
        image_type = "FUNDUS" if modality in ["OP", "OPT"] else "OCT"
        
        upload_url = f"{IMAGING_SERVICE_URL}/upload/{patient_uuid}"
        
        # Read DICOM file
        with open(filepath, 'rb') as f:
            files = {'file': (os.path.basename(filepath), f, 'application/dicom')}
            data = {'image_type': image_type}
            
            response = requests.post(upload_url, files=files, data=data, timeout=30)
            response.raise_for_status()
        
        logger.info(f"✓ Image uploaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error uploading to imaging service: {str(e)}")
        return False


def handle_store(event):
    """
    Handle incoming DICOM C-STORE requests with auto-ingestion
    
    This callback is triggered when a DICOM image is sent to our SCP
    
    Args:
        event: The DICOM association event containing the dataset
        
    Returns:
        0x0000 for success, 0xC000 for error (triggers camera retry)
    """
    filepath = None
    
    try:
        # Get the DICOM dataset from the event
        dataset = event.dataset
        
        # Convert to file meta information
        dataset.file_meta = event.file_meta
        
        # Extract patient information
        patient_id = getattr(dataset, 'PatientID', 'UNKNOWN')
        patient_name = str(getattr(dataset, 'PatientName', 'UNKNOWN'))
        modality = getattr(dataset, 'Modality', 'UNKNOWN')
        study_description = getattr(dataset, 'StudyDescription', 'N/A')
        
        # Extract additional metadata
        study_date = getattr(dataset, 'StudyDate', 'UNKNOWN')
        study_time = getattr(dataset, 'StudyTime', 'UNKNOWN')
        sop_instance_uid = getattr(dataset, 'SOPInstanceUID', 'UNKNOWN')
        
        # Generate filename based on metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{patient_id}_{modality}_{timestamp}_{sop_instance_uid[:8]}.dcm"
        filepath = os.path.join(TEMP_STORAGE_DIR, filename)
        
        # Save DICOM file temporarily
        dataset.save_as(filepath, write_like_original=False)
        
        # Log receipt
        logger.info("=" * 80)
        logger.info(f"📥 Received DICOM image for Patient: {patient_name} ({patient_id})")
        logger.info(f"   Modality: {modality}")
        logger.info(f"   Study: {study_description}")
        logger.info(f"   Date/Time: {study_date} {study_time}")
        logger.info(f"   Saved to: {filepath}")
        logger.info(f"   File size: {os.path.getsize(filepath)} bytes")
        
        # Auto-ingestion pipeline
        if AUTO_INGEST:
            logger.info("🔄 Starting auto-ingestion pipeline...")
            
            # Step A: Find or create patient
            patient_uuid = find_or_create_patient(patient_id, patient_name)
            
            if not patient_uuid:
                logger.error("❌ Failed to find/create patient - aborting ingestion")
                logger.info("=" * 80)
                return 0xC000  # Error - camera should retry
            
            # Step B: Upload to imaging service
            upload_success = upload_to_imaging_service(patient_uuid, filepath, modality)
            
            if not upload_success:
                logger.error("❌ Failed to upload to imaging service")
                logger.info("=" * 80)
                return 0xC000  # Error - camera should retry
            
            # Step C: Cleanup temporary file
            if DELETE_AFTER_UPLOAD:
                try:
                    os.remove(filepath)
                    logger.info(f"🗑️  Deleted temporary file: {filepath}")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to delete temp file: {str(e)}")
            
            logger.info("✅ Auto-ingestion complete!")
        
        logger.info("=" * 80)
        
        # Return success status (0x0000)
        return 0x0000
        
    except Exception as e:
        logger.error(f"❌ Error handling C-STORE request: {str(e)}")
        logger.info("=" * 80)
        
        # Clean up temp file on error
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        
        # Return failure status (camera will retry)
        return 0xC000


def handle_echo(event):
    """
    Handle DICOM C-ECHO (verification) requests
    Used to test connectivity to the DICOM SCP
    """
    logger.info("🔔 Received C-ECHO verification request")
    return 0x0000


def start_dicom_scp():
    """
    Start the DICOM Store SCP server
    Listens for incoming DICOM images from medical imaging devices
    """
    logger.info("=" * 80)
    logger.info("🏥 Starting Refracto AI DICOM Service")
    logger.info("=" * 80)
    logger.info(f"📡 AE Title: {DICOM_AE_TITLE}")
    logger.info(f"🌐 Listening on: {DICOM_HOST}:{DICOM_PORT}")
    logger.info(f"💾 Storage directory: {TEMP_STORAGE_DIR}")
    logger.info("=" * 80)
    
    # Create Application Entity
    ae = AE(ae_title=DICOM_AE_TITLE)
    
    # Add supported Storage SOP Classes (all medical imaging types)
    # This allows us to receive any type of medical image
    ae.supported_contexts = AllStoragePresentationContexts
    
    # Add Verification SOP Class for C-ECHO
    ae.add_supported_context(Verification)
    
    # Set up event handlers
    handlers = [
        (evt.EVT_C_STORE, handle_store),
        (evt.EVT_C_ECHO, handle_echo)
    ]
    
    # Start listening
    logger.info("✅ DICOM SCP is ready and listening...")
    logger.info("Waiting for incoming DICOM transmissions...")
    logger.info("")
    
    try:
        # This blocks and runs indefinitely
        ae.start_server(
            (DICOM_HOST, DICOM_PORT),
            block=True,
            evt_handlers=handlers
        )
    except KeyboardInterrupt:
        logger.info("\n⚠️  Shutting down DICOM service...")
    except Exception as e:
        logger.error(f"❌ Server error: {str(e)}")
    finally:
        logger.info("👋 DICOM service stopped")


def list_received_files():
    """List all received DICOM files"""
    files = list(Path(TEMP_STORAGE_DIR).glob("*.dcm"))
    logger.info(f"\n📋 Total DICOM files received: {len(files)}")
    for f in files:
        size_mb = f.stat().st_size / (1024 * 1024)
        logger.info(f"   - {f.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    # Optional: List any existing files
    if os.path.exists(TEMP_STORAGE_DIR):
        list_received_files()
    
    # Start the DICOM SCP server
    start_dicom_scp()
