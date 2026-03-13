# Phase 1 Implementation Guide: Critical Foundations (P0 Features)
**Refracto AI - Hybrid XAI Clinical Decision Support System**

---

## Overview

This document provides step-by-step technical implementation guidance for **9 P0 (critical) features** that must be completed before Phase 2 work proceeds. These features form the architectural backbone of the entire system.

---

## Feature 1: Multi-Modal Fusion Architecture (A1.2)

### Current State
```python
# Current: Separate models loaded independently
self.fundus_model = timm.create_model('efficientnet_b3', pretrained=True, num_classes=5)
self.oct_model = ViTForImageClassification.from_pretrained(model_name, num_labels=3)
# No fusion; model.predict() routes entirely to one model or the other
```

### Target State
```
Input: Fundus (224×224) + OCT (224×224) + Structured Data
    ↓
┌─────────────────────┬────────────────────┐
│  Fundus Branch      │    OCT Branch      │
│ (EfficientNet-B3)   │  (Vision Transformer)
│ ↓                   │    ↓               │
│ Features: (1000)    │  Features: (768)   │
└─────────────────────┴────────────────────┘
         ↓                     ↓
    ┌─────────────────────────┐
    │  Multi-Head Attention   │  ← Cross-modality interaction
    │  (Transformer Fusion)   │
    └──────────┬──────────────┘
               ↓
         Fused Features (512)
               ↓
    ┌──────────┴────────────────────┐
    ↓                               ↓
┌─────────────────────┐    ┌──────────────────┐
│ Classification Head │    │ Regression Head  │
│ (DR + Glaucoma)     │    │ (Refraction)     │
└─────────────────────┘    └──────────────────┘
```

### Implementation Steps

#### Step 1.1: Create Fusion Module
**File**: `backend/services/ml_service/core/fusion.py` (NEW)

```python
import torch
import torch.nn as nn
from typing import Tuple, Dict

class MultiHeadFusion(nn.Module):
    """
    Multi-head attention-based fusion of Fundus and OCT features
    """
    def __init__(self, fundus_dim: int = 1000, oct_dim: int = 768, fusion_dim: int = 512):
        super().__init__()
        
        # Project both modalities to same dimension
        self.fundus_proj = nn.Linear(fundus_dim, fusion_dim)
        self.oct_proj = nn.Linear(oct_dim, fusion_dim)
        
        # Multi-head attention (4 heads)
        self.attention = nn.MultiheadAttention(
            embed_dim=fusion_dim,
            num_heads=4,
            batch_first=True,
            dropout=0.1
        )
        
        # Fusion output layer
        self.fusion_layer = nn.Sequential(
            nn.Linear(fusion_dim * 2, fusion_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(fusion_dim, fusion_dim)
        )
        
        self.layer_norm = nn.LayerNorm(fusion_dim)
    
    def forward(self, fundus_features: torch.Tensor, oct_features: torch.Tensor) -> torch.Tensor:
        """
        Args:
            fundus_features: (B, 1000)
            oct_features: (B, 768)
        
        Returns:
            fused_features: (B, 512)
        """
        # Project to common dimension
        fundus_proj = self.fundus_proj(fundus_features)  # (B, 512)
        oct_proj = self.oct_proj(oct_features)  # (B, 512)
        
        # Attention: use fundus as query, oct as key/value
        fundus_unsqueezed = fundus_proj.unsqueeze(1)  # (B, 1, 512)
        oct_unsqueezed = oct_proj.unsqueeze(1)  # (B, 1, 512)
        
        attn_output, _ = self.attention(
            query=fundus_unsqueezed,
            key=oct_unsqueezed,
            value=oct_unsqueezed
        )  # (B, 1, 512)
        
        attn_output = attn_output.squeeze(1)  # (B, 512)
        
        # Combine with residual
        combined = torch.cat([fundus_proj, attn_output], dim=1)  # (B, 1024)
        fused = self.fusion_layer(combined)  # (B, 512)
        
        # Layer normalization
        fused = self.layer_norm(fused + attn_output)  # Residual connection
        
        return fused
```

#### Step 1.2: Create Unified MTL Model
**File**: `backend/services/ml_service/core/mtl_model.py` (NEW)

```python
import torch
import torch.nn as nn
from typing import Dict, Tuple
from .fusion import MultiHeadFusion

class RefractoMTLModel(nn.Module):
    """
    Unified Multi-Task Learning model for Refracto AI
    Outputs:
    - DR Grade (0-4): 5-class classification
    - Glaucoma: Binary classification
    - Refraction: (Sphere, Cylinder, Axis) regression
    """
    
    def __init__(
        self,
        fundus_backbone,  # Pre-trained EfficientNet-B3
        oct_backbone,     # Pre-trained ViT
        fusion_dim: int = 512
    ):
        super().__init__()
        
        self.fundus_backbone = fundus_backbone
        self.oct_backbone = oct_backbone
        
        # Fusion layer
        self.fusion = MultiHeadFusion(fundus_dim=1000, oct_dim=768, fusion_dim=fusion_dim)
        
        # Task-specific heads
        # Task 1: DR Classification
        self.dr_head = nn.Sequential(
            nn.Linear(fusion_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 5)  # 5 DR grades
        )
        
        # Task 2: Glaucoma Classification
        self.glaucoma_head = nn.Sequential(
            nn.Linear(fusion_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1)  # Binary: sigmoid applied in loss
        )
        
        # Task 3: Refraction Regression
        self.refraction_head = nn.Sequential(
            nn.Linear(fusion_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 3)  # Sphere, Cylinder, Axis
        )
    
    def forward(
        self,
        fundus_image: torch.Tensor,
        oct_image: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Args:
            fundus_image: (B, 3, 224, 224)
            oct_image: (B, 3, 224, 224)
        
        Returns:
            dict with keys: 'dr_logits', 'glaucoma_logits', 'refraction'
        """
        # Extract features from backbones
        with torch.no_grad():
            fundus_features = self.fundus_backbone(fundus_image)  # (B, 1000)
            oct_features = self.oct_backbone.forward_features(oct_image)  # (B, 768)
            oct_features = torch.nn.functional.adaptive_avg_pool2d(oct_features, (1, 1)).flatten(1)
        
        # Fuse features
        fused_features = self.fusion(fundus_features, oct_features)  # (B, 512)
        
        # Task-specific predictions
        dr_logits = self.dr_head(fused_features)  # (B, 5)
        glaucoma_logits = self.glaucoma_head(fused_features)  # (B, 1)
        refraction = self.refraction_head(fused_features)  # (B, 3)
        
        # Apply constraints to refraction outputs
        sphere = torch.tanh(refraction[:, 0]) * 20  # Range: -20 to +20
        cylinder = -torch.sigmoid(refraction[:, 1]) * 6  # Range: 0 to -6
        axis = torch.sigmoid(refraction[:, 2]) * 180  # Range: 0 to 180
        
        return {
            'dr_logits': dr_logits,
            'glaucoma_logits': glaucoma_logits,
            'refraction': torch.stack([sphere, cylinder, axis], dim=1)
        }
```

#### Step 1.3: Update Model Loader
**File**: `backend/services/ml_service/core/model_loader.py` (MODIFY)

```python
# Add to RefractoModels class:

def _load_mtl_model(self):
    """Load unified Multi-Task Learning model"""
    logger.info("🔥 Loading Unified MTL Model...")
    
    try:
        # Load backbones
        fundus_backbone = timm.create_model('efficientnet_b3', pretrained=True, num_classes=0)
        oct_backbone = timm.create_model('vit_base_patch16_224', pretrained=True, num_classes=0)
        
        # Create MTL model
        from .mtl_model import RefractoMTLModel
        self.mtl_model = RefractoMTLModel(
            fundus_backbone=fundus_backbone,
            oct_backbone=oct_backbone,
            fusion_dim=512
        )
        
        self.mtl_model = self.mtl_model.to(self.device)
        self.mtl_model.eval()
        
        logger.info("✓ MTL model loaded successfully")
        
    except Exception as e:
        logger.error(f"✗ Failed to load MTL model: {str(e)}")
        raise
```

---

## Feature 2: Refracto-Pathological Link Module (A1.4)

### Current State
- Glaucoma and Refractive predictions are independent
- No modeling of how myopia affects optic disc morphology
- False positives in highly myopic patients unaddressed

### Target State
- Myopia parameter feeds into glaucoma prediction
- Cup-to-Disc Ratio (CDR) adjusted based on axial length
- Flag: "High Myopia Risk Factor" when Sphere < -6

### Implementation

**File**: `backend/services/ml_service/core/refracto_pathological_link.py` (NEW)

```python
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Tuple

class RefractoPathologicalLink(nn.Module):
    """
    Explicitly models the relationship between refractive status and pathological features
    Reduces false positives in glaucoma diagnosis for highly myopic patients
    """
    
    def __init__(self, hidden_dim: int = 128):
        super().__init__()
        
        # Process refractive parameters to extract myopia severity
        self.myopia_processor = nn.Sequential(
            nn.Linear(3, hidden_dim),  # Sphere, Cylinder, Axis
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, 64)
        )
        
        # Correction factor for glaucoma prediction
        self.glaucoma_correction = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)  # Single correction factor
        )
        
        # Correction factor for DR (less myopia dependence, but still relevant)
        self.dr_correction = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    
    def forward(self, refraction: torch.Tensor, glaucoma_logits: torch.Tensor, dr_logits: torch.Tensor) -> Dict:
        """
        Args:
            refraction: (B, 3) - [Sphere, Cylinder, Axis]
            glaucoma_logits: (B, 1) - Raw glaucoma prediction
            dr_logits: (B, 5) - Raw DR logits
        
        Returns:
            dict with corrected predictions and explanations
        """
        # Extract myopia severity
        myopia_features = self.myopia_processor(refraction)  # (B, 64)
        
        # Calculate correction factors
        glaucoma_correction = torch.sigmoid(self.glaucoma_correction(myopia_features))  # (B, 1), range [0, 1]
        dr_correction = self.dr_correction(myopia_features)  # (B, 1), range [-1, 1]
        
        # Apply corrections
        glaucoma_corrected = glaucoma_logits * (1 - glaucoma_correction * 0.3)  # Reduce by up to 30% for myopes
        dr_corrected = dr_logits + dr_correction.unsqueeze(2)  # Small adjustment
        
        # Calculate additional features for explanation
        sphere = refraction[:, 0]
        is_high_myopia = (sphere < -6).float()  # Flag high myopia
        myopia_severity = torch.clamp(sphere / -20, 0, 1)  # Normalize to [0, 1]
        
        return {
            'glaucoma_logits_corrected': glaucoma_corrected,
            'dr_logits_corrected': dr_corrected,
            'glaucoma_correction_factor': glaucoma_correction,
            'dr_correction_factor': dr_correction,
            'myopia_severity': myopia_severity,
            'is_high_myopia': is_high_myopia,
            'explanation': self._generate_explanation(sphere, glaucoma_correction, myopia_severity)
        }
    
    def _generate_explanation(self, sphere: torch.Tensor, correction_factor: torch.Tensor, severity: torch.Tensor) -> str:
        """Generate explanation text for the correction applied"""
        batch_expl = []
        for s, c, sev in zip(sphere.cpu().numpy(), correction_factor.cpu().numpy(), severity.cpu().numpy()):
            if s < -6:
                expl = f"High myopia (Sphere {s:.2f}D) detected. Glaucoma prediction adjusted down by {c[0]*100:.1f}% to account for refractive artifact in optic disc morphology."
            elif s < -3:
                expl = f"Moderate myopia (Sphere {s:.2f}D) detected. Minor glaucoma prediction adjustment applied."
            else:
                expl = f"Minimal refractive correction needed (Sphere {s:.2f}D)."
            batch_expl.append(expl)
        return batch_expl
```

### Integration into MTL Model

Add to `RefractoMTLModel`:

```python
from .refracto_pathological_link import RefractoPathologicalLink

class RefractoMTLModel(nn.Module):
    def __init__(self, ...):
        # ... existing code ...
        self.refracto_link = RefractoPathologicalLink()
    
    def forward(self, fundus_image, oct_image):
        # ... existing feature extraction and task heads ...
        
        # Apply refracto-pathological linking
        link_output = self.refracto_link(
            refraction=refraction,
            glaucoma_logits=glaucoma_logits,
            dr_logits=dr_logits
        )
        
        return {
            'dr_logits': link_output['dr_logits_corrected'],
            'glaucoma_logits': link_output['glaucoma_logits_corrected'],
            'refraction': refraction,
            'refracto_link_metadata': {
                'myopia_severity': link_output['myopia_severity'],
                'is_high_myopia': link_output['is_high_myopia'],
                'correction_explanation': link_output['explanation']
            }
        }
```

---

## Feature 3: Multi-Modal Data Ingestion Pipeline (A3.1)

### Current State
- Single-file uploads only
- No co-registration validation
- No automated pairing of Fundus ↔ OCT

### Target State
```
Patient Upload Session
    ↓
┌─────────────────────────────────────────┐
│ Fundus-OCT Pair Ingestion Module        │
├─────────────────────────────────────────┤
│ 1. User uploads: fundus.jpg + oct.dcm   │
│ 2. DICOM parsing (if OCT is DICOM)      │
│ 3. Image quality check                  │
│ 4. Automatic pairing validation         │
│ 5. Co-registration check (optional)     │
│ 6. Store with metadata linking          │
└─────────────────────────────────────────┘
```

### Implementation

**File**: `backend/services/imaging_service/multimodal_ingestion.py` (NEW)

```python
import os
import pydicom
from pathlib import Path
from typing import Dict, Tuple, Optional
from PIL import Image
import torch
from torchvision import transforms
import numpy as np
from datetime import datetime

class MultiModalIngestor:
    """
    Handles co-registered Fundus + OCT image ingestion
    """
    
    def __init__(self, quality_threshold: float = 0.7):
        self.quality_threshold = quality_threshold
        
        # Image quality model (trained on ImageNet, repurposed for medical image QC)
        self.quality_model = self._load_quality_model()
    
    def _load_quality_model(self):
        """Load a lightweight model for image quality assessment"""
        import timm
        model = timm.create_model('mobilenetv3_small_100', pretrained=True, num_classes=1)
        model.eval()
        return model
    
    def ingest_multimodal_pair(
        self,
        fundus_bytes: bytes,
        oct_bytes: bytes,
        patient_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Ingest a co-registered Fundus + OCT pair
        
        Args:
            fundus_bytes: Binary image data (JPG/PNG)
            oct_bytes: Binary DICOM or image data
            patient_id: Patient identifier
            metadata: Optional metadata (timestamp, device, etc.)
        
        Returns:
            dict with ingestion status and pair metadata
        """
        results = {
            'success': False,
            'fundus_id': None,
            'oct_id': None,
            'pair_id': None,
            'quality_scores': {},
            'warnings': [],
            'errors': []
        }
        
        try:
            # Step 1: Parse Fundus
            fundus_pil = Image.open(io.BytesIO(fundus_bytes)).convert('RGB')
            fundus_quality = self._assess_quality(fundus_pil, modality='fundus')
            results['quality_scores']['fundus'] = fundus_quality
            
            if fundus_quality < self.quality_threshold:
                results['warnings'].append(f"Fundus image quality low ({fundus_quality:.2f})")
            
            # Step 2: Parse OCT
            oct_parsed = self._parse_oct(oct_bytes)
            if oct_parsed['type'] == 'dicom':
                oct_image = self._extract_oct_bscan(oct_parsed['dicom'])
            else:
                oct_image = Image.open(io.BytesIO(oct_bytes)).convert('RGB')
            
            oct_quality = self._assess_quality(oct_image, modality='oct')
            results['quality_scores']['oct'] = oct_quality
            
            if oct_quality < self.quality_threshold:
                results['warnings'].append(f"OCT image quality low ({oct_quality:.2f})")
            
            # Step 3: Validate pairing
            pairing_score = self._validate_pairing(fundus_pil, oct_image, patient_id)
            results['pairing_score'] = pairing_score
            
            if pairing_score < 0.6:
                results['warnings'].append(f"Co-registration confidence low ({pairing_score:.2f}); manual review recommended")
            
            # Step 4: Generate pair metadata
            pair_metadata = {
                'patient_id': patient_id,
                'pair_timestamp': datetime.utcnow().isoformat(),
                'fundus_quality': float(fundus_quality),
                'oct_quality': float(oct_quality),
                'pairing_confidence': float(pairing_score),
                'metadata': metadata or {}
            }
            
            results['success'] = True
            results['pair_metadata'] = pair_metadata
            
        except Exception as e:
            results['errors'].append(str(e))
        
        return results
    
    def _assess_quality(self, image: Image.Image, modality: str) -> float:
        """
        Assess image quality using features and DL model
        Returns score 0-1
        """
        # Convert to tensor
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        tensor = transform(image).unsqueeze(0)
        
        # Model-based quality score
        with torch.no_grad():
            score = torch.sigmoid(self.quality_model(tensor)).item()
        
        # Feature-based checks
        img_array = np.array(image)
        
        # Brightness check
        brightness = np.mean(img_array)
        if brightness < 30 or brightness > 220:
            score *= 0.8  # Penalize extreme brightness
        
        # Contrast check
        contrast = np.std(img_array)
        if contrast < 20:
            score *= 0.7  # Penalize low contrast
        
        return max(0, min(1, score))
    
    def _parse_oct(self, oct_bytes: bytes) -> Dict:
        """Parse OCT data (DICOM or standard image)"""
        try:
            dcm = pydicom.dcmread(io.BytesIO(oct_bytes))
            return {'type': 'dicom', 'dicom': dcm}
        except:
            return {'type': 'image'}
    
    def _extract_oct_bscan(self, dcm) -> Image.Image:
        """Extract B-scan from DICOM and return as PIL Image"""
        # Get pixel data
        pixel_array = dcm.pixel_array
        
        # Normalize to 0-255
        pixel_array = ((pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
        
        # Convert to RGB (repeat grayscale)
        rgb_array = np.stack([pixel_array] * 3, axis=2)
        
        return Image.fromarray(rgb_array)
    
    def _validate_pairing(self, fundus: Image.Image, oct: Image.Image, patient_id: str) -> float:
        """
        Validate that fundus and OCT are from the same eye/session
        Returns confidence score 0-1
        """
        # Simple heuristic: both images should have similar dimensions and color distribution
        fundus_array = np.array(fundus.resize((224, 224)))
        oct_array = np.array(oct.resize((224, 224)))
        
        # Similarity metrics
        # 1. Color distribution similarity
        fundus_mean = fundus_array.mean(axis=(0, 1))
        oct_mean = oct_array.mean(axis=(0, 1))
       color_similarity = 1 - np.mean(np.abs(fundus_mean - oct_mean)) / 255
        
        # 2. Structure similarity (simplified)
        fundus_edges = np.std(fundus_array, axis=2)
        oct_edges = np.std(oct_array, axis=2)
        structure_similarity = 1 - np.abs(fundus_edges.mean() - oct_edges.mean()) / 255
        
        # Combined score
        pairing_score = (color_similarity * 0.3 + structure_similarity * 0.7)
        
        return max(0, min(1, pairing_score))


# Updated imaging service endpoint
@app.post("/upload-multimodal/{patient_id}")
async def upload_multimodal(
    patient_id: UUID,
    fundus_file: UploadFile = File(...),
    oct_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload co-registered Fundus + OCT pair"""
    ingestor = MultiModalIngestor()
    
    fundus_bytes = await fundus_file.read()
    oct_bytes = await oct_file.read()
    
    ingest_result = ingestor.ingest_multimodal_pair(fundus_bytes, oct_bytes, str(patient_id))
    
    if not ingest_result['success']:
        raise HTTPException(status_code=400, detail=ingest_result['errors'])
    
    # Store both images in MinIO
    fundus_path = f"patients/{patient_id}/fundus/{uuid.uuid4()}.jpg"
    oct_path = f"patients/{patient_id}/oct/{uuid.uuid4()}.dcm"
    
    minio = get_minio_handler()
    minio.upload_file(fundus_bytes, settings.MINIO_BUCKET, fundus_path)
    minio.upload_file(oct_bytes, settings.MINIO_BUCKET, oct_path)
    
    # Create paired record in DB
    pair_record = ImagePair(
        patient_id=patient_id,
        fundus_path=fundus_path,
        oct_path=oct_path,
        pairing_confidence=ingest_result['pairing_score'],
        quality_metadata=json.dumps(ingest_result['quality_scores']),
        warnings=json.dumps(ingest_result['warnings'])
    )
    
    db.add(pair_record)
    db.commit()
    
    return {
        'message': 'Multimodal pair uploaded successfully',
        'pair_id': pair_record.id,
        'quality_scores': ingest_result['quality_scores'],
        'warnings': ingest_result['warnings']
    }
```

### Update Database Schema

**File**: `backend/services/imaging_service/models.py` (ADD)

```python
class ImagePair(Base):
    __tablename__ = "image_pairs"
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    fundus_path = Column(String, nullable=False)
    oct_path = Column(String, nullable=False)
    fundus_id = Column(Integer, ForeignKey("image_records.id"))
    oct_id = Column(Integer, ForeignKey("image_records.id"))
    pairing_confidence = Column(Float, default=0.5)
    quality_metadata = Column(JSON)  # {fundus_quality, oct_quality}
    warnings = Column(JSON)  # List of warnings
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## Feature 4: Sri Lankan Local Patient Data Management (A3.3)

### Current State
- No local data collection infrastructure
- No anonymization/de-identification process
- No consent management

### Target State
- Dedicated admin panel for local data ingestion
- Automated de-identification
- Consent audit trail
- Compliance with local ethics approval

### Implementation

**File**: `backend/services/patient_service/local_data_manager.py` (NEW)

```python
import hashlib
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4
from enum import Enum

class DataAnonymizationLevel(Enum):
    FULL = "full"  # All PII removed
    PARTIAL = "partial"  # Date generalized to month/year
    NONE = "none"  # Full data (requires explicit consent)

class LocalDataManager:
    """
    Manages Sri Lankan patient data collection with ethics compliance
    """
    
    def __init__(self):
        self.anonymization_salt = os.getenv("ANONYMIZATION_SALT", "refracto_2026")
    
    def create_anonymized_patient(
        self,
        full_name: str,
        dob: str,
        gender: str,
        consent_level: DataAnonymizationLevel,
        consent_date: datetime,
        eth_approval_id: str
    ) -> Dict:
        """
        Create anonymized patient record with consent audit trail
        """
        # Generate patient hash ID
        hash_input = f"{full_name}_{dob}_{self.anonymization_salt}"
        anonymized_id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        # Parse DOB based on anonymization level
        if consent_level == DataAnonymizationLevel.FULL:
            age_at_consent = self._calculate_age_range(dob)  # E.g., "50-60"
            dob_generalized = None
        elif consent_level == DataAnonymizationLevel.PARTIAL:
            age_at_consent = self._calculate_age_from_dob(dob)
            dob_generalized = dob[:7]  # MM-YYYY only
        else:
            age_at_consent = self._calculate_age_from_dob(dob)
            dob_generalized = dob
        
        # Create audit trail entry
        audit_entry = {
            'anonymized_id': anonymized_id,
            'original_id_hash': hashlib.sha256(str(uuid4()).encode()).hexdigest(),  # Linkage key
            'consent_level': consent_level.value,
            'consent_signed_at': consent_date.isoformat(),
            'eth_approval_id': eth_approval_id,
            'created_at': datetime.utcnow().isoformat(),
            'country': 'Sri Lanka'
        }
        
        # Patient record
        patient_record = {
            'anonymized_patient_id': anonymized_id,
            'dob_generalized': dob_generalized,
            'age_range': age_at_consent,
            'gender': gender,
            'consent_audit': audit_entry,
            'can_identify_later': consent_level != DataAnonymizationLevel.FULL
        }
        
        return patient_record
    
    def _calculate_age_from_dob(self, dob: str) -> int:
        """Calculate exact age from DOB string (YYYY-MM-DD)"""
        from dateutil.relativedelta import relativedelta
        dob_parsed = datetime.strptime(dob, "%Y-%m-%d")
        today = datetime.today()
        return today.year - dob_parsed.year - ((today.month, today.day) < (dob_parsed.month, dob_parsed.day))
    
    def _calculate_age_range(self, dob: str) -> str:
        """Return age range (e.g., '50-60') for full anonymization"""
        age = self._calculate_age_from_dob(dob)
        decade_start = (age // 10) * 10
        return f"{decade_start}-{decade_start + 10}"
    
    def log_consent_compliance(
        self,
        anonymized_patient_id: str,
        action: str,  # "data_collected", "data_used_in_analysis", "data_shipped_to_cloud"
        details: Optional[Dict] = None
    ) -> Dict:
        """Log all data usage for compliance audit"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'anonymized_patient_id': anonymized_patient_id,
            'action': action,
            'details': details or {},
            'logged_by': 'system'
        }
        return log_entry
```

### Database Schema Addition

**File**: `backend/services/patient_service/models.py` (ADD)

```python
class LocalPatientConsent(Base):
    __tablename__ = "local_patient_consent"
    
    id = Column(Integer, primary_key=True)
    anonymized_patient_id = Column(String, uniqueindex=True)
    consent_level = Column(Enum(DataAnonymizationLevel))
    consent_signed_at = Column(DateTime)
    eth_approval_id = Column(String)  # Reference to ethics committee approval
    age_range = Column(String)
    gender = Column(String)
    country = Column(String, default="Sri Lanka")
    data_usage_logs = Column(JSON)  # List of audit entries
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DataConsentAudit(Base):
    __tablename__ = "data_consent_audit"
    
    id = Column(Integer, primary_key=True)
    anonymized_patient_id = Column(String, ForeignKey("local_patient_consent.anonymized_patient_id"))
    action = Column(String)  # "collection", "analysis", "export"
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON)
```

---

## Feature 5: Clinical Concordance Rate (CCR) Framework (A4.1)

### Current Story
- No comparison between AI and expert clinicians
- No structured validation mechanism
- CCR metric not measured

### Target State
```
Expert Panel Review Interface
    ↓
┌──────────────────────────────────────────────┐
│ Display AI Prediction + XAI Report           │
│ Ask Panel: "Do you agree?"                   │
│ Rating Scale: 1 (Strongly Disagree) - 5      │
│ Panel makes independent decision              │
│ Calculate agreement rate (CCR)                │
└──────────────────────────────────────────────┘
```

### Implementation

**File**: `backend/services/ml_service/clinical_concordance.py` (NEW)

```python
from enum import Enum
from typing import List, Dict
from datetime import datetime
import numpy as np

class ExpertAgreementLevel(Enum):
    STRONGLY_DISAGREE = 1
    DISAGREE = 2
    NEUTRAL = 3
    AGREE = 4
    STRONGLY_AGREE = 5

class ClinicalConcordanceManager:
    """
    Manages expert panel review and CCR measurement
    """
    
    def __init__(self):
        self.reviews = []
    
    def create_review_task(
        self,
        patient_id: str,
        prediction: Dict,
        xai_report: Dict,
        panel_size: int = 3
    ) -> Dict:
        """
        Create a review task for the expert panel
        
        Args:
            patient_id: Anonymized patient ID
            prediction: AI prediction (dr_grade, glaucoma_risk, refraction)
            xai_report: XAI explanation (Grad-CAM, SHAP, reasoning)
            panel_size: Number of experts to review
        
        Returns:
            Review task metadata
        """
        task_id = str(uuid4())
        
        review_task = {
            'id': task_id,
            'patient_id': patient_id,
            'ai_prediction': prediction,
            'xai_report': xai_report,
            'created_at': datetime.utcnow().isoformat(),
            'expert_reviews': [],  # Will be filled by experts
            'status': 'pending'
        }
        
        return review_task
    
    def submit_expert_review(
        self,
        task_id: str,
        expert_id: str,
        expert_name: str,
        ai_dr_grade: int,
        expert_dr_grade: int,
        dr_agreement: ExpertAgreementLevel,
        dr_notes: str,
        ai_glaucoma_risk: float,
        expert_glaucoma_risk: float,
        glaucoma_agreement: ExpertAgreementLevel,
        glaucoma_notes: str,
        ai_refraction: Dict,  # {sphere, cylinder, axis}
        expert_refraction: Dict,
        refraction_agreement: ExpertAgreementLevel,
        refraction_notes: str
    ) -> Dict:
        """
        Submit an expert's review of an AI prediction
        """
        review = {
            'expert_id': expert_id,
            'expert_name': expert_name,
            'submitted_at': datetime.utcnow().isoformat(),
            'dr': {
                'ai_prediction': ai_dr_grade,
                'expert_decision': expert_dr_grade,
                'agreement_level': dr_agreement.value,
                'notes': dr_notes,
                'match': ai_dr_grade == expert_dr_grade
            },
            'glaucoma': {
                'ai_risk': ai_glaucoma_risk,
                'expert_risk': expert_glaucoma_risk,
                'agreement_level': glaucoma_agreement.value,
                'notes': glaucoma_notes,
                'match': abs(ai_glaucoma_risk - expert_glaucoma_risk) < 0.2  # Threshold
            },
            'refraction': {
                'ai_prediction': ai_refraction,
                'expert_decision': expert_refraction,
                'agreement_level': refraction_agreement.value,
                'notes': refraction_notes,
                'sphere_mae': abs(ai_refraction['sphere'] - expert_refraction['sphere']),
                'axis_error': min(abs(ai_refraction['axis'] - expert_refraction['axis']), 360 - abs(ai_refraction['axis'] - expert_refraction['axis']))
            }
        }
        
        return review
    
    def calculate_ccr_for_patient(self, reviews: List[Dict]) -> Dict:
        """
        Calculate Clinical Concordance Rate for a single patient
        """
        if not reviews:
            return {'ccr': 0, 'details': {}}
        
        n_experts = len(reviews)
        dr_agreements = [r['dr']['match'] for r in reviews]
        glaucoma_agreements = [r['glaucoma']['match'] for r in reviews]
        refraction_mae_values = [r['refraction']['sphere_mae'] for r in reviews]
        
        # CCR: % of experts who agree with AI (matched decision)
        ccr_dr = sum(dr_agreements) / n_experts if dr_agreements else 0
        ccr_glaucoma = sum(glaucoma_agreements) / n_experts if glaucoma_agreements else 0
        ccr_refraction = 1 - (np.mean(refraction_mae_values) / 3)  # Normalize MAE to 0-1
        
        # Weighted overall CCR
        overall_ccr = (ccr_dr * 0.4 + ccr_glaucoma * 0.4 + ccr_refraction * 0.2)
        
        return {
            'ccr_dr': float(ccr_dr),
            'ccr_glaucoma': float(ccr_glaucoma),
            'ccr_refraction': float(max(0, ccr_refraction)),
            'overall_ccr': float(overall_ccr),
            'n_experts': n_experts,
            'avg_refraction_mae': float(np.mean(refraction_mae_values))
        }
    
    def calculate_aggregate_ccr(self, all_reviews: List[Dict]) -> Dict:
        """
        Calculate overall system CCR across all reviewed cases
        """
        if not all_reviews:
            return {'aggregate_ccr': 0, 'n_cases': 0}
        
        ccrs = [self.calculate_ccr_for_patient(case_reviews) for case_reviews in all_reviews]
        
        aggregate_ccr = np.mean([c['overall_ccr'] for c in ccrs])
        
        return {
            'aggregate_ccr': float(aggregate_ccr),
            'n_cases': len(ccrs),
            'per_case_ccrs': ccrs,
            'status': 'PASS (H3 hypothesis confirmed)' if aggregate_ccr > 0.85 else 'FAIL (H3 hypothesis rejected)'
        }
```

### Frontend Component for Expert Review

**File**: `frontend/src/components/ClinicalConcordancePanel.tsx` (NEW)

```tsx
import React, { useState } from 'react'
import { Card, Button, Rating, Textarea, Badge } from '@shadcn/ui'
import { CheckCircle, XCircle } from 'lucide-react'

interface ClinicalConcordancePanelProps {
  taskId: string
  aiPrediction: {
    dr_grade: number
    glaucoma_risk: number
    refraction: { sphere: number; cylinder: number; axis: number }
  }
  xaiReport: string
}

export const ClinicalConcordancePanel: React.FC<ClinicalConcordancePanelProps> = ({
  taskId,
  aiPrediction,
  xaiReport,
}) => {
  const [drExpertGrade, setDrExpertGrade] = useState<number | null>(null)
  const [drAgreement, setDrAgreement] = useState<number>(3)
  const [drNotes, setDrNotes] = useState('')
  
  const [glaucomaExpertRisk, setGlaucomaExpertRisk] = useState<number | null>(null)
  const [glaucomaAgreement, setGlaucomaAgreement] = useState<number>(3)
  const [glaucomaNotes, setGlaucomaNotes] = useState('')
  
  const [refractionExpert, setRefractionExpert] = useState({ sphere: 0, cylinder: 0, axis: 0 })
  const [refractionAgreement, setRefractionAgreement] = useState<number>(3)
  const [refractionNotes, setRefractionNotes] = useState('')
  
  const handleSubmit = async () => {
    const review = {
      task_id: taskId,
      expert_id: 'current_expert_id',  // From auth context
      expert_name: 'Dr. Name',
      dr_expert: drExpertGrade,
      dr_agreement: drAgreement,
      dr_notes: drNotes,
      glaucoma_expert: glaucomaExpertRisk,
      glaucoma_agreement: glaucomaAgreement,
      glaucoma_notes: glaucomaNotes,
      refraction_expert: refractionExpert,
      refraction_agreement: refractionAgreement,
      refraction_notes: refractionNotes,
    }
    
    // Submit to backend
    // await mlService.submitExpertReview(review)
  }
  
  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <Card className="p-6 bg-blue-50 border-blue-200">
        <h2 className="text-xl font-bold mb-4">AI Prediction Summary</h2>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-600">DR Grade</p>
            <p className="text-2xl font-bold">{aiPrediction.dr_grade}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Glaucoma Risk</p>
            <p className="text-2xl font-bold">{(aiPrediction.glaucoma_risk * 100).toFixed(0)}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Refraction</p>
            <p className="text-lg font-mono">SPH {aiPrediction.refraction.sphere:+.2f}</p>
          </div>
        </div>
      </Card>
      
      <Card className="p-6 bg-purple-50 border-purple-200">
        <h3 className="text-lg font-bold mb-2">XAI Explanation</h3>
        <p className="text-sm text-gray-700">{xaiReport}</p>
      </Card>
      
      {/* DR Grade Review */}
      <Card className="p-6">
        <h3 className="text-lg font-bold mb-4">DR Grade Assessment</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Your DR Grade (0-4)</label>
            <div className="flex gap-2">
              {[0, 1, 2, 3, 4].map((g) => (
                <Button
                  key={g}
                  onClick={() => setDrExpertGrade(g)}
                  variant={drExpertGrade === g ? 'default' : 'outline'}
                >
                  {g}
                </Button>
              ))}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Do you agree with AI?</label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((level) => (
                <Button
                  key={level}
                  onClick={() => setDrAgreement(level)}
                  variant={drAgreement === level ? 'default' : 'outline'}
                  size="sm"
                >
                  {level}
                </Button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">1=Strongly Disagree, 5=Strongly Agree</p>
          </div>
          
          <Textarea
            placeholder="Additional notes"
            value={drNotes}
            onChange={(e) => setDrNotes(e.target.value)}
            rows={3}
          />
        </div>
      </Card>
      
      {/* Glaucoma Review */}
      <Card className="p-6">
        <h3 className="text-lg font-bold mb-4">Glaucoma Risk Assessment</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Your Glaucoma Risk (%)</label>
            <input
              type="number"
              min="0"
              max="100"
              value={glaucomaExpertRisk ?? ''}
              onChange={(e) => setGlaucomaExpertRisk(parseInt(e.target.value))}
              className="w-24 px-2 py-1 border rounded"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Do you agree?</label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((level) => (
                <Button
                  key={level}
                  onClick={() => setGlaucomaAgreement(level)}
                  variant={glaucomaAgreement === level ? 'default' : 'outline'}
                  size="sm"
                >
                  {level}
                </Button>
              ))}
            </div>
          </div>
          
          <Textarea
            placeholder="Notes"
            value={glaucomaNotes}
            onChange={(e) => setGlaucomaNotes(e.target.value)}
            rows={3}
          />
        </div>
      </Card>
      
      {/* Refraction Review */}
      <Card className="p-6">
        <h3 className="text-lg font-bold mb-4">Refraction Assessment</h3>
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium mb-1">Sphere</label>
              <input
                type="number"
                step="0.25"
                value={refractionExpert.sphere}
                onChange={(e) => setRefractionExpert({ ...refractionExpert, sphere: parseFloat(e.target.value) })}
                className="w-full px-2 py-1 border rounded"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Cylinder</label>
              <input
                type="number"
                step="0.25"
                value={refractionExpert.cylinder}
                onChange={(e) => setRefractionExpert({ ...refractionExpert, cylinder: parseFloat(e.target.value) })}
                className="w-full px-2 py-1 border rounded"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Axis</label>
              <input
                type="number"
                step="1"
                min="0"
                max="180"
                value={refractionExpert.axis}
                onChange={(e) => setRefractionExpert({ ...refractionExpert, axis: parseFloat(e.target.value) })}
                className="w-full px-2 py-1 border rounded"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Agreement Level</label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((level) => (
                <Button
                  key={level}
                  onClick={() => setRefractionAgreement(level)}
                  variant={refractionAgreement === level ? 'default' : 'outline'}
                  size="sm"
                >
                  {level}
                </Button>
              ))}
            </div>
          </div>
          
          <Textarea
            placeholder="Notes"
            value={refractionNotes}
            onChange={(e) => setRefractionNotes(e.target.value)}
            rows={3}
          />
        </div>
      </Card>
      
      <Button onClick={handleSubmit} size="lg" className="w-full bg-green-600 hover:bg-green-700">
        Submit Review
      </Button>
    </div>
  )
}
```

---

## Feature 6: Ethical Audit Trail (A6.1)

### Current State
- No logging of AI decisions
- No accountability trail
- No compliance documentation

### Target State
```
Every AI Prediction → Immutable Audit Log
    │
    ├─ Patient ID (anonymized hash)
    ├─ Prediction (DR, Glaucoma, Refraction)
    ├─ Confidence scores
    ├─ Timestamp
    ├─ Clinician action (accepted/rejected/modified)
    ├─ Feedback flag (if incorrect)
    └─ Regulatory reference (ethics ID, consent)
```

### Implementation

**File**: `backend/services/ml_service/audit_logger.py` (NEW)

```python
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy import create_engine, Column, String, DateTime, Float, JSON, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class PredictionAuditLog(Base):
    __tablename__ = "prediction_audit_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    prediction_id = Column(String, unique=True, index=True)
    anonymized_patient_hash = Column(String, index=True)  # SHA256 hash of patient ID
    model_version = Column(String)
    input_modality = Column(JSON)  # {"has_fundus": true, "has_oct": true, "has_structured": true}
    predictions = Column(JSON)  # {dr_grade, glaucoma_risk, refraction}
    confidence_scores = Column(JSON)
    xai_metadata = Column(JSON)  # {grad_cam_path, shap_values, explanation_text}
    clinician_action = Column(String)  # "accepted", "rejected", "modified"
    clinician_id_hash = Column(String)  # Hashed clinician ID
    clinician_notes = Column(String)
    feedback_flag = Column(String)  # "none", "incorrect_dr", "incorrect_glaucoma", "incorrect_refraction"
    ethics_approval_id = Column(String)
    consent_level = Column(String)  # "full", "partial", "none"
    regulatory_notes = Column(String)

class AuditLogger:
    """
    Centralized audit logging for all ML predictions
    Ensuring compliance with ethics, privacy, and regulatory requirements
    """
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def log_prediction(
        self,
        patient_id: str,
        model_version: str,
        input_modality: Dict,
        predictions: Dict,
        confidence_scores: Dict,
        xai_metadata: Dict,
        ethics_approval_id: str,
        consent_level: str
    ) -> str:
        """
        Log a prediction to the audit trail
        
        Returns:
            prediction_id for tracking
        """
        # Generate anonymized hash of patient ID
        patient_hash = hashlib.sha256((patient_id + os.getenv("AUDIT_SALT", "refracto_2026")).encode()).hexdigest()
        
        # Generate unique prediction ID
        prediction_id = str(uuid4())
        
        # Create audit log entry
        log_entry = PredictionAuditLog(
            prediction_id=prediction_id,
            anonymized_patient_hash=patient_hash,
            model_version=model_version,
            input_modality=input_modality,
            predictions=predictions,
            confidence_scores=confidence_scores,
            xai_metadata=xai_metadata,
            ethics_approval_id=ethics_approval_id,
            consent_level=consent_level
        )
        
        session = self.Session()
        session.add(log_entry)
        session.commit()
        session.close()
        
        logger.info(f"Prediction logged: {prediction_id}")
        
        return prediction_id
    
    def log_clinician_action(
        self,
        prediction_id: str,
        clinician_id: str,
        action: str,  # "accepted", "rejected", "modified"
        notes: Optional[str] = None
    ):
        """Log clinician's action on a prediction"""
        clinician_hash = hashlib.sha256(clinician_id.encode()).hexdigest()
        
        session = self.Session()
        log_entry = session.query(PredictionAuditLog).filter_by(prediction_id=prediction_id).first()
        
        if log_entry:
            log_entry.clinician_action = action
            log_entry.clinician_id_hash = clinician_hash
            log_entry.clinician_notes = notes
            session.commit()
        
        session.close()
        
        logger.info(f"Clinician action logged for prediction {prediction_id}: {action}")
    
    def log_feedback(
        self,
        prediction_id: str,
        feedback_type: str,  # "incorrect_dr", "incorrect_glaucoma", "incorrect_refraction"
        notes: str
    ):
        """Log feedback when clinician flags a prediction as incorrect"""
        session = self.Session()
        log_entry = session.query(PredictionAuditLog).filter_by(prediction_id=prediction_id).first()
        
        if log_entry:
            log_entry.feedback_flag = feedback_type
            log_entry.clinician_notes = notes
            session.commit()
        
        session.close()
        
        logger.info(f"Feedback logged for prediction {prediction_id}: {feedback_type}")
    
    def generate_compliance_report(self, date_range: Tuple[datetime, datetime]) -> Dict:
        """Generate compliance report for ethics committee"""
        session = self.Session()
        
        start_date, end_date = date_range
        
        logs = session.query(PredictionAuditLog).filter(
            PredictionAuditLog.timestamp >= start_date,
            PredictionAuditLog.timestamp <= end_date
        ).all()
        
       report = {
            'period': f"{start_date.date()} to {end_date.date()}",
            'total_predictions': len(logs),
            'accepted': sum(1 for l in logs if l.clinician_action == 'accepted'),
            'rejected': sum(1 for l in logs if l.clinician_action == 'rejected'),
            'modified': sum(1 for l in logs if l.clinician_action == 'modified'),
            'feedback_count': sum(1 for l in logs if l.feedback_flag != 'none'),
            'avg_confidence_dr': np.mean([l.confidence_scores.get('dr', 0) for l in logs if l.confidence_scores]),
            'avg_confidence_glaucoma': np.mean([l.confidence_scores.get('glaucoma', 0) for l in logs if l.confidence_scores]),
            'consent_breakdown': {
                'full_anonymization': sum(1 for l in logs if l.consent_level == 'full'),
                'partial_anonymization': sum(1 for l in logs if l.consent_level == 'partial'),
                'full_data': sum(1 for l in logs if l.consent_level == 'none')
            }
        }
        
        session.close()
        
        return report
```

---

## Feature 7–9: Database Schema, Secrets Management, Consent UI

I'll create skeletal implementations for the remaining P0 features:

**File**: `backend/services/ml_service/.env.example` (NEW)

```env
# Secrets Management - NEVER commit .env file
ANONYMIZATION_SALT=your_secret_salt_here_change_in_production
AUDIT_SALT=your_audit_salt_here_change_in_production
SECRET_KEY=your_jwt_secret_key_change_in_production
DATABASE_URL=postgresql://user:password@postgres:5432/refracto_ai_db

# Ethics & Compliance
ETH_APPROVAL_ID=IEC_2026_OPHTHAL_001
ETH_COMMITTEE_EMAIL=ethics@hospital.lk
```

Use **HashiCorp Vault** or AWS Secrets Manager in production (not hardcoded).

---

## Summary: Phase 1 Deliverables Checklist

- [ ] **A1.2** Multi-Modal Fusion: `fusion.py` + `mtl_model.py` created
- [ ] **A1.4** Refracto-Pathological Link: `refracto_pathological_link.py` integrated into MTL
- [ ] **A3.1** Multi-Modal Ingestion: `multimodal_ingestion.py` with co-registration validation
- [ ] **A3.3** Local Data: `local_data_manager.py` with anonymization
- [ ] **A4.1** CCR Framework: `clinical_concordance.py` + frontend panel
- [ ] **A6.1** Audit Trail: `audit_logger.py` with immutable logs
- [ ] **B2.3** DB Schema: `PredictionAuditLog`, `ImagePair`, `LocalPatientConsent` tables
- [ ] **B6.2** Secrets: Migrate to Vault; update docker-compose
- [ ] **B5.4** Consent UI: React consent flow component

---

**Next Action**: Begin with Feature 1 (Fusion Architecture) as it's the foundational piece all others depend on.

