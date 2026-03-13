import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class DataHarmonizer:
    """
    Harmonizes external datasets (RFMiD, GAMMA) into the unified 
    Refracto AI schema required for multi-task training (DR, Glaucoma, Refraction).
    """
    
    # Unified Target Schema
    UNI_COLS = ["patient_id", "fundus_path", "oct_path", "dr_class", "glaucoma_risk", 
                "sphere", "cylinder", "axis", "age", "iop", "diabetes_status", "gender", "high_myopia"]

    @staticmethod
    def map_dr_severity(label: str) -> int:
        """
        Maps various DR labels to ICD (0-4).
        """
        label = str(label).lower().strip()
        if label in ['0', 'normal', 'none', 'no_dr']: return 0
        if label in ['1', 'mild', 'npdr_mild']: return 1
        if label in ['2', 'moderate', 'npdr_moderate']: return 2
        if label in ['3', 'severe', 'npdr_severe']: return 3
        if label in ['4', 'proliferative', 'pdr']: return 4
        
        # Default fallback
        logger.warning(f"Unrecognized DR label: {label}, mapping to 0")
        return 0

    @classmethod
    def process_rfmid(cls, df: pd.DataFrame, base_img_dir: Path) -> pd.DataFrame:
        """
        Processes RFMiD Challenge dataset.
        Usually only contains Fundus images and various disease presence labels.
        """
        harmonized = pd.DataFrame(columns=cls.UNI_COLS)
        
        # RFMiD has columns like 'id', 'Disease_Risk', 'DR', etc.
        try:
            harmonized['patient_id'] = "rfmid_" + df['id'].astype(str)
            harmonized['fundus_path'] = df['id'].astype(str).apply(lambda x: str(base_img_dir / f"{x}.png"))
            harmonized['dr_class'] = df.get('DR', 0).apply(cls.map_dr_severity)
            
            # Binary target for Glaucoma risk (0 or 1)
            harmonized['glaucoma_risk'] = df.get('GLC', 0).astype(int)
            
            # Fill missing required modalities/clinical data with NaN or defaults
            harmonized['oct_path'] = None
            harmonized['sphere'] = 0.0
            harmonized['cylinder'] = 0.0
            harmonized['axis'] = 0.0
            harmonized['age'] = 50.0 # Default missing
            harmonized['iop'] = 15.0 # Default missing
            harmonized['diabetes_status'] = harmonized['dr_class'].apply(lambda x: 1.0 if x > 0 else 0.0)
            harmonized['gender'] = 0.0
            harmonized['high_myopia'] = df.get('MYA', 0).astype(int)
            
        except Exception as e:
            logger.error(f"Error parsing RFMiD dataset: {str(e)}")
            
        return harmonized

    @classmethod
    def process_gamma(cls, df: pd.DataFrame, base_img_dir: Path) -> pd.DataFrame:
        """
        Processes GAMMA Challenge dataset.
        Contains paired Fundus and OCT images, mainly for Glaucoma.
        """
        harmonized = pd.DataFrame(columns=cls.UNI_COLS)
        
        try:
            harmonized['patient_id'] = "gamma_" + df['id'].astype(str)
            harmonized['fundus_path'] = df['id'].astype(str).apply(lambda x: str(base_img_dir / "fundus" / f"{x}.jpg"))
            harmonized['oct_path'] = df['id'].astype(str).apply(lambda x: str(base_img_dir / "oct" / f"{x}.nii.gz"))
            
            # GAMMA DR is usually not explicitly labeled 0-4 unless provided, defaulting to 0
            harmonized['dr_class'] = 0 
            
            # GAMMA provides glaucoma labels (0: none, 1: early, 2: advanced -> binary)
            glc = df.get('glaucoma_grade', 0).astype(int)
            harmonized['glaucoma_risk'] = (glc > 0).astype(int)
            
            # Spherical equivalent sometimes provided in GAMMA
            se = df.get('spherical_equivalent', 0.0)
            harmonized['sphere'] = se
            harmonized['cylinder'] = 0.0
            harmonized['axis'] = 0.0
            harmonized['high_myopia'] = (se <= -6.0).astype(int)
            
            # Clinical
            harmonized['age'] = df.get('age', 50.0).astype(float)
            harmonized['iop'] = 15.0
            harmonized['diabetes_status'] = 0.0
            harmonized['gender'] = df.get('gender', 0).apply(lambda x: 1.0 if str(x).lower() in ['f', 'female'] else 0.0)
            
        except Exception as e:
            logger.error(f"Error parsing GAMMA dataset: {str(e)}")
            
        return harmonized

    @classmethod
    def merge_datasets(cls, datasets: List[pd.DataFrame]) -> pd.DataFrame:
        """Merges harmonized datasets into a single unified dataframe pool."""
        if not datasets:
            return pd.DataFrame(columns=cls.UNI_COLS)
            
        merged = pd.concat(datasets, ignore_index=True)
        # Drop entries without any images
        merged = merged.dropna(subset=['fundus_path', 'oct_path'], how='all')
        
        logger.info(f"Merged {len(datasets)} datasets. Total unified records: {len(merged)}")
        return merged
