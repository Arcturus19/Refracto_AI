from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pydicom


@dataclass(frozen=True)
class DicomImage:
    pixels: np.ndarray  # float32, shape (H, W), range [0, 1]
    photometric: Optional[str] = None


def _sanitize_photometric(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bytes):
        try:
            value = value.decode(errors="ignore")
        except Exception:
            value = str(value)
    if not isinstance(value, str):
        value = str(value)

    # Some exports contain trailing garbage/nulls due to incorrect VR length.
    cleaned = "".join(ch for ch in value if ch.isalnum() or ch in {"_", " "}).strip().upper()
    if "MONOCHROME1" in cleaned:
        return "MONOCHROME1"
    if "MONOCHROME2" in cleaned:
        return "MONOCHROME2"
    if cleaned == "RGB" or "RGB" in cleaned:
        return "RGB"
    return None


def _infer_hw_from_count(pixel_count: int) -> Optional[tuple[int, int]]:
    # Common OCT-ish heights / preview sizes.
    preferred_heights = [1024, 800, 768, 600, 512, 480, 400, 320, 256, 224, 200, 160, 128, 100]
    for h in preferred_heights:
        if h > 0 and pixel_count % h == 0:
            w = pixel_count // h
            if 32 <= w <= 4096:
                return h, w
    return None


def _decode_zeiss_private_image(ds: pydicom.Dataset) -> Optional[np.ndarray]:
    """Decode image from known Zeiss private tags.

    Many Carl Zeiss Meditec exports embed preview/B-scan pixel arrays in
    (0073,xxxx) private OB elements rather than standard PixelData.
    """

    # Observed in this dataset: multiple 80,000-byte blobs.
    candidate_elements = [
        (0x0073, 0x1150),
        (0x0073, 0x1155),
        (0x0073, 0x1160),
        (0x0073, 0x1165),
        (0x0073, 0x1190),
        (0x0073, 0x1245),
        (0x0073, 0x1270),
    ]

    for tag in candidate_elements:
        if tag not in ds:
            continue
        elem = ds[tag]
        if getattr(elem, "VR", None) not in {"OB", "OW", "UN"}:
            continue

        value = getattr(elem, "value", None)
        if not isinstance(value, (bytes, bytearray)):
            continue
        if len(value) < 4096:
            continue

        # Interpret as little-endian uint16.
        if len(value) % 2 != 0:
            continue
        u16 = np.frombuffer(value, dtype="<u2")
        hw = _infer_hw_from_count(int(u16.size))
        if hw is None:
            continue

        h, w = hw
        try:
            img = u16.reshape((h, w))
        except Exception:
            continue

        # Convert to float32 and normalize.
        return img.astype(np.float32)

    return None


def _normalize_to_unit(x: np.ndarray) -> np.ndarray:
    x = x.astype(np.float32, copy=False)
    finite = np.isfinite(x)
    if not finite.any():
        return np.zeros_like(x, dtype=np.float32)

    x = x.copy()
    x[~finite] = 0.0

    mn = float(x.min())
    mx = float(x.max())
    if mx <= mn:
        return np.zeros_like(x, dtype=np.float32)
    return (x - mn) / (mx - mn)


def read_dicom_as_unit_float(path: Path) -> DicomImage:
    """Read DICOM and return normalized float image.

    - Uses Modality LUT when present (via pydicom.pixel_array already applying rescale).
    - Applies VOI LUT when possible for better visualization.
    - Ensures MONOCHROME1 images are inverted (so higher is brighter).
    """

    ds = pydicom.dcmread(str(path), force=True)

    photometric_raw = getattr(ds, "PhotometricInterpretation", None)
    photometric = _sanitize_photometric(photometric_raw)
    if photometric is not None:
        try:
            ds.PhotometricInterpretation = photometric
        except Exception:
            pass

    # Pixel array may be 2D or 3D. For OCT slices, usually 2D.
    try:
        arr = ds.pixel_array
    except Exception:
        # Common failure: corrupted PhotometricInterpretation or non-standard encoding.
        try:
            ds.PhotometricInterpretation = "MONOCHROME2"
            photometric = "MONOCHROME2"
            arr = ds.pixel_array
        except Exception:
            # Fallback: vendor private image blobs.
            vendor_img = _decode_zeiss_private_image(ds)
            if vendor_img is None:
                raise
            arr = vendor_img
    if arr.ndim == 3:
        # If multi-frame, take middle frame.
        arr = arr[arr.shape[0] // 2]

    # VOI LUT makes sense only for standard PixelData.
    if not isinstance(arr, np.ndarray):
        arr = np.asarray(arr)
    else:
        try:
            from pydicom.pixel_data_handlers.util import apply_voi_lut

            arr = apply_voi_lut(arr, ds)
        except Exception:
            pass

    # Prefer sanitized photometric if we computed it.
    if photometric is None:
        photometric = getattr(ds, "PhotometricInterpretation", None)
    x = np.asarray(arr)

    # Invert MONOCHROME1 (0=white, max=black)
    if isinstance(photometric, str) and photometric.upper() == "MONOCHROME1":
        x = x.max() - x

    x = _normalize_to_unit(x)
    return DicomImage(pixels=x, photometric=photometric)


def resize_nearest(image: np.ndarray, out_hw: Tuple[int, int]) -> np.ndarray:
    """Fast dependency-free resize using nearest neighbor (H,W)."""

    out_h, out_w = out_hw
    in_h, in_w = image.shape[:2]

    if (in_h, in_w) == (out_h, out_w):
        return image

    ys = (np.linspace(0, in_h - 1, out_h)).astype(np.int64)
    xs = (np.linspace(0, in_w - 1, out_w)).astype(np.int64)
    return image[ys][:, xs]
