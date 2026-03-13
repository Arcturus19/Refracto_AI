"""Multi-modal image ingestion with DICOM parsing and co-registration (P0.3)."""
import os
from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np
from dataclasses import dataclass
import time

try:
    import pydicom
except ImportError:
    pydicom = None

import cv2
from PIL import Image


@dataclass
class ImageQualityScore:
    """Quality assessment metrics."""
    sharpness: float  # Laplacian variance; >100 = sharp
    contrast: float   # Histogram spread; 0-1
    brightness: float # Pixel intensity mean; 0-255
    overall_score: float  # Weighted average; 0-1


class MultiModalIngester:
    """Ingest and validate Fundus + OCT image pairs with quality assessment.
    
    Features:
    - Image quality assessment (sharpness, contrast, brightness)
    - DICOM file parsing
    - Co-registration validation via feature matching
    - Graceful error handling
    """
    
    def __init__(self, quality_threshold: float = 0.7):
        self.quality_threshold = quality_threshold
    
    def assess_image_quality(self, image: np.ndarray) -> ImageQualityScore:
        """Assess image quality using multiple metrics.
        
        Args:
            image: (H, W) or (H, W, 3) numpy array in uint8
        
        Returns:
            ImageQualityScore with metrics and composite score
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.astype(np.uint8)
        
        # Sharpness: Laplacian variance
        laplacian = cv2.Laplacian(gray.astype(np.float32), cv2.CV_32F)
        sharpness = laplacian.var()
        
        # Contrast: normalized standard deviation
        contrast = np.std(gray) / 255.0
        
        # Brightness: mean pixel intensity
        brightness = np.mean(gray)
        
        # Composite score: weighted average
        sharpness_norm = min(sharpness / 500, 1.0)  # Normalize to [0,1]
        brightness_norm = 1.0 if (50 <= brightness <= 200) else (brightness / 255)
        
        overall = 0.4 * sharpness_norm + 0.3 * contrast + 0.3 * brightness_norm
        overall = float(np.clip(overall, 0.0, 1.0))
        
        return ImageQualityScore(
            sharpness=float(sharpness),
            contrast=float(contrast),
            brightness=float(brightness),
            overall_score=overall
        )
    
    def load_dicom(self, dicom_path: str) -> np.ndarray:
        """Load DICOM image and convert to RGB.
        
        Args:
            dicom_path: Path to DICOM file
        
        Returns:
            RGB image as (H, W, 3) uint8 numpy array
        """
        if pydicom is None:
            raise ImportError("pydicom not installed. Install via: pip install pydicom")
        
        ds = pydicom.dcmread(dicom_path)
        pixel_array = ds.pixel_array
        
        # Normalize to 8-bit
        if pixel_array.dtype != np.uint8:
            pixel_array = pixel_array.astype(np.float32)
            pixel_array = ((pixel_array - pixel_array.min()) / 
                          (pixel_array.max() - pixel_array.min() + 1e-8) * 255)
            pixel_array = pixel_array.astype(np.uint8)
        
        # Convert to RGB if grayscale
        if len(pixel_array.shape) == 2:
            pixel_array = np.stack([pixel_array] * 3, axis=2)
        
        return pixel_array.astype(np.uint8)
    
    def compute_feature_similarity(self, fundus: np.ndarray, oct: np.ndarray) -> float:
        """Compute co-registration confidence via SIFT feature matching.
        
        Returns:
            Similarity score [0, 1]. >0.6 = good co-registration.
        """
        try:
            # Resize to same dimensions
            h, w = fundus.shape[:2]
            oct_resized = cv2.resize(oct, (w, h))
            
            # Convert to grayscale
            fundus_gray = cv2.cvtColor(fundus, cv2.COLOR_RGB2GRAY) if len(fundus.shape) == 3 else fundus
            oct_gray = cv2.cvtColor(oct_resized, cv2.COLOR_RGB2GRAY) if len(oct_resized.shape) == 3 else oct_resized
            
            # Detect SIFT features
            sift = cv2.SIFT_create()
            kp_f, des_f = sift.detectAndCompute(fundus_gray, None)
            kp_o, des_o = sift.detectAndCompute(oct_gray, None)
            
            if des_f is None or des_o is None or len(kp_f) == 0 or len(kp_o) == 0:
                return 0.0
            
            # Match features via BFMatcher
            bf = cv2.BFMatcher()
            matches = bf.knnMatch(des_f, des_o, k=2)
            
            # Apply Lowe's ratio test
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)
            
            # Confidence based on match count
            max_kp = max(len(kp_f), len(kp_o))
            confidence = float(len(good_matches) / max_kp) if max_kp > 0 else 0.0
            confidence = min(confidence, 1.0)
            
            return confidence
        except Exception as e:
            print(f"Feature matching error: {e}")
            return 0.0
    
    def ingest_pair(self, fundus_path: str, oct_path: str, 
                   patient_id: str, anonymized_patient_hash: str) -> Dict:
        """Ingest and validate a Fundus + OCT pair.
        
        Args:
            fundus_path: Path to fundus image (.png, .jpg, or .dcm)
            oct_path: Path to OCT image (.png, .jpg, or .dcm)
            patient_id: Original patient ID
            anonymized_patient_hash: SHA-256 anonymized hash
        
        Returns:
            Ingestion result with validation status and metadata
        """
        try:
            # Load images
            if fundus_path.endswith('.dcm'):
                fundus_arr = self.load_dicom(fundus_path)
            else:
                fundus_arr = np.array(Image.open(fundus_path).convert('RGB'))
            
            if oct_path.endswith('.dcm'):
                oct_arr = self.load_dicom(oct_path)
            else:
                oct_arr = np.array(Image.open(oct_path).convert('RGB'))
            
            # Assess quality
            fundus_quality = self.assess_image_quality(fundus_arr)
            oct_quality = self.assess_image_quality(oct_arr)
            
            # Check quality thresholds
            if fundus_quality.overall_score < self.quality_threshold:
                return {
                    "status": "rejected",
                    "reason": f"Fundus quality too low: {fundus_quality.overall_score:.3f} < {self.quality_threshold}",
                    "patient_id": anonymized_patient_hash,
                    "ingestion_metadata": None
                }
            
            if oct_quality.overall_score < self.quality_threshold:
                return {
                    "status": "rejected",
                    "reason": f"OCT quality too low: {oct_quality.overall_score:.3f} < {self.quality_threshold}",
                    "patient_id": anonymized_patient_hash,
                    "ingestion_metadata": None
                }
            
            # Compute co-registration confidence
            coregistration_confidence = self.compute_feature_similarity(fundus_arr, oct_arr)
            
            if coregistration_confidence < 0.5:
                return {
                    "status": "flagged",
                    "reason": f"Low co-registration confidence: {coregistration_confidence:.3f}. Requires manual review.",
                    "patient_id": anonymized_patient_hash,
                    "ingestion_metadata": None
                }
            
            # Success: All quality checks pass
            return {
                "status": "accepted",
                "patient_id": anonymized_patient_hash,
                "ingestion_metadata": {
                    "fundus_quality": float(fundus_quality.overall_score),
                    "oct_quality": float(oct_quality.overall_score),
                    "coregistration_confidence": float(coregistration_confidence),
                    "fundus_sharpness": float(fundus_quality.sharpness),
                    "oct_sharpness": float(oct_quality.sharpness),
                    "pair_id": f"{anonymized_patient_hash}_{int(time.time())}"
                }
            }
        
        except Exception as e:
            return {
                "status": "error",
                "reason": f"Ingestion error: {str(e)}",
                "patient_id": anonymized_patient_hash,
                "ingestion_metadata": None
            }
