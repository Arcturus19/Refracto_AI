import numpy as np
import pandas as pd
from typing import List, Iterator, Optional
from torch.utils.data import Sampler
import logging

logger = logging.getLogger(__name__)

class CurriculumSampler(Sampler):
    """
    Implements Curriculum Learning by gradually introducing harder examples 
    during training. (e.g. starting with clear cases of 'No DR' and 'Severe DR', 
    then introducing borderline cases and complex pathologies like High Myopia + Glaucoma).
    """
    
    def __init__(self, dataset_df: pd.DataFrame, batch_size: int, 
                 random_seed: int = 42, initial_difficulty: float = 0.2):
        self.dataset_df = dataset_df.reset_index(drop=True)
        self.batch_size = batch_size
        self.random_state = np.random.RandomState(random_seed)
        
        # Difficulty pacing (0.0 to 1.0)
        self.current_difficulty = initial_difficulty
        self.max_difficulty = 1.0
        
        # Calculate static difficulty for each sample in the dataset
        self._calculate_sample_difficulties()
        
    def _calculate_sample_difficulties(self):
        """
        Computes a difficulty score (0.0 to 1.0) for every sample.
        Easy (0.0): Healthy (DR=0, Glc=0, Emmetropia) or very clear severe cases.
        Hard (1.0): Borderline DR (1, 2), High Myopia combined with Borderline Glaucoma.
        """
        difficulties = np.zeros(len(self.dataset_df))
        
        try:
            for idx, row in self.dataset_df.iterrows():
                diff = 0.0
                
                # DR borderline is harder than clear severe/none
                dr = row.get('dr_class', 0)
                if dr in [1, 2]:
                    diff += 0.3 # Mild/Moderate is harder to distinguish
                
                # Glaucoma with High Myopia (the refracto-pathological link gap)
                glc = row.get('glaucoma_risk', 0)
                hm = row.get('high_myopia', 0)
                if glc == 1 and hm == 1:
                    diff += 0.5 # Clinical gap: High myopia masquerading as Glaucoma
                    
                # Missing modalities makes inference harder
                if pd.isna(row.get('oct_path')) or pd.isna(row.get('fundus_path')):
                    diff += 0.2
                    
                difficulties[idx] = min(1.0, diff)
                
            self.dataset_df['difficulty'] = difficulties
            logger.info(f"Calculated difficulties. Mean: {difficulties.mean():.2f}")
            
        except Exception as e:
            logger.error(f"Error calculating curriculum difficulty: {str(e)}")
            self.dataset_df['difficulty'] = 0.5 # Default fallback

    def update_difficulty(self, epoch: int, total_epochs: int):
        """
        Increases the allowed difficulty linearly based on training progress.
        """
        # Starts at initial_difficulty, hits 1.0 halfway through training
        progress = min(1.0, epoch / (total_epochs * 0.6))
        
        new_diff = self.current_difficulty + (self.max_difficulty - self.current_difficulty) * progress
        self.current_difficulty = min(1.0, max(self.current_difficulty, new_diff))
        
        logger.info(f"Epoch {epoch}: Curriculum difficulty adjusted to {self.current_difficulty:.2f}")

    def __iter__(self) -> Iterator[int]:
        """
        Yields indices for the dataloader up to the current difficulty threshold.
        """
        # Filter indices where difficulty <= current_difficulty
        valid_indices = self.dataset_df.index[self.dataset_df['difficulty'] <= self.current_difficulty].tolist()
        
        if not valid_indices:
            valid_indices = self.dataset_df.index.tolist() # Fallback if too strict
            
        # Shuffle valid indices
        self.random_state.shuffle(valid_indices)
        
        # Yield batches
        batch = []
        for idx in valid_indices:
            batch.append(idx)
            if len(batch) == self.batch_size:
                yield batch
                batch = []
        
        # Yield remaining elements
        if batch:
            yield batch

    def __len__(self) -> int:
        valid_count = len(self.dataset_df[self.dataset_df['difficulty'] <= self.current_difficulty])
        return (valid_count + self.batch_size - 1) // self.batch_size
