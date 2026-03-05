# DICOM Service - Medical Image Receiver

## Overview

The DICOM Service acts as a **DICOM Store SCP** (Service Class Provider) - a receiver for medical images sent from imaging devices like:
- Fundus cameras
- OCT scanners  
- Retinal imaging systems
- Any DICOM-compliant medical imaging device

## Configuration

- **AE Title**: `REFRACTO_AI`
- **Port**: `11112`
- **Protocol**: DICOM C-STORE
- **Storage**: `/tmp/dicom_received` (mapped to `./dicom_received`)

## Features

✅ Accepts all DICOM Storage SOP Classes  
✅ Handles C-ECHO verification requests  
✅ Extracts patient metadata (ID, Name, Modality)  
✅ Saves received DICOM files  
✅ Detailed logging of all transmissions  
✅ Supports all Transfer Syntaxes

## Starting the Service

### With Docker Compose

```bash
cd "c:\Users\VICTUS\Desktop\Refracto AI\Refracto-AI-Backend"
docker-compose up -d dicom_service
```

### Standalone

```bash
cd services/dicom_service
pip install -r requirements.txt
python main.py
```

## Testing the DICOM SCP

### 1. Test with C-ECHO (Verification)

```bash
# Using DCMTK echoscu
echoscu localhost 11112 -aet SENDING_AE -aec REFRACTO_AI

# Using pynetdicom
python -m pynetdicom echoscu localhost 11112 -aet SENDING_AE -aec REFRACTO_AI
```

**Expected output:**
```
🔔 Received C-ECHO verification request
```

### 2. Send a Test DICOM Image

```bash
# Using DCMTK storescu
storescu localhost 11112 -aet FUNDUS_CAMERA -aec REFRACTO_AI test_image.dcm

# Using pynetdicom
python -m pynetdicom storescu localhost 11112 -aet FUNDUS_CAMERA -aec REFRACTO_AI test_image.dcm
```

**Expected output:**
```
================================================================================
📥 Received DICOM image for Patient: John Doe (12345)
   Modality: OP (Ophthalmic Photography)
   Study: Fundus Imaging
   Date/Time: 20260111 143022
   Saved to: /tmp/dicom_received/12345_OP_20260111_143530_1a2b3c4d.dcm
   File size: 2458624 bytes
================================================================================
```

## Configuring Medical Devices

### General DICOM Settings

Most fundus cameras and OCT devices have a DICOM export/send configuration:

1. **Find DICOM settings** in device menu
2. **Add new destination:**
   - **AE Title**: `REFRACTO_AI`
   - **Hostname/IP**: `<server-ip>` (e.g., `192.168.1.100`)
   - **Port**: `11112`
   - **Calling AE Title**: Device-specific (e.g., `FUNDUS_01`)

### Device-Specific Examples

**Topcon Fundus Camera:**
- Menu → Network → DICOM → Destinations
- Add: Refracto AI / 192.168.1.100:11112

**Zeiss OCT Scanner:**
- Settings → Export → DICOM Node
- Configure: REFRACTO_AI@192.168.1.100:11112

**Heidelberg Engineering:**
- Administration → DICOM → Store SCP
- Add Receiver: IP, Port, AE Title

## Supported Modalities

The service accepts **all DICOM storage types**, including:

- **OP** - Ophthalmic Photography (Fundus)
- **OPT** - Ophthalmic Tomography (OCT)
- **OPV** - Ophthalmic Visual Field
- **CT** - Computed Tomography
- **MR** - Magnetic Resonance
- **US** - Ultrasound
- And many more...

## Metadata Extracted

From each received DICOM file:

```python
{
    "PatientID": "12345",
    "PatientName": "Doe^John",
    "Modality": "OP",
    "StudyDescription": "Fundus Imaging",
    "StudyDate": "20260111",
    "StudyTime": "143022",
    "SOPInstanceUID": "1.2.840.10008..."
}
```

## File Naming Convention

Received files are saved as:
```
{PatientID}_{Modality}_{Timestamp}_{UID}.dcm
```

Example:
```
12345_OP_20260111_143530_1a2b3c4d.dcm
```

## Logs

View real-time DICOM transmissions:

```bash
docker logs refracto_dicom_service -f
```

## Integration with Other Services

### Future: Auto-forward to Imaging Service

The `handle_store` callback can be extended to:

```python
def handle_store(event):
    # ... save DICOM file ...
    
    # Convert DICOM to JPEG/PNG
    image = convert_dicom_to_image(filepath)
    
    # Upload to imaging service
    upload_to_imaging_service(
        patient_id=patient_id,
        image_data=image,
        modality=modality
    )
    
    # Trigger ML analysis
    trigger_ml_analysis(filepath)
    
    return 0x0000
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 11112
netstat -ano | findstr :11112

# Kill the process or change DICOM_PORT in main.py
```

### DICOM Device Can't Connect

1. **Check firewall**: Allow port 11112
2. **Verify network**: Device and server on same network
3. **Test with echoscu**: Verify basic connectivity
4. **Check AE Title**: Must match exactly (case-sensitive)

### Files Not Saving

```bash
# Check permissions
docker exec -it refracto_dicom_service ls -la /tmp/dicom_received

# Check logs for errors
docker logs refracto_dicom_service
```

## Security Considerations

### Production Deployment

1. **Network Isolation**: Use VPN or private network
2. **AE Title Validation**: Restrict allowed calling AE titles
3. **IP Whitelisting**: Only accept from known devices
4. **TLS Encryption**: Use DICOM TLS for encrypted transmission
5. **Authentication**: Implement DICOM user authentication

### Implementation Example

```python
ALLOWED_CALLING_AE = ['FUNDUS_01', 'OCT_SCANNER_02']
ALLOWED_IPS = ['192.168.1.10', '192.168.1.11']

def validate_association(event):
    calling_ae = event.assoc.requestor.ae_title
    calling_ip = event.assoc.requestor.address
    
    if calling_ae not in ALLOWED_CALLING_AE:
        return False
    if calling_ip not in ALLOWED_IPS:
        return False
    return True
```

## Performance

- **Concurrent associations**: Supports multiple devices simultaneously
- **Throughput**: Depends on network and file size
- **Typical fundus image**: 1-5 MB, ~1-2 seconds transfer
- **OCT volume**: 10-50 MB, ~5-10 seconds transfer

## Next Steps

1. **Convert DICOM to Standard Images**: Add DICOM → JPEG/PNG conversion
2. **Auto-upload to MinIO**: Forward to imaging service
3. **Patient Matching**: Auto-link to patient records
4. **Immediate Analysis**: Trigger ML service on receipt
5. **Web Interface**: Admin panel to view received studies
6. **HL7 Integration**: Match with patient ADT messages

---

**DICOM Service is ready to receive medical images!** 📡🏥
