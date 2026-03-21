"""Refracto-pathological linking module for H2 hypothesis validation (P0.2)."""

from __future__ import annotations

from typing import Tuple

import torch
import torch.nn as nn

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
    
    def _clamp_sphere(self, sphere: torch.Tensor) -> torch.Tensor:
        """Clamp sphere to the configured valid range."""
        return torch.clamp(sphere, self.sphere_min, self.sphere_max)

    def get_correction_factor(self, predicted_sphere: torch.Tensor) -> torch.Tensor:
        """Return deterministic correction factor in [0.5, 1.5].

        This is intentionally monotonic and deterministic so that:
        - Myopia (negative sphere) reduces glaucoma confidence
        - Hyperopia (positive sphere) increases glaucoma confidence
        - Emmetropia (~0D) has minimal correction
        """
        sphere = self._clamp_sphere(predicted_sphere)

        # Simple monotonic mapping: +0.05 per diopter.
        # -20D -> 0.0 (clamped to 0.5), 0D -> 1.0, +10D -> 1.5.
        correction_factor = 1.0 + 0.05 * sphere
        return torch.clamp(correction_factor, 0.5, 1.5)
    
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
        correction_factor = self.get_correction_factor(predicted_sphere)  # (B,)
        
        # Apply to glaucoma positive class logit (index 1)
        corrected_logits = glaucoma_logits.clone()
        corrected_logits[:, 1] = corrected_logits[:, 1] * correction_factor
        
        return corrected_logits
    
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
