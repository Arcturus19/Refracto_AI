"""Refracto-pathological linking module for H2 hypothesis validation (P0.2)."""
import torch
import torch.nn as nn
from typing import Tuple

class RefractoPathologicalLink(nn.Module):
    """Models myopia ↔ glaucoma relationship for H2 hypothesis.
    
    High myopia (negative sphere) is associated with larger optic disc,
    which increases false-positive glaucoma diagnoses. This module learns
    to correct for this artifact by modulating glaucoma predictions based
    on predicted refraction severity.
    
    H2 Hypothesis: Refracto-pathological linking reduces false positives
    in high myopia cases by 50%+ compared to naive predictions.
    """
    
    def __init__(self, sphere_min: float = -20.0, sphere_max: float = 10.0):
        super().__init__()
        self.sphere_min = sphere_min
        self.sphere_max = sphere_max
        
        # Learnable correction curve (polynomial fit via MLP)
        # Maps sphere severity → glaucoma correction factor (0.0 to 1.0)
        self.correction_curve = nn.Sequential(
            nn.Linear(1, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()  # Output 0.0 to 1.0
        )
    
    def normalize_sphere(self, sphere: torch.Tensor) -> torch.Tensor:
        """Normalize sphere from [-20, +10] to [-1, +1] range.
        
        Args:
            sphere: (B,) predicted sphere values in diopters
        
        Returns:
            normalized: (B,) values in [-1, 1]
        """
        # Clamp to valid range
        sphere = torch.clamp(sphere, self.sphere_min, self.sphere_max)
        
        # Map to [-1, 1]
        normalized = 2 * (sphere - self.sphere_min) / (self.sphere_max - self.sphere_min) - 1
        return normalized
    
    def forward(self, glaucoma_logits: torch.Tensor, predicted_sphere: torch.Tensor) -> torch.Tensor:
        """Apply myopia correction to glaucoma predictions.
        
        Args:
            glaucoma_logits: (B, 2) raw logits from glaucoma head [healthy, glaucoma]
            predicted_sphere: (B,) predicted sphere values from refraction head
        
        Returns:
            corrected_logits: (B, 2) adjusted glaucoma logits
        
        Logic:
            - High myopia (sphere < -6.0) reduces glaucoma confidence (FPR correction)
            - High hyperopia (sphere > 4.0) increases glaucoma confidence
            - Emmetropia (0 ± 2) has near-neutral correction
        """
        B = glaucoma_logits.shape[0]
        
        # Normalize sphere to [-1, 1]
        sphere_norm = self.normalize_sphere(predicted_sphere)  # (B,)
        sphere_norm = sphere_norm.unsqueeze(1)  # (B, 1)
        
        # Get correction factor (0 to 1 via sigmoid)
        correction_factor = self.correction_curve(sphere_norm)  # (B, 1)
        
        # Scale to [0.5, 1.5] range
        # High myopia → factor ≈ 0.7 (reduces glaucoma by 30%)
        # Emmetropia → factor ≈ 1.0 (no change)
        # Hyperopia → factor ≈ 1.2 (increases glaucoma by 20%)
        correction_factor = 0.5 + correction_factor * 1.0  # Maps [0, 1] → [0.5, 1.5]
        
        # Apply to glaucoma positive class logit (index 1)
        corrected_logits = glaucoma_logits.clone()
        corrected_logits[:, 1] = corrected_logits[:, 1] * correction_factor.squeeze(1)
        
        return corrected_logits
    
    def get_correction_factor(self, predicted_sphere: torch.Tensor) -> torch.Tensor:
        """Only return correction factor (for logging/debugging).
        
        Args:
            predicted_sphere: (B,) sphere values
        
        Returns:
            correction_factor: (B,) in range [0.5, 1.5]
        """
        sphere_norm = self.normalize_sphere(predicted_sphere).unsqueeze(1)
        raw_factor = self.correction_curve(sphere_norm)  # (B, 1)
        correction_factor = 0.5 + raw_factor * 1.0
        return correction_factor.squeeze(1)


def apply_refracto_link(glaucoma_logits: torch.Tensor, refraction: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    """Functional form of refracto-pathological linking.
    
    Args:
        glaucoma_logits: (B, 2) raw glaucoma predictions
        refraction: (B, 3) where [0] is sphere
    
    Returns:
        corrected_logits: (B, 2) after correction
        correction_factor: (B,) applied correction factors
    """
    link = RefractoPathologicalLink()
    sphere = refraction[:, 0]  # Extract sphere
    corrected = link(glaucoma_logits, sphere)
    correction = link.get_correction_factor(sphere)
    
    return corrected, correction
