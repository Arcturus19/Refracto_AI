"""
Dataset Processing Script for Refracto AI
Processes RFMiD and custom fundus datasets for ML training
"""

import os
import pandas as pd
from PIL import Image
from pathlib import Path
from tqdm import tqdm
import shutil
from typing import Tuple, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
RAW_DATA_DIR = BASE_DIR / 'data' / 'raw'
PROCESSED_DATA_DIR = BASE_DIR / 'data' / 'processed'

# Image size
TARGET_SIZE = (224, 224)

# Statistics
stats = {
    'dataset1_train': 0,
    'dataset1_val': 0,
    'dataset1_test': 0,
    'dataset2_train': 0,
    'total': 0
}


def create_output_dirs():
    """Create output directory structure"""
    dirs = [
        PROCESSED_DATA_DIR / 'train',
        PROCESSED_DATA_DIR / 'val',
        PROCESSED_DATA_DIR / 'test'
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")


def resize_and_save_image(src_path: Path, dest_path: Path, size: Tuple[int, int] = TARGET_SIZE) -> bool:
    """
    Resize and save image
    
    Args:
        src_path: Source image path
        dest_path: Destination path
        size: Target size (width, height)
        
    Returns:
        True if successful
    """
    try:
        # Open image
        img = Image.open(src_path)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize
        img_resized = img.resize(size, Image.Resampling.LANCZOS)
        
        # Save
        img_resized.save(dest_path, 'JPEG', quality=95)
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing {src_path}: {str(e)}")
        return False


def map_rfmid_labels(row: pd.Series) -> Tuple[int, int]:
    """
    Map RFMiD labels to DR grade and glaucoma flag
    
    RFMiD has multiple disease labels. We extract:
    - DR (Diabetic Retinopathy) - mapped to grade
    - Glaucoma - binary flag
    
    Args:
        row: DataFrame row with disease columns
        
    Returns:
        Tuple of (dr_grade, glaucoma_flag)
    """
    # RFMiD columns (adjust based on actual dataset)
    # Common RFMiD columns: DR, ARMD, MH, DN, MYA, BRVO, TSLN, ERM, LS, MS, CSR, ODC, CRVO, TV, AH, ODP, ODE, ST, AION, PT, RT, RS, CRS, EDN
    
    dr_grade = 0  # Default: No DR
    glaucoma_flag = 0  # Default: No glaucoma
    
    # Map DR severity
    if 'DR' in row.index and row['DR'] == 1:
        dr_grade = 1  # Mild DR (adjust if multiple severity levels available)
    
    # Check for glaucoma indicators
    glaucoma_columns = ['Glaucoma', 'ODOC', 'ODP']  # Common glaucoma-related columns
    for col in glaucoma_columns:
        if col in row.index and row[col] == 1:
            glaucoma_flag = 1
            break
    
    return dr_grade, glaucoma_flag


def process_dataset_1():
    """
    Process RFMiD Dataset (test_dataset1)
    
    Structure:
        data/raw/test_dataset1/
            ├── train_1.csv
            ├── valid.csv
            ├── test.csv
            ├── train_images/
            ├── val_images/
            └── test_images/
    """
    logger.info("=" * 80)
    logger.info("Processing Dataset 1 (RFMiD)")
    logger.info("=" * 80)
    
    dataset1_path = RAW_DATA_DIR / 'test_dataset1'
    
    if not dataset1_path.exists():
        logger.warning(f"Dataset 1 not found at: {dataset1_path}")
        return
    
    # Process train set
    logger.info("\nProcessing training set...")
    train_csv = dataset1_path / 'train_1.csv'
    train_images_dir = dataset1_path / 'train_images' / 'train_images'
    
    if train_csv.exists() and train_images_dir.exists():
        df_train = pd.read_csv(train_csv)
        processed_rows = []
        
        for idx, row in tqdm(df_train.iterrows(), total=len(df_train), desc="Train images"):
            # Get image filename (adjust column name based on actual CSV)
            img_filename = row.get('id_code', row.get('ID', row.get('image_id', row.get('filename', None))))
            
            if img_filename is None:
                logger.warning(f"No image filename found in row {idx}")
                continue
            
            # Add extension if needed
            if not str(img_filename).endswith(('.jpg', '.jpeg', '.png')):
                img_filename = f"{img_filename}.png"  # RFMiD uses PNG
            
            src_path = train_images_dir / img_filename
            
            if not src_path.exists():
                # Try alternative extensions
                for ext in ['.jpg', '.jpeg', '.png', '.JPG']:
                    alt_path = train_images_dir / f"{Path(img_filename).stem}{ext}"
                    if alt_path.exists():
                        src_path = alt_path
                        break
            
            if not src_path.exists():
                logger.warning(f"Image not found: {src_path}")
                continue
            
            # Destination path
            dest_filename = f"rfmid_train_{idx:05d}.jpg"
            dest_path = PROCESSED_DATA_DIR / 'train' / dest_filename
            
            # Resize and save
            if resize_and_save_image(src_path, dest_path):
                # Map labels
                dr_grade, glaucoma_flag = map_rfmid_labels(row)
                
                processed_rows.append({
                    'filename': dest_filename,
                    'dr_grade': dr_grade,
                    'glaucoma_flag': glaucoma_flag,
                    'source': 'rfmid',
                    'original_id': img_filename
                })
                
                stats['dataset1_train'] += 1
        
        # Save clean CSV
        if processed_rows:
            df_clean = pd.DataFrame(processed_rows)
            df_clean.to_csv(PROCESSED_DATA_DIR / 'train' / 'rfmid_train.csv', index=False)
            logger.info(f"✓ Processed {len(processed_rows)} training images")
    
    # Process validation set
    logger.info("\nProcessing validation set...")
    val_csv = dataset1_path / 'valid.csv'
    val_images_dir = dataset1_path / 'val_images' / 'val_images'
    
    if val_csv.exists() and val_images_dir.exists():
        df_val = pd.read_csv(val_csv)
        processed_rows = []
        
        for idx, row in tqdm(df_val.iterrows(), total=len(df_val), desc="Val images"):
            img_filename = row.get('id_code', row.get('ID', row.get('image_id', row.get('filename', None))))
            
            if img_filename is None:
                continue
            
            if not str(img_filename).endswith(('.jpg', '.jpeg', '.png')):
                img_filename = f"{img_filename}.jpg"
            
            src_path = val_images_dir / img_filename
            
            if not src_path.exists():
                for ext in ['.jpg', '.jpeg', '.png', '.JPG']:
                    alt_path = val_images_dir / f"{Path(img_filename).stem}{ext}"
                    if alt_path.exists():
                        src_path = alt_path
                        break
            
            if not src_path.exists():
                continue
            
            dest_filename = f"rfmid_val_{idx:05d}.jpg"
            dest_path = PROCESSED_DATA_DIR / 'val' / dest_filename
            
            if resize_and_save_image(src_path, dest_path):
                dr_grade, glaucoma_flag = map_rfmid_labels(row)
                
                processed_rows.append({
                    'filename': dest_filename,
                    'dr_grade': dr_grade,
                    'glaucoma_flag': glaucoma_flag,
                    'source': 'rfmid',
                    'original_id': img_filename
                })
                
                stats['dataset1_val'] += 1
        
        if processed_rows:
            df_clean = pd.DataFrame(processed_rows)
            df_clean.to_csv(PROCESSED_DATA_DIR / 'val' / 'rfmid_val.csv', index=False)
            logger.info(f"✓ Processed {len(processed_rows)} validation images")
    
    # Process test set
    logger.info("\nProcessing test set...")
    test_csv = dataset1_path / 'test.csv'
    test_images_dir = dataset1_path / 'test_images' / 'test_images'
    
    if test_csv.exists() and test_images_dir.exists():
        df_test = pd.read_csv(test_csv)
        processed_rows = []
        
        for idx, row in tqdm(df_test.iterrows(), total=len(df_test), desc="Test images"):
            img_filename = row.get('id_code', row.get('ID', row.get('image_id', row.get('filename', None))))
            
            if img_filename is None:
                continue
            
            if not str(img_filename).endswith(('.jpg', '.jpeg', '.png')):
                img_filename = f"{img_filename}.jpg"
            
            src_path = test_images_dir / img_filename
            
            if not src_path.exists():
                for ext in ['.jpg', '.jpeg', '.png', '.JPG']:
                    alt_path = test_images_dir / f"{Path(img_filename).stem}{ext}"
                    if alt_path.exists():
                        src_path = alt_path
                        break
            
            if not src_path.exists():
                continue
            
            dest_filename = f"rfmid_test_{idx:05d}.jpg"
            dest_path = PROCESSED_DATA_DIR / 'test' / dest_filename
            
            if resize_and_save_image(src_path, dest_path):
                dr_grade, glaucoma_flag = map_rfmid_labels(row)
                
                processed_rows.append({
                    'filename': dest_filename,
                    'dr_grade': dr_grade,
                    'glaucoma_flag': glaucoma_flag,
                    'source': 'rfmid',
                    'original_id': img_filename
                })
                
                stats['dataset1_test'] += 1
        
        if processed_rows:
            df_clean = pd.DataFrame(processed_rows)
            df_clean.to_csv(PROCESSED_DATA_DIR / 'test' / 'rfmid_test.csv', index=False)
            logger.info(f"✓ Processed {len(processed_rows)} test images")


def process_dataset_2():
    """
    Process Custom Fundus Dataset (test_dataset2)
    
    Structure:
        data/raw/test_dataset2/
            └── Training_set/
                ├── image1.jpg
                ├── image2.jpg
                └── ...
    """
    logger.info("\n" + "=" * 80)
    logger.info("Processing Dataset 2 (Custom Fundus)")
    logger.info("=" * 80)
    
    dataset2_path = RAW_DATA_DIR / 'test_dataset2' / 'Training_set'
    
    if not dataset2_path.exists():
        logger.warning(f"Dataset 2 not found at: {dataset2_path}")
        return
    
    # Get all images
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(dataset2_path.glob(ext))
    
    logger.info(f"Found {len(image_files)} images in Training_set")
    
    processed_rows = []
    
    for idx, src_path in enumerate(tqdm(image_files, desc="Dataset 2 images")):
        dest_filename = f"custom_train_{idx:05d}.jpg"
        dest_path = PROCESSED_DATA_DIR / 'train' / dest_filename
        
        if resize_and_save_image(src_path, dest_path):
            # Default labels (no CSV available)
            processed_rows.append({
                'filename': dest_filename,
                'dr_grade': 0,  # Unknown
                'glaucoma_flag': 0,  # Unknown
                'source': 'custom',
                'original_filename': src_path.name
            })
            
            stats['dataset2_train'] += 1
    
    # Save CSV
    if processed_rows:
        df_clean = pd.DataFrame(processed_rows)
        df_clean.to_csv(PROCESSED_DATA_DIR / 'train' / 'custom_train.csv', index=False)
        logger.info(f"✓ Processed {len(processed_rows)} custom training images")


def merge_csvs():
    """Merge all CSVs in each split"""
    logger.info("\n" + "=" * 80)
    logger.info("Merging CSVs")
    logger.info("=" * 80)
    
    for split in ['train', 'val', 'test']:
        csv_files = list((PROCESSED_DATA_DIR / split).glob('*.csv'))
        
        if not csv_files:
            continue
        
        # Read and concatenate
        dfs = []
        for csv_file in csv_files:
            df = pd.read_csv(csv_file)
            dfs.append(df)
        
        if dfs:
            df_merged = pd.concat(dfs, ignore_index=True)
            output_path = PROCESSED_DATA_DIR / split / f'{split}_labels.csv'
            df_merged.to_csv(output_path, index=False)
            logger.info(f"✓ Merged {split} CSV: {len(df_merged)} total images")


def print_summary():
    """Print processing summary"""
    stats['total'] = sum([
        stats['dataset1_train'],
        stats['dataset1_val'],
        stats['dataset1_test'],
        stats['dataset2_train']
    ])
    
    logger.info("\n" + "=" * 80)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"\nDataset 1 (RFMiD):")
    logger.info(f"  Training:   {stats['dataset1_train']:6d} images")
    logger.info(f"  Validation: {stats['dataset1_val']:6d} images")
    logger.info(f"  Test:       {stats['dataset1_test']:6d} images")
    logger.info(f"\nDataset 2 (Custom):")
    logger.info(f"  Training:   {stats['dataset2_train']:6d} images")
    logger.info(f"\n{'TOTAL:':<13} {stats['total']:6d} images processed")
    logger.info("\n" + "=" * 80)
    logger.info(f"Output directory: {PROCESSED_DATA_DIR}")
    logger.info("=" * 80)


def main():
    """Main processing function"""
    logger.info("Starting dataset processing...")
    logger.info(f"Raw data directory: {RAW_DATA_DIR}")
    logger.info(f"Output directory: {PROCESSED_DATA_DIR}")
    logger.info(f"Target image size: {TARGET_SIZE}")
    
    # Create output directories
    create_output_dirs()
    
    # Process datasets
    process_dataset_1()
    process_dataset_2()
    
    # Merge CSVs
    merge_csvs()
    
    # Print summary
    print_summary()
    
    logger.info("\n✅ Dataset processing complete!")


if __name__ == '__main__':
    main()
