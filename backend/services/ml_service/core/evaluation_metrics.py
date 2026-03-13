import numpy as np
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score, balanced_accuracy_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, confusion_matrix
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class ModelEvaluator:
    """
    Calculates academic metrics required for the Hybrid XAI thesis proposal.
    Matches the specific requirements for DR (multi-class), Glaucoma (binary),
    and Refraction (regression).
    """

    @staticmethod
    def evaluate_dr_performance(y_true: np.ndarray, y_pred_prob: np.ndarray, y_pred_class: np.ndarray) -> Dict[str, float]:
        """
        Evaluate Diabetic Retinopathy (5-class classification).
        """
        metrics = {}
        try:
            metrics['accuracy'] = float(accuracy_score(y_true, y_pred_class))
            metrics['balanced_accuracy'] = float(balanced_accuracy_score(y_true, y_pred_class))
            metrics['f1_macro'] = float(f1_score(y_true, y_pred_class, average='macro'))
            metrics['f1_weighted'] = float(f1_score(y_true, y_pred_class, average='weighted'))
            
            # AUC requires handling multi-class format
            # y_pred_prob should be (N_samples, N_classes)
            if y_pred_prob.ndim == 2 and y_pred_prob.shape[1] > 1:
                metrics['auc_ovr'] = float(roc_auc_score(y_true, y_pred_prob, multi_class='ovr'))
        except Exception as e:
            logger.error(f"Error calculating DR metrics: {str(e)}")
            
        return metrics

    @staticmethod
    def evaluate_glaucoma_performance(y_true: np.ndarray, y_pred_prob: np.ndarray, y_pred_class: np.ndarray) -> Dict[str, float]:
        """
        Evaluate Glaucoma Risk (Binary classification).
        Uses Sensitivity and Specificity which are clinically important.
        """
        metrics = {}
        try:
            metrics['accuracy'] = float(accuracy_score(y_true, y_pred_class))
            metrics['f1'] = float(f1_score(y_true, y_pred_class))
            
            # Probability for class 1
            if y_pred_prob.ndim == 2:
                prob_class_1 = y_pred_prob[:, 1]
            else:
                prob_class_1 = y_pred_prob
                
            metrics['auc'] = float(roc_auc_score(y_true, prob_class_1))
            
            # Sensitivity (Recall) and Specificity from confusion matrix
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred_class, labels=[0, 1]).ravel()
            metrics['sensitivity'] = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            metrics['specificity'] = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating Glaucoma metrics: {str(e)}")
            
        return metrics

    @staticmethod
    def evaluate_refraction_performance(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Dict[str, float]]:
        """
        Evaluate Refraction (Regression: Sphere, Cylinder, Axis).
        """
        metrics = {'sphere': {}, 'cylinder': {}, 'axis': {}}
        try:
            # Assuming y_true and y_pred are (N_samples, 3) where columns are Sphere, Cylinder, Axis
            for i, name in enumerate(['sphere', 'cylinder', 'axis']):
                true_vals = y_true[:, i]
                pred_vals = y_pred[:, i]
                
                metrics[name]['mae'] = float(mean_absolute_error(true_vals, pred_vals))
                metrics[name]['rmse'] = float(np.sqrt(mean_squared_error(true_vals, pred_vals)))
                
                # Clinical tolerance (e.g., within 0.5 Diopters for Sphere/Cyl)
                if name in ['sphere', 'cylinder']:
                    within_05d = np.mean(np.abs(true_vals - pred_vals) <= 0.5)
                    metrics[name]['accuracy_within_0.5D'] = float(within_05d)
                elif name == 'axis':
                    # Axis is circular (0-180), evaluate within 10 degrees
                    diffs = np.abs(true_vals - pred_vals)
                    # Correct for circular nature
                    diffs = np.minimum(diffs, 180 - diffs)
                    within_10deg = np.mean(diffs <= 10.0)
                    metrics[name]['accuracy_within_10deg'] = float(within_10deg)
                    
        except Exception as e:
            logger.error(f"Error calculating Refraction metrics: {str(e)}")
            
        return metrics

    @classmethod
    def generate_comprehensive_report(cls, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregates results from validation batches into a full report.
        results expects: {'dr_true': [], 'dr_prob': [], 'dr_pred': [], ...}
        """
        report = {}
        
        # DR
        if 'dr_true' in results and len(results['dr_true']) > 0:
            report['diabetic_retinopathy'] = cls.evaluate_dr_performance(
                np.array(results['dr_true']),
                np.array(results['dr_prob']),
                np.array(results['dr_pred'])
            )
            
        # Glaucoma
        if 'glaucoma_true' in results and len(results['glaucoma_true']) > 0:
            report['glaucoma'] = cls.evaluate_glaucoma_performance(
                np.array(results['glaucoma_true']),
                np.array(results['glaucoma_prob']),
                np.array(results['glaucoma_pred'])
            )
            
        # Refraction
        if 'refraction_true' in results and len(results['refraction_true']) > 0:
            report['refraction'] = cls.evaluate_refraction_performance(
                np.array(results['refraction_true']),
                np.array(results['refraction_pred'])
            )
            
        return report
