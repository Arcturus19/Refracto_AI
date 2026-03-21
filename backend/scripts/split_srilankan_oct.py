"""Split and organize Sri Lankan OCT DICOM dataset.

This dataset is laid out as:
  <root>/DataFiles/E000/*.DCM
  <root>/DataFiles/E001/*.DCM
  ...

We treat each E### directory as one sample (likely one study/series bundle).
The script creates train/val/test splits of E### directories with fixed counts.

Default behavior is *non-destructive*: create directory junctions (Windows) in
an output folder, so no data is duplicated.

Example:
  python backend/scripts/split_srilankan_oct.py \
    --datafiles "backend/data/Srilankan_OCT/DataFiles" \
    --out "backend/data/Srilankan_OCT_SPLIT" \
    --train 50 --val 20 --seed 42 --mode junction --overwrite

"""

from __future__ import annotations

import argparse
import csv
import os
import platform
import random
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Literal


SplitMode = Literal["junction", "copy", "move"]


@dataclass(frozen=True)
class Sample:
    sample_id: str
    src_dir: Path
    file_count: int
    total_bytes: int


def _iter_sample_dirs(datafiles_dir: Path) -> Iterable[Path]:
    for entry in sorted(datafiles_dir.iterdir(), key=lambda p: p.name):
        if not entry.is_dir():
            continue
        # Keep it simple: accept E### style folders.
        if entry.name and entry.name[0].upper() == "E":
            yield entry


def _summarize_dir(dir_path: Path) -> tuple[int, int]:
    file_count = 0
    total_bytes = 0
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            file_count += 1
            try:
                total_bytes += file_path.stat().st_size
            except OSError:
                pass
    return file_count, total_bytes


def _create_junction_windows(dest: Path, src: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        raise FileExistsError(str(dest))

    # Use cmd mklink /J which does not require admin.
    # mklink syntax: mklink /J <Link> <Target>
    completed = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(dest), str(src)],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Failed to create junction: {dest} -> {src}\n"
            f"stdout: {completed.stdout}\n"
            f"stderr: {completed.stderr}"
        )


def _materialize(dest: Path, src: Path, mode: SplitMode) -> None:
    if mode == "junction":
        if platform.system().lower() != "windows":
            raise RuntimeError("mode=junction is only supported on Windows")
        _create_junction_windows(dest, src)
        return

    if mode == "copy":
        shutil.copytree(src, dest)
        return

    if mode == "move":
        shutil.move(str(src), str(dest))
        return

    raise ValueError(f"Unknown mode: {mode}")


def _remove_existing(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return

    if path.is_symlink():
        path.unlink()
        return

    if path.is_dir():
        shutil.rmtree(path)
        return

    path.unlink()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split Sri Lankan OCT DICOM dataset")
    parser.add_argument(
        "--datafiles",
        type=Path,
        required=True,
        help="Path to DataFiles directory (contains E### folders)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output directory to create train/val/test folders in",
    )
    parser.add_argument("--train", type=int, default=50)
    parser.add_argument("--val", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--mode",
        choices=["junction", "copy", "move"],
        default="junction",
        help="How to organize: junction (default, Windows only, no duplication), copy, or move",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output directories/links",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without creating any output",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    datafiles_dir: Path = args.datafiles
    out_dir: Path = args.out
    train_n: int = args.train
    val_n: int = args.val
    seed: int = args.seed
    mode: SplitMode = args.mode

    if not datafiles_dir.exists() or not datafiles_dir.is_dir():
        print(f"ERROR: --datafiles not found or not a directory: {datafiles_dir}")
        return 2

    sample_dirs = list(_iter_sample_dirs(datafiles_dir))
    if not sample_dirs:
        print(f"ERROR: no sample directories found under {datafiles_dir}")
        return 2

    total = len(sample_dirs)
    if train_n + val_n > total:
        print(
            f"ERROR: requested train+val ({train_n + val_n}) exceeds total samples ({total})"
        )
        return 2

    rng = random.Random(seed)
    rng.shuffle(sample_dirs)

    train_dirs = sample_dirs[:train_n]
    val_dirs = sample_dirs[train_n : train_n + val_n]
    test_dirs = sample_dirs[train_n + val_n :]

    # Precompute summaries for manifest.
    samples: dict[str, Sample] = {}
    for d in sample_dirs:
        file_count, total_bytes = _summarize_dir(d)
        samples[d.name] = Sample(
            sample_id=d.name,
            src_dir=d,
            file_count=file_count,
            total_bytes=total_bytes,
        )

    out_train = out_dir / "train"
    out_val = out_dir / "val"
    out_test = out_dir / "test"

    manifest_path = out_dir / "splits_manifest.csv"

    if args.dry_run:
        print(f"Total samples: {total}")
        print(f"Train: {len(train_dirs)}  Val: {len(val_dirs)}  Test: {len(test_dirs)}")
        print(f"Mode: {mode}")
        print(f"Out: {out_dir}")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    for split_dir in (out_train, out_val, out_test):
        split_dir.mkdir(parents=True, exist_ok=True)

    # Create outputs.
    def handle_split(split_name: str, dirs: list[Path], split_root: Path) -> None:
        for src in dirs:
            dest = split_root / src.name
            if dest.exists() or dest.is_symlink():
                if args.overwrite:
                    _remove_existing(dest)
                else:
                    raise FileExistsError(
                        f"Destination already exists: {dest} (use --overwrite)"
                    )
            _materialize(dest, src, mode)

    handle_split("train", train_dirs, out_train)
    handle_split("val", val_dirs, out_val)
    handle_split("test", test_dirs, out_test)

    # Write manifest.
    now = datetime.now().isoformat(timespec="seconds")
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "sample_id",
                "split",
                "src_dir",
                "dst_dir",
                "file_count",
                "total_bytes",
                "seed",
                "created_at",
                "mode",
            ],
        )
        writer.writeheader()

        for split, split_root, dirs in (
            ("train", out_train, train_dirs),
            ("val", out_val, val_dirs),
            ("test", out_test, test_dirs),
        ):
            for src in dirs:
                s = samples[src.name]
                writer.writerow(
                    {
                        "sample_id": s.sample_id,
                        "split": split,
                        "src_dir": str(s.src_dir),
                        "dst_dir": str((split_root / s.sample_id).resolve()),
                        "file_count": s.file_count,
                        "total_bytes": s.total_bytes,
                        "seed": seed,
                        "created_at": now,
                        "mode": mode,
                    }
                )

    print(f"OK: created splits under: {out_dir}")
    print(f"- Train: {len(train_dirs)}")
    print(f"- Val:   {len(val_dirs)}")
    print(f"- Test:  {len(test_dirs)}")
    print(f"Manifest: {manifest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
