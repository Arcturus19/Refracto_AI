"""Compute embeddings + anomaly scores for Sri Lankan OCT DICOM split.

Uses the pretrained SSL encoder (ResNet18 backbone) and fits an anomaly model
on TRAIN embeddings, then scores val/test.

Outputs:
  backend/models/srilankan_oct_ssl/
    embeddings_train.csv
    embeddings_val.csv
    embeddings_test.csv
    anomaly_scores.csv

Anomaly scoring methods:
- Mahalanobis distance on encoder features

Run:
  python backend/services/ml_service/score_srilankan_oct_anomaly.py

"""

from __future__ import annotations

import argparse
import csv
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision.models import resnet18

from ml_service.core.oct_ssl.dicom_io import read_dicom_as_unit_float, resize_nearest
from ml_service.core.oct_ssl.ssl_dataset import load_manifest_csv


class Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        base = resnet18(weights=None)
        base.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        feat_dim = base.fc.in_features
        base.fc = nn.Identity()
        self.net = base
        self.feat_dim = feat_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class ManifestEmbedDataset(Dataset):
    def __init__(self, manifest_csv: Path, image_size: int = 224):
        self.rows = load_manifest_csv(manifest_csv)
        self.image_size = image_size

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int):
        r = self.rows[idx]
        dicom = read_dicom_as_unit_float(r.rep_dicom_path)
        img = resize_nearest(dicom.pixels, (self.image_size, self.image_size))
        t = torch.from_numpy(img.astype(np.float32)).unsqueeze(0)
        return {
            "x": t,
            "sample_id": r.sample_id,
            "split": r.split,
            "rep_dicom_path": str(r.rep_dicom_path),
        }


@dataclass
class ScoreConfig:
    split_root: Path
    model_dir: Path
    ckpt: Path
    image_size: int
    batch_size: int
    num_workers: int


def parse_args(argv: list[str]) -> ScoreConfig:
    p = argparse.ArgumentParser(description="Score anomaly on Sri Lankan OCT")
    p.add_argument(
        "--split-root",
        type=Path,
        default=Path("backend/data/Srilankan_OCT_SPLIT"),
    )
    p.add_argument(
        "--model-dir",
        type=Path,
        default=Path("backend/models/srilankan_oct_ssl"),
    )
    p.add_argument(
        "--ckpt",
        type=Path,
        default=Path("backend/models/srilankan_oct_ssl/ssl_best.pt"),
    )
    p.add_argument("--image-size", type=int, default=224)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--num-workers", type=int, default=0)
    args = p.parse_args(argv)

    return ScoreConfig(
        split_root=args.split_root,
        model_dir=args.model_dir,
        ckpt=args.ckpt,
        image_size=args.image_size,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
    )


@torch.no_grad()
def embed_split(
    encoder: Encoder,
    manifest_csv: Path,
    device: torch.device,
    image_size: int,
    batch_size: int,
    num_workers: int,
) -> tuple[list[dict], np.ndarray]:
    ds = ManifestEmbedDataset(manifest_csv, image_size=image_size)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    meta: list[dict] = []
    embs: list[np.ndarray] = []

    encoder.eval()
    for batch in loader:
        x = batch["x"].to(device)
        feats = encoder(x).cpu().numpy().astype(np.float32)
        embs.append(feats)

        bsz = feats.shape[0]
        for i in range(bsz):
            meta.append(
                {
                    "sample_id": batch["sample_id"][i],
                    "split": batch["split"][i],
                    "rep_dicom_path": batch["rep_dicom_path"][i],
                }
            )

    return meta, np.concatenate(embs, axis=0)


def _write_embeddings_csv(path: Path, meta: list[dict], emb: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["sample_id", "split", "rep_dicom_path"] + [f"f{i}" for i in range(emb.shape[1])]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m, v in zip(meta, emb):
            row = dict(m)
            for i, val in enumerate(v.tolist()):
                row[f"f{i}"] = f"{val:.6f}"
            writer.writerow(row)


def _fit_mahalanobis(train_emb: np.ndarray):
    mu = train_emb.mean(axis=0)
    x = train_emb - mu
    # shrinkage for stability
    cov = (x.T @ x) / max(1, x.shape[0] - 1)
    eps = 1e-3
    cov = cov + np.eye(cov.shape[0]) * eps
    inv = np.linalg.inv(cov)
    return mu.astype(np.float32), inv.astype(np.float32)


def _mahalanobis_scores(emb: np.ndarray, mu: np.ndarray, inv: np.ndarray) -> np.ndarray:
    x = emb - mu
    # sqrt((x^T inv x))
    # vectorized: (x @ inv) * x summed over dims
    q = (x @ inv) * x
    d2 = q.sum(axis=1)
    return np.sqrt(np.maximum(d2, 0.0)).astype(np.float32)


def main(argv: list[str]) -> int:
    cfg = parse_args(argv)

    if not cfg.ckpt.exists():
        print(f"ERROR: checkpoint not found: {cfg.ckpt}")
        print("Run SSL training first: python backend/services/ml_service/train_srilankan_oct_ssl.py")
        return 2

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Our checkpoints are produced locally by this repo; load full object.
    # Newer PyTorch defaults to weights_only=True; older versions may not
    # support the argument at all.
    try:
        ckpt = torch.load(cfg.ckpt, map_location="cpu", weights_only=False)
    except TypeError:
        ckpt = torch.load(cfg.ckpt, map_location="cpu")

    encoder = Encoder()
    # Load weights from SimCLR checkpoint by matching key prefix "encoder."
    state = ckpt.get("model", {})
    enc_state = {k.replace("encoder.", ""): v for k, v in state.items() if k.startswith("encoder.")}
    missing, unexpected = encoder.net.load_state_dict(enc_state, strict=False)
    if unexpected:
        print(f"WARN: unexpected keys: {len(unexpected)}")
    if missing:
        print(f"WARN: missing keys: {len(missing)}")

    encoder = encoder.to(device)

    train_csv = cfg.split_root / "train_manifest.csv"
    val_csv = cfg.split_root / "val_manifest.csv"
    test_csv = cfg.split_root / "test_manifest.csv"

    for p in (train_csv, val_csv, test_csv):
        if not p.exists():
            print(f"ERROR: missing manifest: {p}")
            return 2

    meta_train, emb_train = embed_split(
        encoder,
        train_csv,
        device=device,
        image_size=cfg.image_size,
        batch_size=cfg.batch_size,
        num_workers=cfg.num_workers,
    )
    meta_val, emb_val = embed_split(
        encoder,
        val_csv,
        device=device,
        image_size=cfg.image_size,
        batch_size=cfg.batch_size,
        num_workers=cfg.num_workers,
    )
    meta_test, emb_test = embed_split(
        encoder,
        test_csv,
        device=device,
        image_size=cfg.image_size,
        batch_size=cfg.batch_size,
        num_workers=cfg.num_workers,
    )

    _write_embeddings_csv(cfg.model_dir / "embeddings_train.csv", meta_train, emb_train)
    _write_embeddings_csv(cfg.model_dir / "embeddings_val.csv", meta_val, emb_val)
    _write_embeddings_csv(cfg.model_dir / "embeddings_test.csv", meta_test, emb_test)

    mu, inv = _fit_mahalanobis(emb_train)

    s_train = _mahalanobis_scores(emb_train, mu, inv)
    s_val = _mahalanobis_scores(emb_val, mu, inv)
    s_test = _mahalanobis_scores(emb_test, mu, inv)

    out_scores = cfg.model_dir / "anomaly_scores.csv"
    with out_scores.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["sample_id", "split", "rep_dicom_path", "anomaly_score"],
        )
        writer.writeheader()
        for m, s in zip(meta_train, s_train.tolist()):
            writer.writerow({**m, "anomaly_score": f"{s:.6f}"})
        for m, s in zip(meta_val, s_val.tolist()):
            writer.writerow({**m, "anomaly_score": f"{s:.6f}"})
        for m, s in zip(meta_test, s_test.tolist()):
            writer.writerow({**m, "anomaly_score": f"{s:.6f}"})

    print(f"OK: wrote {out_scores}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(os.sys.argv[1:])))
