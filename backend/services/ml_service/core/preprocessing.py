"""
Image preprocessing utilities for ML inference
Supports: JPEG, PNG, TIFF, BMP, WebP, and DICOM (.dcm) files
"""

import torch
from PIL import Image
import torchvision.transforms as transforms
from typing import Union
import io
import numpy as np
import logging

logger = logging.getLogger(__name__)


def _is_dicom_bytes(data: bytes) -> bool:
    """Detect DICOM file by its magic bytes (DICM at offset 128)."""
    if len(data) > 132:
        return data[128:132] == b'DICM'
    # Also check for implicit DICOM (no preamble) by looking for common DICOM tags
    return data[:4] == b'\x08\x00\x00\x00' or data[:2] in (b'\x08\x00', b'\x02\x00')


def _dicom_bytes_to_pil(data: bytes) -> Image.Image:
    """
    Convert DICOM bytes to a PIL RGB image.

    Handles:
    - Standard DICOM with 128-byte preamble
    - Grayscale and color pixel data
    - Rescale slope/intercept for windowing
    - 8-bit and 16-bit pixel arrays
    """
    try:
        import pydicom
        from pydicom.filebase import DicomBytesIO
    except ImportError:
        raise RuntimeError(
            "pydicom is required to process DICOM files. "
            "It should be installed. Please rebuild the container."
        )

    try:
        ds = pydicom.dcmread(DicomBytesIO(data))
        pixel_array = ds.pixel_array  # numpy array

        # Apply rescale slope and intercept if present (for CT/MRI windowing)
        slope = float(getattr(ds, 'RescaleSlope', 1.0))
        intercept = float(getattr(ds, 'RescaleIntercept', 0.0))
        pixel_array = pixel_array * slope + intercept

        # Handle multi-frame DICOM: take the middle frame
        if pixel_array.ndim == 3 and pixel_array.shape[0] > 1 and pixel_array.shape[2] != 3:
            mid = pixel_array.shape[0] // 2
            pixel_array = pixel_array[mid]

        # Normalize to 0–255 uint8
        p_min, p_max = pixel_array.min(), pixel_array.max()
        if p_max > p_min:
            pixel_array = (pixel_array - p_min) / (p_max - p_min) * 255.0
        else:
            pixel_array = np.zeros_like(pixel_array, dtype=np.float32)

        pixel_array = pixel_array.astype(np.uint8)

        # Convert to PIL
        if pixel_array.ndim == 2:
            # Grayscale → RGB (most fundus / OCT DICOMs are grayscale)
            pil_image = Image.fromarray(pixel_array, mode='L').convert('RGB')
        elif pixel_array.ndim == 3 and pixel_array.shape[2] == 3:
            pil_image = Image.fromarray(pixel_array, mode='RGB')
        elif pixel_array.ndim == 3 and pixel_array.shape[2] == 4:
            pil_image = Image.fromarray(pixel_array, mode='RGBA').convert('RGB')
        else:
            raise ValueError(f"Unexpected pixel array shape: {pixel_array.shape}")

        logger.info(f"✓ DICOM decoded: {ds.get('Modality', 'UNK')} "
                    f"| {pil_image.size} | Patient: {ds.get('PatientID', 'N/A')}")
        return pil_image

    except Exception as e:
        logger.error(f"DICOM decode failed: {e}")
        raise ValueError(f"Could not read DICOM file: {e}")


class ImagePreprocessor:
    """
    Preprocessing pipelines for different image types.
    Supports standard image formats and DICOM.
    """

    def __init__(self):
        """Initialize preprocessing transforms"""

        # Standard ImageNet normalization
        self.normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )

        # Fundus preprocessing (224x224)
        self.fundus_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            self.normalize
        ])

        # OCT preprocessing (224x224 for ViT)
        self.oct_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            self.normalize
        ])

        # Refraction preprocessing (same as fundus)
        self.refraction_transform = self.fundus_transform

    def preprocess(
        self,
        image: Union[Image.Image, bytes, np.ndarray],
        task_type: str = 'fundus'
    ) -> torch.Tensor:
        """
        Preprocess image for ML inference.

        Args:
            image: PIL Image, bytes (JPEG/PNG/DICOM), or numpy array
            task_type: Type of task ('fundus', 'oct', 'refraction')

        Returns:
            Preprocessed image tensor (C, H, W) ready for model input
        """
        # Convert bytes to PIL Image
        if isinstance(image, bytes):
            try:
                if _is_dicom_bytes(image):
                    logger.info("📄 Detected DICOM file — decoding with pydicom")
                    image = _dicom_bytes_to_pil(image)
                else:
                    image = Image.open(io.BytesIO(image))
            except Exception as e:
                logger.error(f"Failed to load image bytes: {e}")
                raise

        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)

        # Ensure PIL Image is RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Apply appropriate transform
        if task_type == 'fundus':
            tensor = self.fundus_transform(image)
        elif task_type == 'oct':
            tensor = self.oct_transform(image)
        elif task_type == 'refraction':
            tensor = self.refraction_transform(image)
        else:
            raise ValueError(f"Unknown task_type: {task_type}")

        return tensor


# Global preprocessor instance (singleton)
_preprocessor = None


def get_preprocessor() -> ImagePreprocessor:
    """Get singleton preprocessor instance"""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = ImagePreprocessor()
    return _preprocessor
