"""
OCT dataset loading utilities for Refracto AI.

Supports:
- Flat split structure: root/train/<CLASS>, root/val/<CLASS>, root/test/<CLASS>
- Nested OCT2017 structure: root/OCT2017/train/<CLASS>, ...
- Multiple dataset roots with duplicate filename filtering
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import logging
from pathlib import Path
import random
from typing import Iterable, Sequence

from PIL import Image
import torch
from torch.utils.data import Dataset, WeightedRandomSampler

logger = logging.getLogger(__name__)

OCT_CLASSES: tuple[str, ...] = ("CNV", "DME", "DRUSEN", "NORMAL")
OCT_CLASS_TO_INDEX: dict[str, int] = {class_name: index for index, class_name in enumerate(OCT_CLASSES)}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@dataclass(frozen=True)
class OCTSample:
    path: Path
    label: int
    class_name: str
    split: str
    source_root: str


class OCTImageDataset(Dataset):
    """PyTorch dataset for OCT image classification."""

    def __init__(self, samples: Sequence[OCTSample], transform=None):
        self.samples = list(samples)
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> dict[str, object]:
        sample = self.samples[index]
        image = Image.open(sample.path).convert("RGB")

        if self.transform is not None:
            image = self.transform(image)

        return {
            "image": image,
            "label": sample.label,
            "class_name": sample.class_name,
            "path": str(sample.path),
            "source_root": sample.source_root,
        }


def resolve_oct_split_dir(root: str | Path, split: str) -> Path | None:
    """Resolve a split directory for a given OCT dataset root."""
    root_path = Path(root)
    candidates = [root_path / split, root_path / "OCT2017" / split]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    return None


def _iter_image_files(directory: Path) -> list[Path]:
    return sorted(
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS and not path.name.startswith(".")
    )


def collect_oct_samples(data_roots: Sequence[str | Path], split: str) -> list[OCTSample]:
    """Collect OCT samples from one or more dataset roots, deduplicating by class and filename."""
    dedupe_keys: set[tuple[str, str]] = set()
    samples: list[OCTSample] = []

    for root in data_roots:
        split_dir = resolve_oct_split_dir(root, split)
        if split_dir is None:
            logger.warning("Split '%s' not found under %s", split, root)
            continue

        for class_name in OCT_CLASSES:
            class_dir = split_dir / class_name
            if not class_dir.exists():
                logger.warning("Class directory missing: %s", class_dir)
                continue

            for image_path in _iter_image_files(class_dir):
                dedupe_key = (class_name, image_path.name.lower())
                if dedupe_key in dedupe_keys:
                    continue

                dedupe_keys.add(dedupe_key)
                samples.append(
                    OCTSample(
                        path=image_path,
                        label=OCT_CLASS_TO_INDEX[class_name],
                        class_name=class_name,
                        split=split,
                        source_root=Path(root).name,
                    )
                )

    return samples


def _class_counts(samples: Sequence[OCTSample]) -> dict[str, int]:
    counts = Counter(sample.class_name for sample in samples)
    return {class_name: counts.get(class_name, 0) for class_name in OCT_CLASSES}


def summarize_samples(samples: Sequence[OCTSample]) -> dict[str, int]:
    summary = _class_counts(samples)
    summary["total"] = len(samples)
    return summary


def has_minimum_samples_per_class(samples: Sequence[OCTSample], minimum: int) -> bool:
    counts = _class_counts(samples)
    return all(counts[class_name] >= minimum for class_name in OCT_CLASSES)


def stratified_split_train_val(
    train_samples: Sequence[OCTSample],
    val_split: float,
    seed: int,
) -> tuple[list[OCTSample], list[OCTSample]]:
    """Create a stratified validation split from the training pool."""
    grouped: dict[int, list[OCTSample]] = defaultdict(list)
    rng = random.Random(seed)

    for sample in train_samples:
        grouped[sample.label].append(sample)

    split_train: list[OCTSample] = []
    split_val: list[OCTSample] = []

    for label, class_samples in grouped.items():
        shuffled = list(class_samples)
        rng.shuffle(shuffled)

        if len(shuffled) < 2:
            split_train.extend(shuffled)
            continue

        val_count = max(1, int(len(shuffled) * val_split))
        val_count = min(val_count, len(shuffled) - 1)

        split_val.extend(shuffled[:val_count])
        split_train.extend(shuffled[val_count:])

        logger.info(
            "Derived validation split for %s: train=%s val=%s",
            OCT_CLASSES[label],
            len(shuffled) - val_count,
            val_count,
        )

    return split_train, split_val


def build_oct_splits(
    data_roots: Sequence[str | Path],
    val_split: float = 0.15,
    seed: int = 42,
    use_existing_val: bool = False,
    min_existing_val_per_class: int = 50,
) -> dict[str, list[OCTSample]]:
    """Build train/val/test splits from the supplied OCT dataset roots."""
    train_samples = collect_oct_samples(data_roots, "train")
    existing_val_samples = collect_oct_samples(data_roots, "val")
    test_samples = collect_oct_samples(data_roots, "test")

    if not train_samples:
        raise FileNotFoundError("No OCT training samples were found in the provided dataset roots.")

    if use_existing_val and has_minimum_samples_per_class(existing_val_samples, min_existing_val_per_class):
        val_samples = existing_val_samples
        logger.info("Using existing validation split from dataset roots.")
    else:
        if existing_val_samples:
            logger.warning(
                "Ignoring existing validation split because it is too small or disabled. Summary: %s",
                summarize_samples(existing_val_samples),
            )
        train_samples, val_samples = stratified_split_train_val(train_samples, val_split=val_split, seed=seed)

    return {
        "train": list(train_samples),
        "val": list(val_samples),
        "test": list(test_samples),
    }


def compute_class_weights(samples: Sequence[OCTSample]) -> dict[int, float]:
    """Compute inverse-frequency class weights for loss rebalancing."""
    label_counts = Counter(sample.label for sample in samples)
    num_classes = len(OCT_CLASSES)
    total = sum(label_counts.values())

    return {
        label: total / (num_classes * count)
        for label, count in label_counts.items()
        if count > 0
    }


def create_weighted_sampler(samples: Sequence[OCTSample]) -> WeightedRandomSampler:
    """Create a weighted sampler to reduce class imbalance during training."""
    class_weights = compute_class_weights(samples)
    sample_weights = [class_weights[sample.label] for sample in samples]

    return WeightedRandomSampler(
        weights=torch.tensor(sample_weights, dtype=torch.double),
        num_samples=len(sample_weights),
        replacement=True,
    )


def samples_to_manifest(samples: Iterable[OCTSample]) -> list[dict[str, object]]:
    """Convert samples into a JSON-serializable manifest for logging."""
    return [
        {
            "path": str(sample.path),
            "label": sample.label,
            "class_name": sample.class_name,
            "split": sample.split,
            "source_root": sample.source_root,
        }
        for sample in samples
    ]