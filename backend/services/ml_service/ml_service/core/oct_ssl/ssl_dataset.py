from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from torch.utils.data import Dataset

from .dicom_io import read_dicom_as_unit_float, resize_nearest


@dataclass(frozen=True)
class ManifestRow:
    sample_id: str
    split: str
    study_dir: Path
    rep_dicom_path: Path
    dicom_count: int
    total_bytes: int


def load_manifest_csv(path: Path) -> list[ManifestRow]:
    rows: list[ManifestRow] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(
                ManifestRow(
                    sample_id=r["sample_id"],
                    split=r["split"],
                    study_dir=Path(r["study_dir"]),
                    rep_dicom_path=Path(r["rep_dicom_path"]),
                    dicom_count=int(r["dicom_count"]),
                    total_bytes=int(r["total_bytes"]),
                )
            )
    return rows


class PairAugment:
    """Two stochastic views of the same OCT slice (simple CPU-friendly aug)."""

    def __init__(self, out_hw: tuple[int, int], seed: Optional[int] = None):
        self.out_hw = out_hw
        self._rng = np.random.default_rng(seed)

    def _random_crop(self, img: np.ndarray) -> np.ndarray:
        h, w = img.shape
        out_h, out_w = self.out_hw

        # Crop from a slightly larger resized image to add translation jitter.
        scale = float(self._rng.uniform(1.0, 1.15))
        crop_h = int(round(out_h * scale))
        crop_w = int(round(out_w * scale))

        resized = resize_nearest(img, (crop_h, crop_w))

        top = int(self._rng.integers(0, max(1, crop_h - out_h + 1)))
        left = int(self._rng.integers(0, max(1, crop_w - out_w + 1)))
        patch = resized[top : top + out_h, left : left + out_w]
        if patch.shape != (out_h, out_w):
            patch = resize_nearest(patch, (out_h, out_w))
        return patch

    def _random_intensity(self, img: np.ndarray) -> np.ndarray:
        # gamma + brightness/contrast
        gamma = float(self._rng.uniform(0.8, 1.25))
        x = np.clip(img, 0.0, 1.0) ** gamma
        contrast = float(self._rng.uniform(0.9, 1.1))
        brightness = float(self._rng.uniform(-0.05, 0.05))
        x = x * contrast + brightness
        return np.clip(x, 0.0, 1.0)

    def _random_noise(self, img: np.ndarray) -> np.ndarray:
        if self._rng.random() < 0.35:
            sigma = float(self._rng.uniform(0.0, 0.03))
            img = img + self._rng.normal(0.0, sigma, size=img.shape).astype(np.float32)
        return np.clip(img, 0.0, 1.0)

    def __call__(self, img: np.ndarray) -> tuple[torch.Tensor, torch.Tensor]:
        v1 = self._random_crop(img)
        v2 = self._random_crop(img)

        v1 = self._random_intensity(v1)
        v2 = self._random_intensity(v2)

        v1 = self._random_noise(v1)
        v2 = self._random_noise(v2)

        # To torch: 1xHxW
        t1 = torch.from_numpy(v1.astype(np.float32)).unsqueeze(0)
        t2 = torch.from_numpy(v2.astype(np.float32)).unsqueeze(0)
        return t1, t2


class OctSslDataset(Dataset):
    def __init__(
        self,
        manifest_rows: list[ManifestRow],
        out_hw: tuple[int, int] = (224, 224),
        seed: Optional[int] = 0,
    ):
        self.rows = manifest_rows
        self.augment = PairAugment(out_hw=out_hw, seed=seed)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int):
        row = self.rows[idx]
        try:
            dicom = read_dicom_as_unit_float(row.rep_dicom_path)
        except Exception as e:
            raise RuntimeError(
                f"Failed to decode DICOM for sample_id={row.sample_id} rep_dicom_path={row.rep_dicom_path}"
            ) from e
        v1, v2 = self.augment(dicom.pixels)
        return {
            "v1": v1,
            "v2": v2,
            "sample_id": row.sample_id,
            "rep_dicom_path": str(row.rep_dicom_path),
        }
