"""
Logic Engine for Refracto AI
Implements hybrid rule-based logic for clinical decision support
Combines AI predictions with domain knowledge rules
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk level enumeration"""
    NONE = "None"
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class ClinicalWarning:
    """Clinical warning data structure"""
    
    def __init__(
        self,
        warning_type: str,
        risk_level: RiskLevel,
        explanation: str,
        recommendation: str
    ):
        self.warning_type = warning_type
        self.risk_level = risk_level
        self.explanation = explanation
        self.recommendation = recommendation
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "warning_type": self.warning_type,
            "risk_level": self.risk_level.value,
            "explanation": self.explanation,
            "recommendation": self.recommendation
        }


class LogicEngine:
    """
    Hybrid logic engine for clinical decision support
    Applies rule-based analysis on top of AI predictions
    """
    
    def __init__(self):
        """Initialize the logic engine"""
        self.rules_applied = 0
        self.warnings_generated = 0
    
    def analyze_risk(
        self,
        refraction_data: Dict,
        pathology_data: Dict
    ) -> Dict:
        """
        Analyze clinical risk by combining refraction and pathology data
        
        Args:
            refraction_data: Dictionary with keys 'sphere', 'cylinder', 'axis'
            pathology_data: Dictionary with DR and glaucoma scores/grades
            
        Returns:
            Dictionary containing warnings and recommendations
        """
        warnings = []
        
        # Extract data
        sphere = refraction_data.get('sphere', 0)
        cylinder = refraction_data.get('cylinder', 0)
        
        glaucoma_score = pathology_data.get('glaucoma_risk', 0)
        dr_grade = pathology_data.get('dr_grade', 0)
        
        logger.info(f"Analyzing risk: Sphere={sphere:.2f}, Glaucoma={glaucoma_score:.2f}, DR Grade={dr_grade}")
        
        # Rule 1: Myopic Artifact Risk
        myopic_warning = self._check_myopic_artifact_risk(sphere, glaucoma_score)
        if myopic_warning:
            warnings.append(myopic_warning)
        
        # Rule 2: High Myopia with Diabetic Retinopathy
        myopia_dr_warning = self._check_high_myopia_with_dr(sphere, dr_grade)
        if myopia_dr_warning:
            warnings.append(myopia_dr_warning)
        
        # Rule 3: Astigmatism with Pathology
        astigmatism_warning = self._check_astigmatism_correlation(cylinder, pathology_data)
        if astigmatism_warning:
            warnings.append(astigmatism_warning)
        
        # Rule 4: Combined High-Risk Indicators
        combined_warning = self._check_combined_risk(refraction_data, pathology_data)
        if combined_warning:
            warnings.append(combined_warning)
        
        self.rules_applied += 4
        self.warnings_generated += len(warnings)
        
        return {
            "warnings": [w.to_dict() for w in warnings],
            "total_warnings": len(warnings),
            "risk_summary": self._generate_risk_summary(warnings),
            "requires_specialist_review": len(warnings) > 0
        }
    
    def _check_myopic_artifact_risk(
        self,
        sphere: float,
        glaucoma_score: float
    ) -> Optional[ClinicalWarning]:
        """
        Rule 1: Check for myopic artifact risk
        
        High myopia can cause optic disc changes that mimic glaucoma
        """
        # IF sphere < -6.00 (High Myopia) AND glaucoma_score > 0.5
        if sphere < -6.00 and glaucoma_score > 0.5:
            return ClinicalWarning(
                warning_type="myopic_artifact_risk",
                risk_level=RiskLevel.HIGH,
                explanation=f"Patient has High Myopia ({sphere:+.2f}D). The observed optic disc changes may be due to myopic tilt rather than Glaucoma. Clinical correlation recommended.",
                recommendation="Recommend OCT imaging of optic nerve head, visual field testing, and specialist ophthalmology consultation to differentiate between myopic changes and true glaucomatous damage."
            )
        
        return None
    
    def _check_high_myopia_with_dr(
        self,
        sphere: float,
        dr_grade: int
    ) -> Optional[ClinicalWarning]:
        """
        Rule 2: Check for high myopia with diabetic retinopathy
        
        High myopia can complicate DR diagnosis and treatment
        """
        if sphere < -6.00 and dr_grade >= 2:
            return ClinicalWarning(
                warning_type="high_myopia_with_dr",
                risk_level=RiskLevel.MODERATE,
                explanation=f"Patient has both High Myopia ({sphere:+.2f}D) and Moderate/Severe Diabetic Retinopathy (Grade {dr_grade}). Retinal changes may be more extensive than typical.",
                recommendation="Consider wide-field fundus imaging. Monitor for retinal detachment risk. Coordinate care between retina specialist and optometrist for optimal refractive correction."
            )
        
        return None
    
    def _check_astigmatism_correlation(
        self,
        cylinder: float,
        pathology_data: Dict
    ) -> Optional[ClinicalWarning]:
        """
        Rule 3: Check for significant astigmatism
        
        High astigmatism can affect image quality and diagnosis
        """
        if abs(cylinder) > 3.00:
            return ClinicalWarning(
                warning_type="high_astigmatism",
                risk_level=RiskLevel.LOW,
                explanation=f"Significant astigmatism detected ({cylinder:.2f}D). This may affect fundus image quality and clarity of retinal features.",
                recommendation="Ensure proper optical correction during imaging. Consider repeating imaging with optimal refractive correction if image quality is suboptimal."
            )
        
        return None
    
    def _check_combined_risk(
        self,
        refraction_data: Dict,
        pathology_data: Dict
    ) -> Optional[ClinicalWarning]:
        """
        Rule 4: Check for combined high-risk factors
        
        Multiple risk factors increase overall patient risk
        """
        sphere = refraction_data.get('sphere', 0)
        glaucoma_score = pathology_data.get('glaucoma_risk', 0)
        dr_grade = pathology_data.get('dr_grade', 0)
        
        # Critical: High myopia + high glaucoma risk + significant DR
        if sphere < -6.00 and glaucoma_score > 0.7 and dr_grade >= 3:
            return ClinicalWarning(
                warning_type="multiple_risk_factors",
                risk_level=RiskLevel.CRITICAL,
                explanation=f"Multiple high-risk factors detected: High Myopia ({sphere:+.2f}D), High Glaucoma Risk ({glaucoma_score:.2%}), and Severe DR (Grade {dr_grade}). This combination significantly increases risk of vision-threatening complications.",
                recommendation="URGENT: Immediate referral to retina specialist and glaucoma specialist. Comprehensive ophthalmologic evaluation within 1-2 weeks. Consider patient for intensive monitoring protocol."
            )
        
        # Moderate: Moderate myopia + moderate risks
        elif sphere < -4.00 and (glaucoma_score > 0.5 or dr_grade >= 2):
            return ClinicalWarning(
                warning_type="moderate_combined_risk",
                risk_level=RiskLevel.MODERATE,
                explanation=f"Moderate combined risk factors: Myopia ({sphere:+.2f}D) with pathological findings. Regular monitoring recommended.",
                recommendation="Schedule comprehensive eye examination. Consider 3-6 month follow-up interval. Monitor progression of both refractive and pathological changes."
            )
        
        return None
    
    def _generate_risk_summary(self, warnings: List[ClinicalWarning]) -> str:
        """
        Generate a summary of identified risks
        
        Args:
            warnings: List of clinical warnings
            
        Returns:
            Summary string
        """
        if not warnings:
            return "No significant risk factors identified based on current analysis."
        
        # Count by risk level
        critical = sum(1 for w in warnings if w.risk_level == RiskLevel.CRITICAL)
        high = sum(1 for w in warnings if w.risk_level == RiskLevel.HIGH)
        moderate = sum(1 for w in warnings if w.risk_level == RiskLevel.MODERATE)
        low = sum(1 for w in warnings if w.risk_level == RiskLevel.LOW)
        
        summary_parts = []
        
        if critical > 0:
            summary_parts.append(f"{critical} CRITICAL risk factor(s)")
        if high > 0:
            summary_parts.append(f"{high} HIGH risk factor(s)")
        if moderate > 0:
            summary_parts.append(f"{moderate} MODERATE risk factor(s)")
        if low > 0:
            summary_parts.append(f"{low} LOW risk factor(s)")
        
        summary = "Identified: " + ", ".join(summary_parts)
        
        if critical > 0 or high > 0:
            summary += ". Specialist consultation strongly recommended."
        
        return summary
    
    def get_stats(self) -> Dict:
        """Get logic engine statistics"""
        return {
            "rules_applied": self.rules_applied,
            "warnings_generated": self.warnings_generated
        }


# Singleton instance
_logic_engine_instance: Optional[LogicEngine] = None


def get_logic_engine() -> LogicEngine:
    """
    Get or create the singleton LogicEngine instance
    
    Returns:
        LogicEngine instance
    """
    global _logic_engine_instance
    
    if _logic_engine_instance is None:
        _logic_engine_instance = LogicEngine()
    
    return _logic_engine_instance


# Convenience function
def analyze_clinical_risk(
    refraction_data: Dict,
    pathology_data: Dict
) -> Dict:
    """
    Convenience function to analyze clinical risk
    
    Args:
        refraction_data: Refraction measurements
        pathology_data: Pathology predictions
        
    Returns:
        Risk analysis results
    """
    engine = get_logic_engine()
    return engine.analyze_risk(refraction_data, pathology_data)
