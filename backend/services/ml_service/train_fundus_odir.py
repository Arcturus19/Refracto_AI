"""Train a fundus multi-label classifier using the ODIR-5K dataset (from archive.zip).

This script is designed to work in constrained disk environments:
- Reads labels from full_df.csv inside the zip
- Reads images directly from the zip without extracting the full dataset

Labels are the 8 ODIR classes: N, D, G, C, A, H, M, O.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import time
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import timm
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from tqdm import tqdm


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


ODIR_LABELS = ["N", "D", "G", "C", "A", "H", "M", "O"]


@dataclass(frozen=True)
class Sample:
    zip_entry: str
    filename: str
    labels: np.ndarray  # shape (8,)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def get_transforms(img_size: int) -> tuple[transforms.Compose, transforms.Compose]:
    train_transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.RandomApply([
            transforms.ColorJitter(brightness=0.10, contrast=0.10, saturation=0.05)
        ], p=0.25),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    eval_transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    return train_transform, eval_transform


class ODIRZipDataset(Dataset):
    def __init__(self, zip_path: Path, samples: list[Sample], transform: transforms.Compose):
        self.zip_path = zip_path
        self.samples = samples
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict[str, object]:
        sample = self.samples[idx]
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            data = zf.read(sample.zip_entry)

        image = Image.open(BytesIO(data)).convert("RGB")
        image_tensor = self.transform(image)
        label_tensor = torch.from_numpy(sample.labels.astype(np.float32))
        return {
            "image": image_tensor,
            "labels": label_tensor,
            "filename": sample.filename,
        }


def build_zip_index(zip_path: Path) -> dict[str, str]:
    """Map image basename -> zip entry path."""
    index: dict[str, str] = {}
    with zipfile.ZipFile(zip_path, "r") as zf:
        for entry in zf.infolist():
            if entry.is_dir():
                continue
            name = entry.filename
            lower = name.lower()
            if not (lower.endswith(".jpg") or lower.endswith(".jpeg") or lower.endswith(".png")):
                continue
            base = Path(name).name
            # Prefer "Training Images" entries if duplicates exist.
            if base not in index:
                index[base] = name
            else:
                if "training images" in lower and "training images" not in index[base].lower():
                    index[base] = name
    return index


def load_odir_samples(zip_path: Path, csv_entry: str) -> tuple[list[Sample], dict[str, object]]:
    """Load samples from full_df.csv inside zip, resolving each row to a zip image entry."""
    zip_index = build_zip_index(zip_path)
    logger.info("Indexed %s images inside %s", len(zip_index), zip_path)

    with zipfile.ZipFile(zip_path, "r") as zf:
        with zf.open(csv_entry) as fp:
            df = pd.read_csv(fp)

    missing_images = 0
    samples: list[Sample] = []
    for _, row in df.iterrows():
        filename = str(row.get("filename", "")).strip()
        if not filename:
            continue
        zip_entry = zip_index.get(filename)
        if not zip_entry:
            missing_images += 1
            continue

        labels = np.array([int(row.get(label, 0)) for label in ODIR_LABELS], dtype=np.int64)
        samples.append(Sample(zip_entry=zip_entry, filename=filename, labels=labels))

    dataset_info = {
        "total_rows_in_csv": int(len(df)),
        "resolved_samples": int(len(samples)),
        "missing_images": int(missing_images),
        "labels": ODIR_LABELS,
    }
    return samples, dataset_info


def split_samples(samples: list[Sample], val_ratio: float, test_ratio: float, seed: int) -> tuple[list[Sample], list[Sample], list[Sample]]:
    indices = list(range(len(samples)))
    rng = random.Random(seed)
    rng.shuffle(indices)

    n_total = len(indices)
    n_test = int(round(n_total * test_ratio))
    n_val = int(round(n_total * val_ratio))
    n_train = max(0, n_total - n_val - n_test)

    train_idx = indices[:n_train]
    val_idx = indices[n_train:n_train + n_val]
    test_idx = indices[n_train + n_val:]

    train_samples = [samples[i] for i in train_idx]
    val_samples = [samples[i] for i in val_idx]
    test_samples = [samples[i] for i in test_idx]
    return train_samples, val_samples, test_samples


def compute_pos_weight(train_samples: list[Sample]) -> torch.Tensor:
    y = np.stack([s.labels for s in train_samples], axis=0)  # (N, 8)
    positives = y.sum(axis=0).astype(np.float64)
    negatives = (y.shape[0] - positives).astype(np.float64)
    # pos_weight = neg / pos for BCEWithLogitsLoss
    pos_weight = np.ones_like(positives)
    for i in range(len(positives)):
        if positives[i] > 0:
            pos_weight[i] = negatives[i] / positives[i]
        else:
            pos_weight[i] = 1.0
    return torch.tensor(pos_weight, dtype=torch.float32)


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def multilabel_metrics(y_true: np.ndarray, y_logits: np.ndarray, threshold: float = 0.5) -> dict[str, object]:
    """Compute micro/macro precision/recall/F1 and exact match ratio."""
    y_prob = sigmoid(y_logits)
    y_pred = (y_prob >= threshold).astype(np.int64)

    tp = (y_pred * y_true).sum(axis=0).astype(np.float64)
    fp = (y_pred * (1 - y_true)).sum(axis=0).astype(np.float64)
    fn = ((1 - y_pred) * y_true).sum(axis=0).astype(np.float64)

    per_class = {}
    f1s = []
    precisions = []
    recalls = []
    for i, label in enumerate(ODIR_LABELS):
        precision = float(tp[i] / (tp[i] + fp[i])) if (tp[i] + fp[i]) else 0.0
        recall = float(tp[i] / (tp[i] + fn[i])) if (tp[i] + fn[i]) else 0.0
        f1 = float((2 * precision * recall) / (precision + recall)) if (precision + recall) else 0.0
        support = int(y_true[:, i].sum())
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }
        f1s.append(f1)
        precisions.append(precision)
        recalls.append(recall)

    macro_f1 = float(sum(f1s) / len(f1s)) if f1s else 0.0
    macro_precision = float(sum(precisions) / len(precisions)) if precisions else 0.0
    macro_recall = float(sum(recalls) / len(recalls)) if recalls else 0.0

    micro_tp = float(tp.sum())
    micro_fp = float(fp.sum())
    micro_fn = float(fn.sum())
    micro_precision = micro_tp / (micro_tp + micro_fp) if (micro_tp + micro_fp) else 0.0
    micro_recall = micro_tp / (micro_tp + micro_fn) if (micro_tp + micro_fn) else 0.0
    micro_f1 = (2 * micro_precision * micro_recall) / (micro_precision + micro_recall) if (micro_precision + micro_recall) else 0.0

    exact_match = float((y_pred == y_true).all(axis=1).mean()) if y_true.size else 0.0

    return {
        "exact_match_ratio": exact_match,
        "micro": {
            "precision": float(micro_precision),
            "recall": float(micro_recall),
            "f1": float(micro_f1),
        },
        "macro": {
            "precision": macro_precision,
            "recall": macro_recall,
            "f1": macro_f1,
        },
        "per_class": per_class,
    }


def run_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    optimizer: optim.Optimizer | None,
) -> tuple[float, dict[str, object]]:
    train_mode = optimizer is not None
    model.train(train_mode)

    total_loss = 0.0
    all_logits: list[np.ndarray] = []
    all_true: list[np.ndarray] = []

    pbar = tqdm(dataloader, desc="Train" if train_mode else "Eval")
    for batch in pbar:
        images = batch["image"].to(device)
        labels = batch["labels"].to(device)

        if train_mode:
            optimizer.zero_grad(set_to_none=True)

        logits = model(images)
        loss = criterion(logits, labels)

        if train_mode:
            loss.backward()
            optimizer.step()

        batch_size = int(images.size(0))
        total_loss += float(loss.item()) * batch_size
        all_logits.append(logits.detach().cpu().numpy())
        all_true.append(labels.detach().cpu().numpy().astype(np.int64))
        pbar.set_postfix({"loss": float(loss.item())})

    avg_loss = total_loss / max(1, len(dataloader.dataset))
    y_logits = np.concatenate(all_logits, axis=0) if all_logits else np.zeros((0, len(ODIR_LABELS)))
    y_true = np.concatenate(all_true, axis=0) if all_true else np.zeros((0, len(ODIR_LABELS)), dtype=np.int64)
    metrics = multilabel_metrics(y_true=y_true, y_logits=y_logits)
    metrics["loss"] = float(avg_loss)
    return float(avg_loss), metrics


def write_manifest_csv(path: Path, split_name: str, samples: list[Sample]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["split", "filename", "zip_entry", *ODIR_LABELS])
        writer.writeheader()
        for sample in samples:
            row = {
                "split": split_name,
                "filename": sample.filename,
                "zip_entry": sample.zip_entry,
            }
            for i, label in enumerate(ODIR_LABELS):
                row[label] = int(sample.labels[i])
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ODIR-5K fundus multi-label classifier")
    parser.add_argument("--zip-path", type=str, required=True, help="Path to ODIR archive.zip")
    parser.add_argument("--labels-csv", type=str, default="full_df.csv", help="CSV entry name inside the zip")
    parser.add_argument("--model", type=str, default="efficientnet_b0", help="timm model name")
    parser.add_argument("--img-size", type=int, default=224, help="Input image size")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning rate")
    parser.add_argument("--weight-decay", type=float, default=1e-4, help="Weight decay")
    parser.add_argument("--val-ratio", type=float, default=0.10, help="Validation ratio")
    parser.add_argument("--test-ratio", type=float, default=0.10, help="Test ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--patience", type=int, default=3, help="Early stopping patience (macro F1)")
    parser.add_argument("--workers", type=int, default=0, help="DataLoader workers (use 0 on Windows)")
    parser.add_argument("--model-dir", type=str, default="../../models/fundus_odir", help="Directory to save checkpoints and logs")
    parser.add_argument("--resume", type=str, default=None, help="Optional checkpoint (.pt) to resume from")
    parser.add_argument("--dry-run", action="store_true", help="Run a quick 1-batch smoke test")
    args = parser.parse_args()

    zip_path = Path(args.zip_path).resolve()
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip not found: {zip_path}")

    model_dir = Path(args.model_dir).resolve()
    model_dir.mkdir(parents=True, exist_ok=True)
    best_path = model_dir / "fundus_odir_best.pt"
    last_path = model_dir / "fundus_odir_last.pt"
    log_path = model_dir / "training_log.json"
    manifest_path = model_dir / "dataset_manifest.csv"

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Using device: %s", device)

    samples, dataset_info = load_odir_samples(zip_path=zip_path, csv_entry=args.labels_csv)
    if not samples:
        raise RuntimeError("No samples were resolved from the zip + labels CSV")

    train_samples, val_samples, test_samples = split_samples(samples, val_ratio=args.val_ratio, test_ratio=args.test_ratio, seed=args.seed)
    dataset_info.update({
        "train": len(train_samples),
        "val": len(val_samples),
        "test": len(test_samples),
    })
    logger.info("Split sizes: train=%s val=%s test=%s", len(train_samples), len(val_samples), len(test_samples))

    # Save a manifest so the split is reproducible.
    write_manifest_csv(manifest_path, "train", train_samples)
    write_manifest_csv(manifest_path.with_name("dataset_manifest_val.csv"), "val", val_samples)
    write_manifest_csv(manifest_path.with_name("dataset_manifest_test.csv"), "test", test_samples)

    train_tf, eval_tf = get_transforms(args.img_size)
    train_ds = ODIRZipDataset(zip_path=zip_path, samples=train_samples, transform=train_tf)
    val_ds = ODIRZipDataset(zip_path=zip_path, samples=val_samples, transform=eval_tf)
    test_ds = ODIRZipDataset(zip_path=zip_path, samples=test_samples, transform=eval_tf)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.workers)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)

    model = timm.create_model(args.model, pretrained=True, num_classes=len(ODIR_LABELS))
    model = model.to(device)

    pos_weight = compute_pos_weight(train_samples).to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)

    start_epoch = 0
    best_macro_f1 = -1.0
    history: list[dict[str, object]] = []
    if args.resume:
        ckpt = torch.load(Path(args.resume).resolve(), map_location=device)
        model.load_state_dict(ckpt["state_dict"])
        optimizer.load_state_dict(ckpt.get("optimizer", optimizer.state_dict()))
        start_epoch = int(ckpt.get("epoch", 0))
        best_macro_f1 = float(ckpt.get("best_macro_f1", best_macro_f1))
        logger.info("Resumed from %s (start_epoch=%s best_macro_f1=%s)", args.resume, start_epoch, best_macro_f1)

    start_time = time.time()
    epochs_without_improvement = 0

    if args.dry_run:
        logger.info("Dry-run enabled: running 1 batch train + 1 batch val")
        _ = next(iter(train_loader))
        _ = next(iter(val_loader))
        logger.info("Dry-run OK")
        return

    for epoch in range(start_epoch, args.epochs):
        logger.info("Epoch %s/%s", epoch + 1, args.epochs)

        train_loss, train_metrics = run_epoch(model, train_loader, criterion, device, optimizer)
        val_loss, val_metrics = run_epoch(model, val_loader, criterion, device, optimizer=None)

        val_macro_f1 = float(val_metrics["macro"]["f1"])  # type: ignore[index]
        scheduler.step(val_macro_f1)

        lr = float(optimizer.param_groups[0]["lr"])
        logger.info(
            "Train loss=%.4f macro_f1=%.4f | Val loss=%.4f macro_f1=%.4f (lr=%.6f)",
            train_loss,
            float(train_metrics["macro"]["f1"]),  # type: ignore[index]
            val_loss,
            val_macro_f1,
            lr,
        )

        record = {
            "epoch": epoch + 1,
            "train": train_metrics,
            "val": val_metrics,
            "lr": lr,
        }
        history.append(record)

        improved = val_macro_f1 > best_macro_f1
        if improved:
            best_macro_f1 = val_macro_f1
            epochs_without_improvement = 0
            torch.save({
                "state_dict": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "epoch": epoch + 1,
                "best_macro_f1": best_macro_f1,
                "model": args.model,
                "img_size": args.img_size,
                "labels": ODIR_LABELS,
            }, best_path)
            logger.info("Saved best checkpoint to %s", best_path)
        else:
            epochs_without_improvement += 1

        torch.save({
            "state_dict": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "epoch": epoch + 1,
            "best_macro_f1": best_macro_f1,
            "model": args.model,
            "img_size": args.img_size,
            "labels": ODIR_LABELS,
        }, last_path)

        if epochs_without_improvement >= args.patience:
            logger.info("Early stopping triggered (no improvement for %s epochs)", args.patience)
            break

        payload = {
            "model": args.model,
            "img_size": args.img_size,
            "device": str(device),
            "labels": ODIR_LABELS,
            "pos_weight": [float(v) for v in pos_weight.detach().cpu().numpy().tolist()],
            "dataset": dataset_info,
            "best_val_macro_f1": best_macro_f1,
            "epochs_ran": len(history),
            "elapsed_seconds": float(time.time() - start_time),
            "history": history,
        }
        log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Final test evaluation using best checkpoint if present
    if best_path.exists():
        ckpt = torch.load(best_path, map_location=device)
        model.load_state_dict(ckpt["state_dict"])
        logger.info("Loaded best checkpoint for test evaluation")

    _, test_metrics = run_epoch(model, test_loader, criterion, device, optimizer=None)

    final_payload = {
        "model": args.model,
        "img_size": args.img_size,
        "device": str(device),
        "labels": ODIR_LABELS,
        "pos_weight": [float(v) for v in pos_weight.detach().cpu().numpy().tolist()],
        "dataset": dataset_info,
        "best_val_macro_f1": best_macro_f1,
        "test": test_metrics,
        "epochs_ran": len(history),
        "elapsed_seconds": float(time.time() - start_time),
        "history": history,
    }
    log_path.write_text(json.dumps(final_payload, indent=2), encoding="utf-8")
    logger.info("Training finished. Log written to %s", log_path)
    logger.info("Best checkpoint: %s", best_path)


if __name__ == "__main__":
    main()
