import numpy as np
import pandas as pd
from typing import Dict, List, Any
import logging
from core.evaluation_metrics import ModelEvaluator

logger = logging.getLogger(__name__)

class FairnessMonitor:
    """
    Evaluates algorithmic fairness across specific sub-cohorts 
    (e.g., Age brackets, Diabetes Status, Gender) to ensure generalization.
    """

    @staticmethod
    def calculate_disparate_impact(y_true: np.ndarray, y_pred: np.ndarray, cohort_mask: np.ndarray) -> Dict[str, float]:
        """
        Calculates basic fairness metrics by comparing a protected cohort
        against the general population.
        """
        metrics = {}
        try:
            # Mask for the specific cohort
            cohort_true = y_true[cohort_mask]
            cohort_pred = y_pred[cohort_mask]
            
            # Mask for everyone else
            other_true = y_true[~cohort_mask]
            other_pred = y_pred[~cohort_mask]
            
            # True Positive Rates
            tpr_cohort = np.sum((cohort_true == 1) & (cohort_pred == 1)) / max(1, np.sum(cohort_true == 1))
            tpr_other = np.sum((other_true == 1) & (other_pred == 1)) / max(1, np.sum(other_true == 1))
            
            # Disparate Impact Ratio (TPR cohort / TPR other)
            # Ideal is 1.0. < 0.8 is often considered biased against the cohort.
            metrics['tpr_cohort'] = float(tpr_cohort)
            metrics['tpr_other'] = float(tpr_other)
            metrics['disparate_impact_ratio'] = float(tpr_cohort / max(0.001, tpr_other))
            metrics['equality_of_opportunity_difference'] = float(tpr_cohort - tpr_other)
            
        except Exception as e:
            logger.error(f"Error calculating fairness metrics: {str(e)}")
            
        return metrics

    @classmethod
    def evaluate_cohort_fairness(cls, results_df: pd.DataFrame, target_col: str, pred_col: str, group_col: str) -> Dict[str, Any]:
        """
        Evaluates fairness across different demographic groups.
        results_df should contain the true labels, predictions, and demographic info.
        """
        fairness_report = {}
        unique_groups = results_df[group_col].unique()
        
        for group in unique_groups:
            cohort_mask = (results_df[group_col] == group).values
            
            if np.sum(cohort_mask) < 5:
                # Skip if cohort size is too small
                continue
                
            report = cls.calculate_disparate_impact(
                y_true=results_df[target_col].values,
                y_pred=results_df[pred_col].values,
                cohort_mask=cohort_mask
            )
            report['cohort_size'] = int(np.sum(cohort_mask))
            fairness_report[str(group)] = report
            
        return fairness_report

    @classmethod
    def comprehensive_fairness_report(cls, results_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate a full fairness report across known metadata columns if available in the dataframe.
        """
        report = {}
        
        # We need true labels, predicted classes, and metadata
        demographics = ['age_bracket', 'diabetes_status', 'gender', 'high_myopia']
        
        for demo in demographics:
            if demo in results_df.columns and 'glaucoma_true' in results_df.columns and 'glaucoma_pred' in results_df.columns:
                report[f"{demo}_glaucoma_fairness"] = cls.evaluate_cohort_fairness(
                    results_df, 'glaucoma_true', 'glaucoma_pred', demo
                )
                
            if demo in results_df.columns and 'dr_true' in results_df.columns and 'dr_pred' in results_df.columns:
                 # Fairness for DR might require binarization for disparate impact (e.g., Any DR vs No DR)
                 # This is a simplified example
                 results_df['dr_binary_true'] = (results_df['dr_true'] > 0).astype(int)
                 results_df['dr_binary_pred'] = (results_df['dr_pred'] > 0).astype(int)
                 
                 report[f"{demo}_dr_fairness"] = cls.evaluate_cohort_fairness(
                    results_df, 'dr_binary_true', 'dr_binary_pred', demo
                )
                
        return report
