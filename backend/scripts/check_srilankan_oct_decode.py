"""Quickly check how many manifest DICOMs are decodable by pydicom.

Usage:
  python backend/scripts/check_srilankan_oct_decode.py --split train --limit 50

"""

from __future__ import annotations

import argparse
import csv
import os
from collections import Counter
from pathlib import Path

import pydicom


def _sanitize_photometric(value: object):
    if value is None:
        return None
    if isinstance(value, bytes):
        try:
            value = value.decode(errors="ignore")
        except Exception:
            value = str(value)
    if not isinstance(value, str):
        value = str(value)

    cleaned = "".join(ch for ch in value if ch.isalnum() or ch in {"_", " "}).strip().upper()
    if "MONOCHROME1" in cleaned:
        return "MONOCHROME1"
    if "MONOCHROME2" in cleaned:
        return "MONOCHROME2"
    if cleaned == "RGB" or "RGB" in cleaned:
        return "RGB"
    return None


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--split-root",
        type=Path,
        default=Path("backend/data/Srilankan_OCT_SPLIT"),
    )
    p.add_argument("--split", choices=["train", "val", "test"], default="train")
    p.add_argument("--limit", type=int, default=0, help="0 means no limit")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    manifest = args.split_root / f"{args.split}_manifest.csv"
    if not manifest.exists():
        print(f"ERROR: missing {manifest}")
        return 2

    with manifest.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    bad = 0
    ts_counter: Counter[str] = Counter()
    for r in rows:
        p = Path(r["rep_dicom_path"])
        try:
            ds = pydicom.dcmread(str(p), force=True)
            photometric = _sanitize_photometric(getattr(ds, "PhotometricInterpretation", None))
            if photometric is not None:
                try:
                    ds.PhotometricInterpretation = photometric
                except Exception:
                    pass
            ts = str(getattr(ds.file_meta, "TransferSyntaxUID", "NA"))
            ts_counter[ts] += 1
            _ = ds.pixel_array
        except Exception as e:
            bad += 1
            print(f"BAD {r['sample_id']} {p}")
            print(f"  {type(e).__name__}: {str(e)[:200]}")

    print(f"Checked: {len(rows)}")
    print(f"Bad: {bad}")
    print("TransferSyntaxUID counts:")
    for k, v in ts_counter.most_common():
        print(f"  {k}: {v}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(os.sys.argv[1:])))
