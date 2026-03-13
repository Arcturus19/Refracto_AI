"""Clinical Concordance Rate (CCR) framework for expert validation (P0.5)."""
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class ExpertReview:
    """Single expert's assessment of AI prediction (immutable)."""
    review_id: str
    case_id: str
    expert_id: str
    dr_agreement: int  # 1-5 Likert scale (1=strongly disagree, 5=strongly agree)
    glaucoma_agreement: int  # 1-5
    refraction_agreement: int  # 1-5
    confidence: float  # Expert confidence in their assessment (0-1)
    comments: Optional[str]
    timestamp: str  # ISO 8601


class ClinicalConcordanceManager:
    """Manage expert panel reviews and calculate CCR metrics.
    
    Clinical Concordance Rate (CCR) measures agreement between AI predictions
    and expert ophthalmologists using 5-point Likert scales.
    
    H3 Hypothesis: CCR ≥ 85% demonstrates sufficient clinical utility.
    """
    
    def __init__(self, min_experts_per_case: int = 3):
        self.min_experts_per_case = min_experts_per_case
        self.reviews: List[ExpertReview] = []
        self.cases: Dict[str, List[ExpertReview]] = {}  # case_id → [reviews]
    
    def add_review(self, review: ExpertReview) -> None:
        """Record expert review (immutable append).
        
        Args:
            review: ExpertReview to record
        """
        self.reviews.append(review)
        
        if review.case_id not in self.cases:
            self.cases[review.case_id] = []
        
        self.cases[review.case_id].append(review)
    
    def calculate_ccr_for_case(self, case_id: str) -> Optional[Dict]:
        """Calculate CCR for single case across all expert reviews.
        
        Agreement defined as Likert score ≥ 4 (agree + strongly agree).
        
        Args:
            case_id: Unique case identifier
        
        Returns:
            Dict with CCR metrics, or None if insufficient reviews
        """
        if case_id not in self.cases or len(self.cases[case_id]) < self.min_experts_per_case:
            return None
        
        reviews = self.cases[case_id]
        n = len(reviews)
        
        # Count agreements per task (Likert ≥ 4)
        dr_agreeing = sum(1 for r in reviews if r.dr_agreement >= 4)
        glaucoma_agreeing = sum(1 for r in reviews if r.glaucoma_agreement >= 4)
        refraction_agreeing = sum(1 for r in reviews if r.refraction_agreement >= 4)
        
        return {
            "case_id": case_id,
            "dr_ccr": float(dr_agreeing / n),
            "glaucoma_ccr": float(glaucoma_agreeing / n),
            "refraction_ccr": float(refraction_agreeing / n),
            "overall_ccr": float((dr_agreeing + glaucoma_agreeing + refraction_agreeing) / (3 * n)),
            "reviewer_count": n,
            "confidence_mean": float(sum(r.confidence for r in reviews) / n)
        }
    
    def calculate_global_ccr(self) -> Dict:
        """Calculate aggregate CCR across ALL reviewed cases.
        
        H3 Hypothesis Success: Global CCR >= 0.85 (85%).
        
        Returns:
            Dict with global metrics and hypothesis status
        """
        if not self.cases:
            return {"error": "No cases reviewed"}
        
        case_ccrs = []
        case_details = []
        
        # Calculate CCR for each case (with sufficient reviews)
        for case_id in self.cases.keys():
            ccr = self.calculate_ccr_for_case(case_id)
            if ccr is not None:
                case_ccrs.append(ccr["overall_ccr"])
                case_details.append(ccr)
        
        if not case_ccrs:
            return {"error": "Insufficient reviews per case (need ≥3 per case)"}
        
        # Global metrics
        global_ccr = sum(case_ccrs) / len(case_ccrs)
        h3_status = "PASS" if global_ccr >= 0.85 else "FAIL"
        
        return {
            "global_ccr": float(global_ccr),
            "h3_hypothesis_status": h3_status,
            "h3_threshold": 0.85,
            "cases_analyzed": len(case_ccrs),
            "total_reviews": len(self.reviews),
            "min_case_ccr": float(min(case_ccrs)),
            "max_case_ccr": float(max(case_ccrs)),
            "case_details": case_details,
            "interpretation": f"Expert panel agrees with AI predictions {global_ccr*100:.1f}% of the time. "
                            f"H3 hypothesis: {'VALIDATED ✓' if h3_status == 'PASS' else 'NOT YET ACHIEVED'}"
        }
    
    def get_expert_performance(self, expert_id: str) -> Dict:
        """Get individual expert's review metrics.
        
        Args:
            expert_id: Expert identifier
        
        Returns:
            Performance metrics for this expert
        """
        expert_reviews = [r for r in self.reviews if r.expert_id == expert_id]
        
        if not expert_reviews:
            return {"error": "No reviews from this expert"}
        
        # Agreement distribution
        dr_mean = sum(r.dr_agreement for r in expert_reviews) / len(expert_reviews)
        glaucoma_mean = sum(r.glaucoma_agreement for r in expert_reviews) / len(expert_reviews)
        refraction_mean = sum(r.refraction_agreement for r in expert_reviews) / len(expert_reviews)
        confidence_mean = sum(r.confidence for r in expert_reviews) / len(expert_reviews)
        
        return {
            "expert_id": expert_id,
            "review_count": len(expert_reviews),
            "dr_mean_agreement": float(dr_mean),
            "glaucoma_mean_agreement": float(glaucoma_mean),
            "refraction_mean_agreement": float(refraction_mean),
            "confidence_mean": float(confidence_mean)
        }
    
    def export_for_analysis(self) -> Dict:
        """Export all reviews for statistical analysis.
        
        Returns:
            Complete dataset for external analysis tools
        """
        return {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "total_reviews": len(self.reviews),
                "total_cases": len(self.cases),
                "total_experts": len(set(r.expert_id for r in self.reviews))
            },
            "reviews": [asdict(r) for r in self.reviews],
            "global_ccr": self.calculate_global_ccr()
        }
