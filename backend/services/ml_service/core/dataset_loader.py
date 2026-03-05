"""
PyTorch Dataset Loader for Refracto AI
Handles loading of processed fundus images and labels for ML training
"""

import os
import torch
import pandas as pd
from PIL import Image
from torch.utils.data import Dataset
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class RefractoDataset(Dataset):
    """
    Custom PyTorch Dataset for Refracto AI fundus images
    
    Args:
        csv_file (str): Path to the CSV file with labels
        root_dir (str): Directory with all the images
        transform (callable, optional): Optional transform to be applied on images
    """
    
    def __init__(self, csv_file: str, root_dir: str, transform: Optional[Any] = None):
        """
        Initialize the dataset
        
        Args:
            csv_file: Path to CSV file containing image filenames and labels
            root_dir: Directory containing the images
            transform: Optional transforms to apply to images
        """
        # Load CSV file
        self.data_frame = pd.read_csv(csv_file)
        self.root_dir = root_dir
        self.transform = transform
        
        logger.info(f"Loaded dataset with {len(self.data_frame)} images from {csv_file}")
        logger.info(f"Image directory: {root_dir}")
        
        # Log label distribution
        if 'dr_grade' in self.data_frame.columns:
            logger.info(f"DR grade distribution:\n{self.data_frame['dr_grade'].value_counts().sort_index()}")
        if 'glaucoma_flag' in self.data_frame.columns:
            glaucoma_count = self.data_frame['glaucoma_flag'].sum()
            logger.info(f"Glaucoma cases: {glaucoma_count}/{len(self.data_frame)}")
    
    def __len__(self) -> int:
        """
        Return the total number of samples in the dataset
        
        Returns:
            int: Number of samples
        """
        return len(self.data_frame)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """
        Get a sample from the dataset
        
        Args:
            idx: Index of the sample to retrieve
            
        Returns:
            dict: Dictionary containing:
                - 'image': Transformed image tensor
                - 'labels': Dictionary with 'dr' and 'glaucoma' labels
                - 'filename': Original filename for debugging
        """
        if torch.is_tensor(idx):
            idx = idx.tolist()
        
        # Get image filename from dataframe
        img_name = self.data_frame.iloc[idx]['filename']
        img_path = os.path.join(self.root_dir, img_name)
        
        # Load image and convert to RGB
        try:
            image = Image.open(img_path).convert('RGB')
        except Exception as e:
            logger.error(f"Error loading image {img_path}: {str(e)}")
            raise
        
        # Apply transforms if available
        if self.transform:
            image = self.transform(image)
        
        # Get labels
        dr_grade = int(self.data_frame.iloc[idx]['dr_grade'])
        glaucoma_flag = int(self.data_frame.iloc[idx]['glaucoma_flag'])
        
        # Return sample
        return {
            'image': image,
            'labels': {
                'dr': dr_grade,
                'glaucoma': glaucoma_flag
            },
            'filename': img_name
        }
    
    def get_class_counts(self) -> Dict[str, Dict[int, int]]:
        """
        Get the count of samples per class for both DR and glaucoma
        
        Returns:
            dict: Dictionary with class counts
        """
        return {
            'dr': self.data_frame['dr_grade'].value_counts().to_dict(),
            'glaucoma': self.data_frame['glaucoma_flag'].value_counts().to_dict()
        }
    
    def get_sample_weights(self) -> torch.Tensor:
        """
        Calculate sample weights for imbalanced dataset handling
        Useful for WeightedRandomSampler
        
        Returns:
            torch.Tensor: Weight for each sample
        """
        # Calculate inverse frequency weights for DR grades
        dr_counts = self.data_frame['dr_grade'].value_counts()
        total_samples = len(self.data_frame)
        
        weights = []
        for idx in range(len(self.data_frame)):
            dr_grade = self.data_frame.iloc[idx]['dr_grade']
            # Inverse frequency weighting
            weight = total_samples / (len(dr_counts) * dr_counts[dr_grade])
            weights.append(weight)
        
        return torch.DoubleTensor(weights)
