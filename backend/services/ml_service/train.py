"""
Training Script for Refracto AI Models
Script to train the EfficientNet-B3 model for DR grading
"""

import os
import argparse
import time
import logging
from pathlib import Path
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import transforms
import timm

from core.dataset_loader import RefractoDataset

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_transforms(img_size=224):
    """Get training and validation transforms"""
    train_transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    return train_transform, val_transform

def train_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(dataloader, desc="Training")
    for batch in pbar:
        images = batch['image'].to(device)
        labels = batch['labels']['dr'].to(device)
        
        optimizer.zero_grad()
        
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        pbar.set_postfix({'loss': loss.item(), 'acc': 100.*correct/total})
        
    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_acc = 100. * correct / total
    return epoch_loss, epoch_acc

def val_epoch(model, dataloader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        pbar = tqdm(dataloader, desc="Validation")
        for batch in pbar:
            images = batch['image'].to(device)
            labels = batch['labels']['dr'].to(device)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            
            pbar.set_postfix({'loss': loss.item(), 'acc': 100.*correct/total})
            
    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_acc = 100. * correct / total
    return epoch_loss, epoch_acc

def main():
    parser = argparse.ArgumentParser(description="Train ML models for Refracto AI")
    parser.add_argument('--data', type=str, required=True, help="Path to processed data directory")
    parser.add_argument('--batch-size', type=int, default=32, help="Batch size")
    parser.add_argument('--epochs', type=int, default=20, help="Number of epochs")
    parser.add_argument('--lr', type=float, default=1e-4, help="Learning rate")
    parser.add_argument('--model-dir', type=str, default='../../models', help="Directory to save models")
    args = parser.parse_args()

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    data_dir = Path(args.data)
    
    # Setup paths
    train_dir = data_dir / 'train'
    val_dir = data_dir / 'val'
    train_csv = train_dir / 'train_labels.csv'
    val_csv = val_dir / 'val_labels.csv'
    
    if not train_csv.exists() or not train_dir.exists():
        logger.error(f"Training data not found at {train_dir}. Please run processing script first.")
        # If running just to test script existence, we can still generate the script but exit here.
        return
        
    # Transforms
    train_transform, val_transform = get_transforms()
    
    # Datasets
    logger.info("Initializing datasets...")
    train_dataset = RefractoDataset(csv_file=str(train_csv), root_dir=str(train_dir), transform=train_transform)
    val_dataset = RefractoDataset(csv_file=str(val_csv), root_dir=str(val_dir), transform=val_transform)
    
    # Dataloaders
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=4)
    
    logger.info(f"Train size: {len(train_dataset)}, Val size: {len(val_dataset)}")
    
    # Model
    logger.info("Initializing EfficientNet-B3...")
    model = timm.create_model('efficientnet_b3', pretrained=True, num_classes=5)
    model = model.to(device)
    
    # Loss and Optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=3, verbose=True)
    
    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    
    best_acc = 0.0
    
    logger.info("Starting training...")
    for epoch in range(args.epochs):
        logger.info(f"Epoch {epoch+1}/{args.epochs}")
        
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = val_epoch(model, val_loader, criterion, device)
        
        logger.info(f"Train Loss: {train_loss:.4f} Acc: {train_acc:.2f}% | Val Loss: {val_loss:.4f} Acc: {val_acc:.2f}%")
        
        scheduler.step(val_acc)
        
        # Save best model
        if val_acc > best_acc:
            best_acc = val_acc
            save_path = model_dir / 'fundus_efficientnet_b3_best.pth'
            torch.save(model.state_dict(), save_path)
            logger.info(f"Saved new best model with accuracy {best_acc:.2f}%")
            
    logger.info(f"Training complete. Best validation accuracy: {best_acc:.2f}%")

if __name__ == '__main__':
    main()
