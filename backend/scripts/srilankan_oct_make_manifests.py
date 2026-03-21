"""Create train/val/test manifest CSVs for Sri Lankan OCT DICOM split.

Input split structure (created earlier):
  backend/data/Srilankan_OCT_SPLIT/{train,val,test}/E###/*.DCM

We treat each E### directory as one sample and pick ONE representative DICOM
(default: middle slice) to define the sample.

Outputs:
  <split_root>/train_manifest.csv
  <split_root>/val_manifest.csv
  <split_root>/test_manifest.csv

Each row:
  sample_id,split,study_dir,rep_dicom_path,dicom_count,total_bytes

"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Iterable

import pydicom


def _iter_studies(split_dir: Path) -> Iterable[Path]:
    for entry in sorted(split_dir.iterdir(), key=lambda p: p.name):
        if entry.is_dir():
            yield entry


def _list_dicoms(study_dir: Path) -> list[Path]:
    dicoms: list[Path] = []
    for p in study_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".dcm", ".dicom", ".dc"}:
            if p.name.upper() == "DICOMDIR":
                continue
            dicoms.append(p)
    if not dicoms:
        # Some datasets use .DCM uppercase without suffix detection issues.
        for p in study_dir.rglob("*"):
            if p.is_file() and p.name.lower().endswith(".dcm"):
                dicoms.append(p)
    return sorted(dicoms, key=lambda p: p.name)


def _has_zeiss_private_image_tags(path: Path) -> bool:
    # Zeiss private pixel blobs observed in this dataset.
    candidate_elements = [
        (0x0073, 0x1150),
        (0x0073, 0x1155),
        (0x0073, 0x1160),
        (0x0073, 0x1165),
        (0x0073, 0x1190),
        (0x0073, 0x1245),
        (0x0073, 0x1270),
    ]
    try:
        ds = pydicom.dcmread(str(path), force=True, stop_before_pixels=True)
    except Exception:
        return False
    for tag in candidate_elements:
        if tag in ds:
            try:
                v = ds[tag].value
                if isinstance(v, (bytes, bytearray)) and len(v) >= 4096:
                    return True
            except Exception:
                continue
    return False


def _has_decodable_pixel_array(path: Path) -> bool:
    """Return True if pydicom can decode ds.pixel_array for this file.

    This is used as a fallback when Zeiss private preview tags are absent.
    """

    try:
        ds = pydicom.dcmread(str(path), force=True)
        # Try to sanitize known-bad photometric strings.
        photometric = getattr(ds, "PhotometricInterpretation", None)
        if photometric is not None:
            try:
                if isinstance(photometric, (bytes, bytearray)):
                    photometric = photometric.decode(errors="ignore")
                if not isinstance(photometric, str):
                    photometric = str(photometric)
                cleaned = "".join(ch for ch in photometric if ch.isalnum() or ch in {"_", " "}).strip().upper()
                if "MONOCHROME1" in cleaned:
                    ds.PhotometricInterpretation = "MONOCHROME1"
                elif "MONOCHROME2" in cleaned:
                    ds.PhotometricInterpretation = "MONOCHROME2"
                elif cleaned == "RGB" or "RGB" in cleaned:
                    ds.PhotometricInterpretation = "RGB"
            except Exception:
                pass

        _ = ds.pixel_array
        return True
    except Exception:
        # Common failure mode: bad/unknown photometric; try defaulting to MONOCHROME2.
        try:
            ds = pydicom.dcmread(str(path), force=True)
            ds.PhotometricInterpretation = "MONOCHROME2"
            _ = ds.pixel_array
            return True
        except Exception:
            return False


def _pick_representative(dicom_paths: list[Path]) -> Path:
    if not dicom_paths:
        raise ValueError("No DICOM files")

    # Prefer a file that contains Zeiss private pixel blobs (more reliable than PixelData).
    for p in dicom_paths:
        if _has_zeiss_private_image_tags(p):
            return p

    # Fallback: pick a DICOM that has a decodable standard pixel_array.
    # To keep runtime reasonable, probe a few candidates spread across the study.
    n = len(dicom_paths)
    probe_indices = sorted({0, n // 4, n // 2, (3 * n) // 4, n - 1})
    for i in probe_indices:
        p = dicom_paths[i]
        if _has_decodable_pixel_array(p):
            return p

    # Last resort: scan until we find one decodable.
    for p in dicom_paths:
        if _has_decodable_pixel_array(p):
            return p

    raise ValueError("No decodable representative DICOM found")


def _dir_size_bytes(dir_path: Path) -> int:
    total = 0
    for p in dir_path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total


def _write_manifest(split_root: Path, split: str) -> Path:
    split_dir = split_root / split
    if not split_dir.exists():
        raise FileNotFoundError(str(split_dir))

    out_path = split_root / f"{split}_manifest.csv"
    skipped_path = split_root / f"skipped_{split}.csv"
    included_count = 0
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "sample_id",
                "split",
                "study_dir",
                "rep_dicom_path",
                "dicom_count",
                "total_bytes",
            ],
        )
        writer.writeheader()

        skipped: list[dict] = []

        for study_dir in _iter_studies(split_dir):
            dicoms = _list_dicoms(study_dir)
            if not dicoms:
                # Skip empty studies but keep a record? For now, skip.
                skipped.append({"sample_id": study_dir.name, "reason": "no_dicoms"})
                continue

            try:
                rep = _pick_representative(dicoms)
            except Exception:
                skipped.append({"sample_id": study_dir.name, "reason": "no_decodable_dicom"})
                continue

            writer.writerow(
                {
                    "sample_id": study_dir.name,
                    "split": split,
                    "study_dir": str(study_dir),
                    "rep_dicom_path": str(rep),
                    "dicom_count": len(dicoms),
                    "total_bytes": _dir_size_bytes(study_dir),
                }
            )
            included_count += 1

    # Write skipped report
    with skipped_path.open("w", newline="", encoding="utf-8") as f:
        sw = csv.DictWriter(f, fieldnames=["sample_id", "reason"])
        sw.writeheader()
        sw.writerows(skipped)

    print(f"INFO: split={split} included={included_count} skipped={len(skipped)}")

    return out_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create manifests for Sri Lankan OCT splits")
    parser.add_argument(
        "--split-root",
        type=Path,
        default=Path("backend/data/Srilankan_OCT_SPLIT"),
        help="Root containing train/val/test folders",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    split_root: Path = args.split_root

    if not split_root.exists():
        print(f"ERROR: split root not found: {split_root}")
        return 2

    for split in ("train", "val", "test"):
        out = _write_manifest(split_root, split)
        print(f"OK: wrote {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(os.sys.argv[1:])))
