"""Self-supervised (SimCLR-style) pretraining on Sri Lankan OCT DICOM split.

This is designed to be CPU-friendly by default.

Inputs:
  backend/data/Srilankan_OCT_SPLIT/train_manifest.csv
  backend/data/Srilankan_OCT_SPLIT/val_manifest.csv

Outputs:
  backend/models/srilankan_oct_ssl/
    ssl_best.pt
    ssl_last.pt
    training_log.csv

Run:
  python backend/scripts/srilankan_oct_make_manifests.py
  python backend/services/ml_service/train_srilankan_oct_ssl.py --epochs 50

"""

from __future__ import annotations

import argparse
import csv
import math
import os
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision.models import resnet18

from ml_service.core.oct_ssl.ssl_dataset import OctSslDataset, load_manifest_csv


class ProjectionHead(nn.Module):
    def __init__(self, in_dim: int, proj_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, in_dim),
            nn.ReLU(inplace=True),
            nn.Linear(in_dim, proj_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class SimClrModel(nn.Module):
    def __init__(self, proj_dim: int = 128):
        super().__init__()
        base = resnet18(weights=None)
        # Adapt first conv for 1-channel input
        base.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        feat_dim = base.fc.in_features
        base.fc = nn.Identity()

        self.encoder = base
        self.proj = ProjectionHead(feat_dim, proj_dim=proj_dim)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        feats = self.encoder(x)
        z = self.proj(feats)
        z = F.normalize(z, dim=1)
        return feats, z


def nt_xent_loss(z1: torch.Tensor, z2: torch.Tensor, temperature: float) -> torch.Tensor:
    """NT-Xent for SimCLR.

    z1,z2: (B, D) normalized.
    """

    bsz = z1.shape[0]
    z = torch.cat([z1, z2], dim=0)  # (2B, D)

    sim = torch.matmul(z, z.T) / temperature  # (2B,2B)
    # Mask self-similarity
    mask = torch.eye(2 * bsz, dtype=torch.bool, device=z.device)
    sim = sim.masked_fill(mask, -1e9)

    # Positives: i<->i+B
    pos = torch.cat([torch.diag(sim, bsz), torch.diag(sim, -bsz)], dim=0)

    # Denominator: logsumexp over all except self
    loss = -pos + torch.logsumexp(sim, dim=1)
    return loss.mean()


@dataclass
class TrainConfig:
    train_manifest: Path
    val_manifest: Path
    out_dir: Path
    epochs: int
    batch_size: int
    lr: float
    weight_decay: float
    temperature: float
    proj_dim: int
    num_workers: int
    seed: int
    image_size: int


def parse_args(argv: list[str]) -> TrainConfig:
    p = argparse.ArgumentParser(description="SSL pretraining for Sri Lankan OCT")
    p.add_argument(
        "--split-root",
        type=Path,
        default=Path("backend/data/Srilankan_OCT_SPLIT"),
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("backend/models/srilankan_oct_ssl"),
    )
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--proj-dim", type=int, default=128)
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--image-size", type=int, default=224)
    args = p.parse_args(argv)

    return TrainConfig(
        train_manifest=args.split_root / "train_manifest.csv",
        val_manifest=args.split_root / "val_manifest.csv",
        out_dir=args.out_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        weight_decay=args.weight_decay,
        temperature=args.temperature,
        proj_dim=args.proj_dim,
        num_workers=args.num_workers,
        seed=args.seed,
        image_size=args.image_size,
    )


def _seed_all(seed: int) -> None:
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def _make_loader(
    manifest_csv: Path,
    batch_size: int,
    num_workers: int,
    seed: int,
    image_size: int,
    drop_last: bool,
):
    rows = load_manifest_csv(manifest_csv)
    ds = OctSslDataset(rows, out_hw=(image_size, image_size), seed=seed)

    g = torch.Generator()
    g.manual_seed(seed)

    return DataLoader(
        ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        generator=g,
        drop_last=drop_last,
    )


@torch.no_grad()
def _eval_epoch(model: SimClrModel, loader: DataLoader, device: torch.device, temperature: float) -> float:
    model.eval()
    total_loss = 0.0
    n = 0
    for batch in loader:
        v1 = batch["v1"].to(device)
        v2 = batch["v2"].to(device)
        _, z1 = model(v1)
        _, z2 = model(v2)
        loss = nt_xent_loss(z1, z2, temperature=temperature)
        total_loss += float(loss.item())
        n += 1
    return total_loss / max(1, n)


def train(cfg: TrainConfig) -> None:
    cfg.out_dir.mkdir(parents=True, exist_ok=True)

    _seed_all(cfg.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_rows = load_manifest_csv(cfg.train_manifest)
    val_rows = load_manifest_csv(cfg.val_manifest)

    train_ds = OctSslDataset(train_rows, out_hw=(cfg.image_size, cfg.image_size), seed=cfg.seed)
    val_ds = OctSslDataset(val_rows, out_hw=(cfg.image_size, cfg.image_size), seed=cfg.seed + 1)

    g_train = torch.Generator(); g_train.manual_seed(cfg.seed)
    g_val = torch.Generator(); g_val.manual_seed(cfg.seed + 1)

    train_loader = DataLoader(
        train_ds,
        batch_size=cfg.batch_size,
        shuffle=True,
        num_workers=cfg.num_workers,
        generator=g_train,
        drop_last=len(train_ds) >= cfg.batch_size,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=cfg.batch_size,
        shuffle=False,
        num_workers=cfg.num_workers,
        generator=g_val,
        drop_last=False,
    )

    model = SimClrModel(proj_dim=cfg.proj_dim).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)

    best_val = math.inf
    log_path = cfg.out_dir / "training_log.csv"

    with log_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["epoch", "train_loss", "val_loss", "lr"])
        writer.writeheader()

        for epoch in range(1, cfg.epochs + 1):
            model.train()
            total = 0.0
            n = 0

            for batch in train_loader:
                v1 = batch["v1"].to(device)
                v2 = batch["v2"].to(device)

                opt.zero_grad(set_to_none=True)
                _, z1 = model(v1)
                _, z2 = model(v2)

                loss = nt_xent_loss(z1, z2, temperature=cfg.temperature)
                loss.backward()
                opt.step()

                total += float(loss.item())
                n += 1

            train_loss = total / max(1, n)
            val_loss = _eval_epoch(model, val_loader, device, temperature=cfg.temperature)

            writer.writerow(
                {
                    "epoch": epoch,
                    "train_loss": f"{train_loss:.6f}",
                    "val_loss": f"{val_loss:.6f}",
                    "lr": f"{cfg.lr:.8f}",
                }
            )
            f.flush()

            # Save checkpoints
            last_path = cfg.out_dir / "ssl_last.pt"
            cfg_state = {
                k: (str(v) if isinstance(v, Path) else v)
                for k, v in cfg.__dict__.items()
            }
            torch.save({"epoch": epoch, "model": model.state_dict(), "cfg": cfg_state}, last_path)

            if val_loss < best_val:
                best_val = val_loss
                best_path = cfg.out_dir / "ssl_best.pt"
                torch.save({"epoch": epoch, "model": model.state_dict(), "cfg": cfg_state}, best_path)

            print(f"Epoch {epoch}/{cfg.epochs} train_loss={train_loss:.4f} val_loss={val_loss:.4f}")

    print(f"OK: artifacts in {cfg.out_dir}")


def main(argv: list[str]) -> int:
    cfg = parse_args(argv)
    if not cfg.train_manifest.exists() or not cfg.val_manifest.exists():
        print("ERROR: manifest files not found. Run: python backend/scripts/srilankan_oct_make_manifests.py")
        print(f"Missing: {cfg.train_manifest}")
        print(f"Missing: {cfg.val_manifest}")
        return 2

    train(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(os.sys.argv[1:])))
