"""
Dataset Preparation Script for Refracto AI
Organizes raw fundus images into train/validation/test splits
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple
import random
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatasetPreparator:
    """
    Prepare fundus image datasets for training
    """
    
    def __init__(
        self,
        raw_data_path: str,
        output_base_path: str,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42
    ):
        """
        Initialize dataset preparator
        
        Args:
            raw_data_path: Path to raw images
            output_base_path: Base path for organized datasets
            train_ratio: Proportion for training set
            val_ratio: Proportion for validation set
            test_ratio: Proportion for test set
            seed: Random seed for reproducibility
        """
        self.raw_data_path = Path(raw_data_path)
        self.output_base_path = Path(output_base_path)
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed
        
        # Validate ratios
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
            raise ValueError("Train, val, and test ratios must sum to 1.0")
        
        random.seed(seed)
        
    def scan_images(self) -> List[Path]:
        """
        Scan raw data directory for image files
        
        Returns:
            List of image file paths
        """
        logger.info(f"Scanning images in: {self.raw_data_path}")
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(self.raw_data_path.glob(f'**/*{ext}'))
            image_files.extend(self.raw_data_path.glob(f'**/*{ext.upper()}'))
        
        logger.info(f"Found {len(image_files)} images")
        return image_files
    
    def organize_by_class(self, image_files: List[Path]) -> dict:
        """
        Organize images by class based on filename or directory structure
        
        For diabetic retinopathy datasets, common naming conventions:
        - DR_0_*, DR_1_*, etc. (class in filename)
        - Organized in class folders (0/, 1/, 2/, etc.)
        
        Args:
            image_files: List of image paths
            
        Returns:
            Dictionary mapping class -> list of images
        """
        classes = defaultdict(list)
        
        for img_path in image_files:
            # Try to extract class from parent directory
            parent_name = img_path.parent.name
            
            # Check if parent directory is a class label (0, 1, 2, 3, 4)
            if parent_name.isdigit():
                class_label = parent_name
            else:
                # Try to extract from filename (e.g., DR_0_123.jpg, class_2_image.png)
                filename = img_path.stem.lower()
                
                # Look for patterns like "dr_0", "class_2", "grade_3", etc.
                class_label = None
                for i in range(5):  # DR grades 0-4
                    if f'_{i}_' in filename or f'_grade_{i}' in filename or f'_class_{i}' in filename:
                        class_label = str(i)
                        break
                
                # If no class found, put in 'unknown' category
                if class_label is None:
                    class_label = 'unknown'
            
            classes[class_label].append(img_path)
        
        # Log class distribution
        logger.info("\nClass distribution:")
        for class_label in sorted(classes.keys()):
            logger.info(f"  Class {class_label}: {len(classes[class_label])} images")
        
        return dict(classes)
    
    def split_dataset(
        self,
        image_files: List[Path]
    ) -> Tuple[List[Path], List[Path], List[Path]]:
        """
        Split images into train/val/test sets
        
        Args:
            image_files: List of image paths
            
        Returns:
            Tuple of (train_files, val_files, test_files)
        """
        # Shuffle images
        shuffled = image_files.copy()
        random.shuffle(shuffled)
        
        # Calculate split indices
        total = len(shuffled)
        train_end = int(total * self.train_ratio)
        val_end = train_end + int(total * self.val_ratio)
        
        train_files = shuffled[:train_end]
        val_files = shuffled[train_end:val_end]
        test_files = shuffled[val_end:]
        
        logger.info(f"\nDataset split:")
        logger.info(f"  Train: {len(train_files)} images ({len(train_files)/total*100:.1f}%)")
        logger.info(f"  Val:   {len(val_files)} images ({len(val_files)/total*100:.1f}%)")
        logger.info(f"  Test:  {len(test_files)} images ({len(test_files)/total*100:.1f}%)")
        
        return train_files, val_files, test_files
    
    def copy_files(
        self,
        file_list: List[Path],
        destination_dir: Path,
        class_label: str = None
    ):
        """
        Copy files to destination directory
        
        Args:
            file_list: List of files to copy
            destination_dir: Destination directory
            class_label: Optional class label for subdirectory
        """
        if class_label:
            dest = destination_dir / class_label
        else:
            dest = destination_dir
        
        dest.mkdir(parents=True, exist_ok=True)
        
        for src_path in file_list:
            dest_path = dest / src_path.name
            
            # Handle duplicate filenames
            counter = 1
            while dest_path.exists():
                dest_path = dest / f"{src_path.stem}_{counter}{src_path.suffix}"
                counter += 1
            
            shutil.copy2(src_path, dest_path)
    
    def prepare_datasets(self, split_by_class: bool = True):
        """
        Main method to prepare datasets
        
        Args:
            split_by_class: Whether to organize by class labels
        """
        logger.info("=" * 80)
        logger.info("Starting Dataset Preparation")
        logger.info("=" * 80)
        
        # Scan images
        image_files = self.scan_images()
        
        if len(image_files) == 0:
            logger.error("No images found! Check your raw_data_path.")
            return
        
        # Create output directories
        train_dir = self.output_base_path / 'train'
        val_dir = self.output_base_path / 'val'
        test_dir = self.output_base_path / 'test'
        
        if split_by_class:
            # Organize by class and split each class
            classes = self.organize_by_class(image_files)
            
            for class_label, class_images in classes.items():
                logger.info(f"\nProcessing class '{class_label}'...")
                
                # Split this class
                train_files, val_files, test_files = self.split_dataset(class_images)
                
                # Copy files
                logger.info(f"  Copying train files...")
                self.copy_files(train_files, train_dir, class_label)
                
                logger.info(f"  Copying validation files...")
                self.copy_files(val_files, val_dir, class_label)
                
                logger.info(f"  Copying test files...")
                self.copy_files(test_files, test_dir, class_label)
        else:
            # Split without class organization
            train_files, val_files, test_files = self.split_dataset(image_files)
            
            logger.info("\nCopying files...")
            self.copy_files(train_files, train_dir)
            self.copy_files(val_files, val_dir)
            self.copy_files(test_files, test_dir)
        
        logger.info("\n" + "=" * 80)
        logger.info("Dataset Preparation Complete!")
        logger.info("=" * 80)
        logger.info(f"\nDatasets created at: {self.output_base_path}")
        logger.info(f"  - Train: {train_dir}")
        logger.info(f"  - Val:   {val_dir}")
        logger.info(f"  - Test:  {test_dir}")


def main():
    """
    Main function to run dataset preparation
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Prepare fundus image datasets')
    parser.add_argument(
        '--raw-path',
        type=str,
        default='datasets/fundus/raw',
        help='Path to raw images'
    )
    parser.add_argument(
        '--output-path',
        type=str,
        default='datasets/fundus',
        help='Base output path for organized datasets'
    )
    parser.add_argument(
        '--train-ratio',
        type=float,
        default=0.7,
        help='Training set ratio (default: 0.7)'
    )
    parser.add_argument(
        '--val-ratio',
        type=float,
        default=0.15,
        help='Validation set ratio (default: 0.15)'
    )
    parser.add_argument(
        '--test-ratio',
        type=float,
        default=0.15,
        help='Test set ratio (default: 0.15)'
    )
    parser.add_argument(
        '--no-class-split',
        action='store_true',
        help='Do not organize by class labels'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    
    args = parser.parse_args()
    
    # Create preparator
    preparator = DatasetPreparator(
        raw_data_path=args.raw_path,
        output_base_path=args.output_path,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed
    )
    
    # Prepare datasets
    preparator.prepare_datasets(split_by_class=not args.no_class_split)


if __name__ == '__main__':
    main()
