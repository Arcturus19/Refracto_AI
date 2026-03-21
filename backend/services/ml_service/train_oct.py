"""Train an OCT classifier for CNV, DME, DRUSEN, and NORMAL scans."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import random
import time

import numpy as np
import timm
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import transforms
from tqdm import tqdm

from core.oct_dataset_loader import (
    OCT_CLASSES,
    OCT_CLASS_TO_INDEX,
    OCTImageDataset,
    build_oct_splits,
    compute_class_weights,
    create_weighted_sampler,
    summarize_samples,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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
            transforms.ColorJitter(brightness=0.10, contrast=0.10)
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


def configure_trainable_parameters(model: nn.Module, freeze_backbone: bool) -> None:
    for parameter in model.parameters():
        parameter.requires_grad = not freeze_backbone

    for attribute_name in ("classifier", "fc", "head"):
        module = getattr(model, attribute_name, None)
        if isinstance(module, nn.Module):
            for parameter in module.parameters():
                parameter.requires_grad = True


def create_optimizer(model: nn.Module, learning_rate: float, weight_decay: float) -> optim.Optimizer:
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    return optim.AdamW(parameters, lr=learning_rate, weight_decay=weight_decay)


def update_confusion_matrix(confusion: np.ndarray, labels: torch.Tensor, predictions: torch.Tensor) -> None:
    label_values = labels.detach().cpu().numpy()
    prediction_values = predictions.detach().cpu().numpy()

    for label, prediction in zip(label_values, prediction_values):
        confusion[int(label), int(prediction)] += 1


def compute_metrics(confusion: np.ndarray) -> dict[str, object]:
    total = int(confusion.sum())
    correct = int(np.trace(confusion))
    accuracy = correct / total if total else 0.0

    per_class: dict[str, dict[str, float | int]] = {}
    f1_scores: list[float] = []
    recalls: list[float] = []

    for class_index, class_name in enumerate(OCT_CLASSES):
        true_positive = int(confusion[class_index, class_index])
        false_positive = int(confusion[:, class_index].sum() - true_positive)
        false_negative = int(confusion[class_index, :].sum() - true_positive)
        support = int(confusion[class_index, :].sum())

        precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) else 0.0
        recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) else 0.0
        if precision + recall:
            f1_score = (2.0 * precision * recall) / (precision + recall)
        else:
            f1_score = 0.0

        per_class[class_name] = {
            "precision": precision,
            "recall": recall,
            "f1": f1_score,
            "support": support,
        }
        f1_scores.append(f1_score)
        recalls.append(recall)

    macro_f1 = float(sum(f1_scores) / len(f1_scores)) if f1_scores else 0.0
    balanced_accuracy = float(sum(recalls) / len(recalls)) if recalls else 0.0

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "balanced_accuracy": balanced_accuracy,
        "per_class": per_class,
        "confusion_matrix": confusion.tolist(),
    }


def run_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    optimizer: optim.Optimizer | None = None,
    max_batches: int | None = None,
) -> dict[str, object]:
    is_training = optimizer is not None
    model.train(mode=is_training)

    running_loss = 0.0
    total_samples = 0
    confusion = np.zeros((len(OCT_CLASSES), len(OCT_CLASSES)), dtype=np.int64)
    progress = tqdm(dataloader, desc="Train" if is_training else "Eval")

    for batch_index, batch in enumerate(progress):
        if max_batches is not None and batch_index >= max_batches:
            break

        images = batch["image"].to(device)
        labels = batch["label"].to(device)

        if is_training:
            optimizer.zero_grad(set_to_none=True)

        with torch.set_grad_enabled(is_training):
            logits = model(images)
            loss = criterion(logits, labels)

            if is_training:
                loss.backward()
                optimizer.step()

        predictions = torch.argmax(logits, dim=1)
        batch_size = labels.size(0)
        running_loss += float(loss.item()) * batch_size
        total_samples += batch_size
        update_confusion_matrix(confusion, labels, predictions)

        batch_accuracy = float((predictions == labels).float().mean().item())
        progress.set_postfix(loss=f"{loss.item():.4f}", acc=f"{batch_accuracy * 100:.2f}%")

    metrics = compute_metrics(confusion)
    metrics["loss"] = running_loss / total_samples if total_samples else 0.0
    return metrics


def save_checkpoint(
    model: nn.Module,
    output_path: Path,
    model_name: str,
    img_size: int,
    epoch: int,
    metrics: dict[str, object],
    args: argparse.Namespace,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_name": model_name,
            "num_classes": len(OCT_CLASSES),
            "class_to_idx": OCT_CLASS_TO_INDEX,
            "classes": list(OCT_CLASSES),
            "img_size": img_size,
            "epoch": epoch,
            "metrics": metrics,
            "args": vars(args),
            "state_dict": model.state_dict(),
        },
        output_path,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train an OCT classifier for Refracto AI")
    parser.add_argument(
        "--data-roots",
        nargs="+",
        required=True,
        help="One or more OCT dataset roots. Duplicate filenames across roots are deduplicated.",
    )
    parser.add_argument("--model", type=str, default="efficientnet_b3", help="timm model name")
    parser.add_argument("--img-size", type=int, default=300, help="Input image size")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--epochs", type=int, default=20, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning rate")
    parser.add_argument("--weight-decay", type=float, default=1e-4, help="Weight decay")
    parser.add_argument("--freeze-backbone-epochs", type=int, default=2, help="Warm-up epochs with frozen backbone")
    parser.add_argument("--val-split", type=float, default=0.15, help="Validation split ratio if re-splitting train data")
    parser.add_argument("--use-existing-val", action="store_true", help="Use an existing validation split if it is sufficiently large")
    parser.add_argument("--min-existing-val-per-class", type=int, default=50, help="Minimum per-class validation images required to use an existing val split")
    parser.add_argument("--workers", type=int, default=0, help="DataLoader workers. Use 0 on Windows for stability.")
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience on validation macro F1")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--model-dir", type=str, default="../../models/oct", help="Directory for checkpoints and logs")
    parser.add_argument("--resume-checkpoint", type=str, default=None, help="Optional checkpoint path to resume OCT training from")
    parser.add_argument("--max-train-batches", type=int, default=None, help="Optional limit for train batches per epoch")
    parser.add_argument("--max-val-batches", type=int, default=None, help="Optional limit for validation batches per epoch")
    parser.add_argument("--max-test-batches", type=int, default=None, help="Optional limit for test batches")
    parser.add_argument("--dry-run", action="store_true", help="Run a 1-batch train/val smoke test instead of full training")
    parser.add_argument("--cpu", action="store_true", help="Force CPU even if CUDA is available")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    device = torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")
    logger.info("Using device: %s", device)
    logger.info("Data roots: %s", args.data_roots)

    splits = build_oct_splits(
        data_roots=args.data_roots,
        val_split=args.val_split,
        seed=args.seed,
        use_existing_val=args.use_existing_val,
        min_existing_val_per_class=args.min_existing_val_per_class,
    )

    logger.info("Train summary: %s", summarize_samples(splits["train"]))
    logger.info("Val summary: %s", summarize_samples(splits["val"]))
    logger.info("Test summary: %s", summarize_samples(splits["test"]))

    train_transform, eval_transform = get_transforms(args.img_size)
    train_dataset = OCTImageDataset(splits["train"], transform=train_transform)
    val_dataset = OCTImageDataset(splits["val"], transform=eval_transform)
    test_dataset = OCTImageDataset(splits["test"], transform=eval_transform)

    sampler = create_weighted_sampler(splits["train"])
    class_weights = compute_class_weights(splits["train"])
    loss_weights = torch.tensor(
        [class_weights[index] for index in range(len(OCT_CLASSES))],
        dtype=torch.float32,
        device=device,
    )

    loader_kwargs = {
        "batch_size": args.batch_size,
        "num_workers": args.workers,
        "pin_memory": device.type == "cuda",
    }

    train_loader = DataLoader(train_dataset, sampler=sampler, **loader_kwargs)
    val_loader = DataLoader(val_dataset, shuffle=False, **loader_kwargs)
    test_loader = DataLoader(test_dataset, shuffle=False, **loader_kwargs)

    model = timm.create_model(args.model, pretrained=True, num_classes=len(OCT_CLASSES))
    model = model.to(device)

    start_epoch = 0
    best_macro_f1 = -1.0
    if args.resume_checkpoint:
        resume_path = Path(args.resume_checkpoint).resolve()
        logger.info("Resuming OCT training from %s", resume_path)
        checkpoint = torch.load(resume_path, map_location=device)
        model.load_state_dict(checkpoint["state_dict"])
        start_epoch = int(checkpoint.get("epoch", 0))
        checkpoint_metrics = checkpoint.get("metrics", {})
        best_macro_f1 = float(checkpoint_metrics.get("macro_f1", best_macro_f1))

    configure_trainable_parameters(model, freeze_backbone=args.freeze_backbone_epochs > 0)
    optimizer = create_optimizer(model, learning_rate=args.lr, weight_decay=args.weight_decay)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)
    criterion = nn.CrossEntropyLoss(weight=loss_weights)

    output_dir = Path(args.model_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    best_model_path = output_dir / "oct_best.pt"
    history_path = output_dir / "training_log.json"

    max_train_batches = 1 if args.dry_run else args.max_train_batches
    max_val_batches = 1 if args.dry_run else args.max_val_batches
    max_test_batches = 1 if args.dry_run else args.max_test_batches

    history: list[dict[str, object]] = []
    epochs_without_improvement = 0
    start_time = time.time()

    for epoch in range(start_epoch, args.epochs):
        if epoch == args.freeze_backbone_epochs and args.freeze_backbone_epochs > 0:
            logger.info("Unfreezing OCT backbone for fine-tuning.")
            configure_trainable_parameters(model, freeze_backbone=False)
            optimizer = create_optimizer(model, learning_rate=args.lr, weight_decay=args.weight_decay)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)

        logger.info("Epoch %s/%s", epoch + 1, args.epochs)
        train_metrics = run_epoch(
            model=model,
            dataloader=train_loader,
            criterion=criterion,
            device=device,
            optimizer=optimizer,
            max_batches=max_train_batches,
        )
        val_metrics = run_epoch(
            model=model,
            dataloader=val_loader,
            criterion=criterion,
            device=device,
            optimizer=None,
            max_batches=max_val_batches,
        )

        scheduler.step(float(val_metrics["macro_f1"]))

        epoch_record = {
            "epoch": epoch + 1,
            "train": train_metrics,
            "val": val_metrics,
            "lr": optimizer.param_groups[0]["lr"],
        }
        history.append(epoch_record)

        logger.info(
            "Train loss %.4f | acc %.4f | macro_f1 %.4f || Val loss %.4f | acc %.4f | macro_f1 %.4f",
            train_metrics["loss"],
            train_metrics["accuracy"],
            train_metrics["macro_f1"],
            val_metrics["loss"],
            val_metrics["accuracy"],
            val_metrics["macro_f1"],
        )

        if float(val_metrics["macro_f1"]) > best_macro_f1:
            best_macro_f1 = float(val_metrics["macro_f1"])
            epochs_without_improvement = 0
            save_checkpoint(model, best_model_path, args.model, args.img_size, epoch + 1, val_metrics, args)
            logger.info("Saved new best OCT checkpoint to %s", best_model_path)
        else:
            epochs_without_improvement += 1

        if args.dry_run:
            logger.info("Dry run complete after one validation pass.")
            break

        if epochs_without_improvement >= args.patience:
            logger.info("Early stopping triggered after %s epochs without improvement.", args.patience)
            break

    if best_model_path.exists():
        checkpoint = torch.load(best_model_path, map_location=device)
        model.load_state_dict(checkpoint["state_dict"])

    test_metrics = run_epoch(
        model=model,
        dataloader=test_loader,
        criterion=criterion,
        device=device,
        optimizer=None,
        max_batches=max_test_batches,
    ) if len(test_dataset) else {}

    summary = {
        "model": args.model,
        "img_size": args.img_size,
        "device": str(device),
        "classes": list(OCT_CLASSES),
        "class_weights": {OCT_CLASSES[index]: weight for index, weight in class_weights.items()},
        "dataset": {
            "train": summarize_samples(splits["train"]),
            "val": summarize_samples(splits["val"]),
            "test": summarize_samples(splits["test"]),
        },
        "best_val_macro_f1": best_macro_f1,
        "test": test_metrics,
        "epochs_ran": len(history),
        "elapsed_seconds": time.time() - start_time,
        "history": history,
    }

    history_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("Wrote OCT training log to %s", history_path)

    if test_metrics:
        logger.info(
            "Final test metrics | loss %.4f | acc %.4f | macro_f1 %.4f",
            test_metrics["loss"],
            test_metrics["accuracy"],
            test_metrics["macro_f1"],
        )


if __name__ == "__main__":
    main()