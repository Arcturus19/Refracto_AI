# Dataset Preparation Guide

## Quick Start

### 1. Move Your Data

```powershell
# Move data folder to ML service
Move-Item -Path "c:\Users\VICTUS\Desktop\Refracto AI\data" -Destination "c:\Users\VICTUS\Desktop\Refracto AI\Refracto-AI-Backend\services\ml_service\datasets"
```

### 2. Run Preparation Script

```powershell
cd "c:\Users\VICTUS\Desktop\Refracto AI\Refracto-AI-Backend\services\ml_service"

# Default: 70% train, 15% val, 15% test
python prepare_dataset.py

# Custom split ratios
python prepare_dataset.py --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1

# Specify paths
python prepare_dataset.py --raw-path "datasets/data/raw" --output-path "datasets/fundus"
```

## Dataset Structure

**Before (Raw):**
```
datasets/
└── data/
    └── raw/
        ├── image001.jpg
        ├── image002.jpg
        └── ...
```

**After (Organized):**
```
datasets/
└── fundus/
    ├── raw/              # Original untouched
    ├── train/
    │   ├── 0/           # No DR
    │   ├── 1/           # Mild DR
    │   ├── 2/           # Moderate DR
    │   ├── 3/           # Severe DR
    │   └── 4/           # Proliferative DR
    ├── val/
    │   ├── 0/
    │   ├── 1/
    │   ├── 2/
    │   ├── 3/
    │   └── 4/
    └── test/
        ├── 0/
        ├── 1/
        ├── 2/
        ├── 3/
        └── 4/
```

## Features

✅ **Auto-class detection** - Detects DR grades from filenames or folders  
✅ **Stratified splitting** - Maintains class distribution  
✅ **Reproducible** - Uses random seed  
✅ **Preserves originals** - Copies (doesn't move) files  
✅ **Duplicate handling** - Renames duplicates automatically  

## Class Detection

The script automatically detects classes from:

1. **Folder structure:** `raw/0/`, `raw/1/`, etc.
2. **Filenames:** 
   - `DR_0_image.jpg`
   - `class_2_fundus.png`
   - `grade_3_scan.jpg`

If no class is detected, images go to `unknown/` folder.

## Command-Line Options

```bash
Options:
  --raw-path PATH         Path to raw images (default: datasets/fundus/raw)
  --output-path PATH      Output base path (default: datasets/fundus)
  --train-ratio FLOAT     Training set ratio (default: 0.7)
  --val-ratio FLOAT       Validation set ratio (default: 0.15)
  --test-ratio FLOAT      Test set ratio (default: 0.15)
  --no-class-split        Don't organize by class
  --seed INT              Random seed (default: 42)
```

## Example Outputs

```
==============================================
Starting Dataset Preparation
==============================================
Scanning images in: datasets/fundus/raw
Found 6868 images

Class distribution:
  Class 0: 2745 images
  Class 1: 1523 images
  Class 2: 1689 images
  Class 3: 579 images
  Class 4: 332 images

Dataset split:
  Train: 4807 images (70.0%)
  Val:   1030 images (15.0%)
  Test:  1031 images (15.0%)

Processing class '0'...
  Copying train files...
  Copying validation files...
  Copying test files...

...

==============================================
Dataset Preparation Complete!
==============================================

Datasets created at: datasets/fundus
  - Train: datasets/fundus/train
  - Val:   datasets/fundus/val
  - Test:  datasets/fundus/test
```

## Update .gitignore

Add to `.gitignore`:

```
# Datasets
services/ml_service/datasets/
*.jpg
*.jpeg
*.png
*.bmp
*.tiff

# Keep structure but ignore images
!.gitkeep
```

## Next Steps

After organizing your dataset:

1. **Train a model:**
```bash
cd services/ml_service
python train_model.py --dataset datasets/fundus
```

2. **Validate data quality:**
```bash
python validate_dataset.py
```

3. **Create data loaders** for PyTorch training

---

**Your fundus images are now ready for ML training!** 🎯📊
