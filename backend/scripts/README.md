# Dataset Processing Guide

## Overview

The `process_datasets.py` script processes raw RFMiD and custom fundus datasets for ML training.

## Quick Start

```powershell
# Install requirements
cd "c:\Users\VICTUS\Desktop\Refracto AI\Refracto-AI-Backend\scripts"
pip install -r requirements.txt

# Run processing
python process_datasets.py
```

## Expected Directory Structure

### Input (Raw Data)

```
Refracto-AI-Backend/
└── data/
    └── raw/
        ├── test_dataset1/          # RFMiD Dataset
        │   ├── train_1.csv
        │   ├── valid.csv
        │   ├── test.csv
        │   ├── train_images/
        │   ├── val_images/
        │   └── test_images/
        └── test_dataset2/          # Custom Dataset
            └── Training_set/
                ├── image1.jpg
                ├── image2.jpg
                └── ...
```

### Output (Processed Data)

```
Refracto-AI-Backend/
└── data/
    └── processed/
        ├── train/
        │   ├── rfmid_train_00001.jpg (224x224)
        │   ├── custom_train_00001.jpg (224x224)
        │   ├── rfmid_train.csv
        │   ├── custom_train.csv
        │   └── train_labels.csv (merged)
        ├── val/
        │   ├── rfmid_val_00001.jpg
        │   ├── rfmid_val.csv
        │   └── val_labels.csv (merged)
        └── test/
            ├── rfmid_test_00001.jpg
            ├── rfmid_test.csv
            └── test_labels.csv (merged)
```

## CSV Format

### Individual CSVs (e.g., rfmid_train.csv)

| filename | dr_grade | glaucoma_flag | source | original_id |
|----------|----------|---------------|--------|-------------|
| rfmid_train_00001.jpg | 0 | 0 | rfmid | 12345.jpg |
| rfmid_train_00002.jpg | 1 | 1 | rfmid | 12346.jpg |

### Merged CSV (e.g., train_labels.csv)

Combines all individual CSVs for each split (train/val/test).

## Features

✅ **Automatic resizing** to 224x224  
✅ **DR grade extraction** from RFMiD labels  
✅ **Glaucoma flag detection**  
✅ **Progress bars** with tqdm  
✅ **Error handling** for missing images  
✅ **Multiple format support** (.jpg, .jpeg, .png)  
✅ **Clean CSV generation**  
✅ **Processing statistics**  

## Label Mapping (RFMiD)

The script maps RFMiD disease labels to:

- **DR Grade** (0-4): Diabetic retinopathy severity
  - 0: No DR
  - 1: Mild
  - 2: Moderate
  - 3: Severe
  - 4: Proliferative

- **Glaucoma Flag** (0/1): Binary indicator
  - Detected from columns: Glaucoma, ODOC, ODP

## Customization

### Adjust Target Size

```python
# In process_datasets.py
TARGET_SIZE = (512, 512)  # Change from default (224, 224)
```

### Modify Label Mapping

```python
def map_rfmid_labels(row: pd.Series) -> Tuple[int, int]:
    # Customize DR grade mapping
    if 'DR_MILD' in row.index and row['DR_MILD'] == 1:
        dr_grade = 1
    elif 'DR_MODERATE' in row.index and row['DR_MODERATE'] == 1:
        dr_grade = 2
    # ... your logic
```

### Add Custom Dataset 3

```python
def process_dataset_3():
    dataset3_path = RAW_DATA_DIR / 'test_dataset3'
    # Your processing logic
    
# In main():
process_dataset_3()
```

## Expected Output

```
================================================================================
PROCESSING SUMMARY
================================================================================

Dataset 1 (RFMiD):
  Training:     1234 images
  Validation:    234 images
  Test:          345 images

Dataset 2 (Custom):
  Training:     5000 images

TOTAL:          6813 images processed

================================================================================
Output directory: c:\Users\VICTUS\Desktop\Refracto AI\Refracto-AI-Backend\data\processed
================================================================================

✅ Dataset processing complete!
```

## Troubleshooting

### CSV Column Names

If RFMiD CSV uses different column names, update:

```python
img_filename = row.get('ID', row.get('image_id', row.get('YOUR_COLUMN_NAME', None)))
```

### Missing Images

The script automatically:
- Tries multiple extensions (.jpg, .jpeg, .png, .JPG)
- Logs warnings for missing images
- Continues processing remaining images

### Memory Issues

For large datasets, process in batches:

```python
# Process first 1000 images
df_train = pd.read_csv(train_csv).head(1000)
```

## Next Steps

1. **Verify processed data:**
```python
import pandas as pd
df = pd.read_csv('data/processed/train/train_labels.csv')
print(df.head())
print(df['dr_grade'].value_counts())
```

2. **Create PyTorch DataLoader:**
```python
from torch.utils.data import Dataset, DataLoader

class FundusDataset(Dataset):
    def __init__(self, csv_file, img_dir, transform=None):
        self.df = pd.read_csv(csv_file)
        self.img_dir = img_dir
        self.transform = transform
    
    def __getitem__(self, idx):
        # Load preprocessed image
        img_name = self.df.iloc[idx]['filename']
        image = Image.open(self.img_dir / img_name)
        label = self.df.iloc[idx]['dr_grade']
        
        if self.transform:
            image = self.transform(image)
        
        return image, label
```

3. **Start training:**
```bash
cd services/ml_service
python train.py --data ../data/processed
```

---

**Your datasets are ready for ML training!** 🎯📊
