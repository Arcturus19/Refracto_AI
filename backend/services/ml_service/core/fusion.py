"""Multi-head attention-based fusion of Fundus and OCT features (P0.1)."""
import torch
import torch.nn as nn
from typing import Tuple, Optional

class MultiHeadFusion(nn.Module):
    """Multi-head attention-based fusion of Fundus and OCT features.
    
    Combines 1000-dim Fundus features (EfficientNet-B3) with 768-dim OCT features (ViT)
    into 512-dim fused representation using scaled dot-product attention.
    
    Input shapes:
        - fundus_features: (B, 1000) or (B, 1, 1000)
        - oct_features: (B, 768) or (B, 1, 768)
    
    Output shape:
        - fused_features: (B, 512)
    """
    
    def __init__(self, fundus_dim: int = 1000, oct_dim: int = 768, fused_dim: int = 512, num_heads: int = 8):
        super().__init__()
        self.fundus_dim = fundus_dim
        self.oct_dim = oct_dim
        self.fused_dim = fused_dim
        self.num_heads = num_heads
        
        # Project inputs to common dimension
        self.fundus_proj = nn.Linear(fundus_dim, fused_dim)
        self.oct_proj = nn.Linear(oct_dim, fused_dim)
        
        # Multi-head attention: OCT attends to Fundus
        self.attention = nn.MultiheadAttention(
            fused_dim, num_heads, batch_first=True, dropout=0.1
        )
        
        # Fusion gate: learn which modality to emphasize
        self.gate = nn.Sequential(
            nn.Linear(fused_dim * 2, fused_dim),
            nn.Sigmoid()
        )
        
        # Output normalization
        self.norm = nn.LayerNorm(fused_dim)
        
    def forward(self, fundus_features: torch.Tensor, oct_features: torch.Tensor) -> torch.Tensor:
        """Forward pass: fuse two modalities.
        
        Args:
            fundus_features: (B, 1000) or (B, 1, 1000)
            oct_features: (B, 768) or (B, 1, 768)
        
        Returns:
            fused_features: (B, 512) fused representation
        """
        # Ensure 2D input
        if fundus_features.dim() == 3:
            fundus_features = fundus_features.squeeze(1)
        if oct_features.dim() == 3:
            oct_features = oct_features.squeeze(1)
        
        # Project to common space
        fundus_proj = self.fundus_proj(fundus_features)  # (B, 512)
        oct_proj = self.oct_proj(oct_features)  # (B, 512)
        
        # Attention: OCT attends to Fundus
        fundus_expanded = fundus_proj.unsqueeze(1)  # (B, 1, 512)
        oct_expanded = oct_proj.unsqueeze(1)  # (B, 1, 512)
        
        attended, _ = self.attention(oct_expanded, fundus_expanded, fundus_expanded)
        attended = attended.squeeze(1)  # (B, 512)
        
        # Gating mechanism: interpolate between fundus and attended OCT
        concat = torch.cat([fundus_proj, attended], dim=1)  # (B, 1024)
        gate = self.gate(concat)  # (B, 512)
        
        # Fused output: weighted combination
        fused = gate * fundus_proj + (1 - gate) * attended
        fused = self.norm(fused)
        
        return fused


class MultiTaskFusionHead(nn.Module):
    """Shared encoder with multi-task prediction heads (P0.1).
    
    Takes fused features and produces 3 task outputs:
    1. DR severity (5-class classification)
    2. Glaucoma risk (binary classification)
    3. Refraction parameters (3-value regression: sphere, cylinder, axis)
    """
    
    def __init__(self, input_dim: int = 512, num_dr_classes: int = 5, num_glaucoma_classes: int = 2):
        super().__init__()
        
        # Shared dense layers after fusion
        self.shared = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        # Task 1: DR severity (5-class: 0=no DR to 4=severe)
        self.dr_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, num_dr_classes)
        )
        
        # Task 2: Glaucoma (binary: 0=healthy, 1=glaucoma)
        self.glaucoma_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, num_glaucoma_classes)
        )
        
        # Task 3: Refraction (3-value regression: sphere, cylinder, axis)
        self.refraction_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 3)
        )
    
    def forward(self, fused_features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Multi-task prediction.
        
        Args:
            fused_features: (B, 512) from MultiHeadFusion
        
        Returns:
            dr_logits: (B, 5) for 5 DR classes
            glaucoma_logits: (B, 2) for glaucoma (healthy/glaucoma)
            refraction: (B, 3) for (Sphere, Cylinder, Axis)
        """
        shared = self.shared(fused_features)
        
        dr_logits = self.dr_head(shared)
        glaucoma_logits = self.glaucoma_head(shared)
        refraction = self.refraction_head(shared)
        
        return dr_logits, glaucoma_logits, refraction
