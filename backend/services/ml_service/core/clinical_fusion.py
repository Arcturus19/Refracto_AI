import torch
import torch.nn as nn

class ClinicalDataEncoder(nn.Module):
    """Encodes structured clinical metadata to be fused with visual features.
    
    Expected clinical features:
        0: Age (normalized: age / 100.0)
        1: IOP (normalized: iop / 40.0)
        2: Diabetes Status (0=No, 1=Yes)
        3: Spherical Equivalent (normalized: (se + 20) / 30.0)
        4: Gender (binary: 0=Male, 1=Female)
        5: Modality Present (Fundus=1, OCT=1, Both=2) (Optional proxy)

    Output:
        A dense vector of dimension `encoded_dim` suitable for concatenation
        with the visual feature embedding.
    """
    
    def __init__(self, input_dim: int = 5, encoded_dim: int = 64):
        super().__init__()
        self.input_dim = input_dim
        self.encoded_dim = encoded_dim
        
        # A simple Multi-Layer Perceptron (MLP) acting as a strong
        # feature extractor for structured data (Gradient Boosting proxy)
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, encoded_dim),
            nn.BatchNorm1d(encoded_dim),
            nn.ReLU()
        )
        
    def forward(self, clinical_features: torch.Tensor) -> torch.Tensor:
        """
        Args:
            clinical_features: (B, input_dim) tensor of structured data.
            
        Returns:
            encoded_clinical: (B, encoded_dim) tensor
        """
        # Ensure 2D input
        if clinical_features.dim() == 1:
            clinical_features = clinical_features.unsqueeze(0)
            
        return self.encoder(clinical_features)
