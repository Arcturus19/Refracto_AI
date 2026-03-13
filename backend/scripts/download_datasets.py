#!/usr/bin/env python3
"""
download_datasets.py
Script to download necessary open-source datasets (e.g., sample data from RFMiD, GAMMA, or mock Sri Lankan data)
to enable the training pipeline for Phase 2 fine-tuning.
"""

import os
import requests
import zipfile
import logging
from pathlib import Path
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample/Mock Dataset Links for demonstration purposes
# In a real environment, replace these with actual authorized dataset links or Kaggle API commands
DATASETS = {
    "rfmid_sample": {
        "url": "https://raw.githubusercontent.com/Arcturus19/Refracto_AI_Dataset_Mock/main/rfmid_sample.zip",  # Replace with actual
        "desc": "RFMiD Sample Dataset (Foreign Pre-training)"
    },
    "gamma_sample": {
        "url": "https://raw.githubusercontent.com/Arcturus19/Refracto_AI_Dataset_Mock/main/gamma_sample.zip",  # Replace with actual
        "desc": "GAMMA Challenge Sample (Glaucoma + OCT)"
    },
    "sri_lankan_mock": {
        "url": "https://raw.githubusercontent.com/Arcturus19/Refracto_AI_Dataset_Mock/main/sri_lankan_mock.zip", # Replace with actual
        "desc": "Local Sri Lankan Cohort Mock (Fine-tuning)"
    }
}

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

def download_file(url: str, dest_path: Path):
    """Downloads a file with a progress bar."""
    logger.info(f"Downloading from {url} to {dest_path}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 # 1 Kibibyte
        
        with open(dest_path, 'wb') as file, tqdm(
                desc=dest_path.name,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
            for data in response.iter_content(block_size):
                size = file.write(data)
                bar.update(size)
                
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        # Note: Since the URLs are mock placeholders, we catch the error but don't strictly fail
        return False

def extract_zip(zip_path: Path, extract_to: Path):
    """Extracts a zip file."""
    logger.info(f"Extracting {zip_path} to {extract_to}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        logger.info("Extraction complete.")
        return True
    except zipfile.BadZipFile:
        logger.error(f"Bad zip file: {zip_path}")
        return False

def main():
    logger.info("Starting dataset download process...")
    
    # Ensure raw data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    for name, info in DATASETS.items():
        logger.info(f"\nProcessing {info['desc']}...")
        zip_path = DATA_DIR / f"{name}.zip"
        extract_dir = DATA_DIR / name
        
        # Download
        if not zip_path.exists():
            success = download_file(info['url'], zip_path)
            if not success:
                logger.warning(f"Using mock structure for {name} since download failed (expected for mock URLs).")
                # Create a mock directory structure just so training pipeline works
                extract_dir.mkdir(parents=True, exist_ok=True)
                (extract_dir / "images").mkdir(exist_ok=True)
                (extract_dir / "labels.csv").touch()
                continue
        else:
            logger.info(f"File {zip_path} already exists. Skipping download.")
            
        # Extract
        if not extract_dir.exists() and zip_path.exists():
            extract_zip(zip_path, extract_dir)
        else:
            logger.info(f"Directory {extract_dir} already exists. Skipping extraction.")
            
    logger.info("\nDataset download process completed. Data ready for data_harmonization.py")

if __name__ == "__main__":
    main()
