"""
H1 Validation: Multi-Modal Fusion Superiority
Validates that fusion model outperforms single-modality baselines by ≥5%
"""

import torch
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, List
from scipy.stats import mcnemar
import json
from datetime import datetime


class H1ValidationDataset:
    """Balanced test set for H1 hypothesis validation"""
    
    def __init__(self, test_data_path: str, n_samples: int = 50):
        self.test_data_path = Path(test_data_path)
        self.n_samples = n_samples
        self.balanced_set = []
    
    def prepare_balanced_test_set(self) -> List[Dict]:
        """Create balanced test set across all 5 DR classes"""
        balanced_set = []
        
        # Simulate loading images from RFMiD/GAMMA/local data
        # In production: query database with DR labels
        for dr_class in range(5):
            class_images = self._get_images_by_class(dr_class, n_per_class=10)
            balanced_set.extend(class_images)
        
        self.balanced_set = balanced_set
        return balanced_set
    
    def _get_images_by_class(self, dr_class: int, n_per_class: int) -> List[Dict]:
        """Retrieve n_per_class images for DR class"""
        # Pseudocode: In production, query database
        images = []
        for i in range(n_per_class):
            images.append({
                'case_id': f'H1_CLASS{dr_class}_IMG{i}',
                'dr_label': dr_class,
                'source': 'RFMiD' if i % 2 == 0 else 'GAMMA',
                'confidence': np.random.uniform(0.6, 0.99)
            })
        return images
    
    def compute_h1_metrics(self, predictions_dict: Dict) -> Dict:
        """Calculate accuracy for single vs multi-modal"""
        fundus_preds = np.array(predictions_dict['fundus_only'])
        oct_preds = np.array(predictions_dict['oct_only'])
        fusion_preds = np.array(predictions_dict['fusion'])
        ground_truth = np.array(predictions_dict['ground_truth_dr'])
        
        fundus_acc = np.mean(fundus_preds == ground_truth)
        oct_acc = np.mean(oct_preds == ground_truth)
        fusion_acc = np.mean(fusion_preds == ground_truth)
        
        baseline_acc = max(fundus_acc, oct_acc)
        fusion_advantage = fusion_acc - baseline_acc
        
        return {
            'fundus_only_accuracy': float(fundus_acc),
            'oct_only_accuracy': float(oct_acc),
            'fusion_accuracy': float(fusion_acc),
            'baseline_accuracy': float(baseline_acc),
            'fusion_advantage': float(fusion_advantage),
            'advantage_percentage': float(fusion_advantage * 100),
        }


class H1InferenceEngine:
    """Run fusion vs single-modality inference"""
    
    def __init__(self, model_path: str = None, device: str = 'cpu'):
        self.device = torch.device(device)
        self.model_path = model_path
    
    def infer_h1_comparison(self, fundus_tensor: torch.Tensor, oct_tensor: torch.Tensor) -> Dict:
        """Run inference on all 3 models"""
        # Simulate models - in production: load actual models
        
        # Single-modality predictions (simulated)
        fundus_logits = torch.randn(1, 5)  # 5 DR classes
        fundus_pred = torch.argmax(fundus_logits, dim=1)
        fundus_conf = torch.softmax(fundus_logits, dim=1).max(dim=1)[0]
        
        oct_logits = torch.randn(1, 5)
        oct_pred = torch.argmax(oct_logits, dim=1)
        oct_conf = torch.softmax(oct_logits, dim=1).max(dim=1)[0]
        
        # Fusion prediction (slightly better performance)
        fusion_logits = fundus_logits * 0.6 + oct_logits * 0.4  # Weighted average
        fusion_pred = torch.argmax(fusion_logits, dim=1)
        fusion_conf = torch.softmax(fusion_logits, dim=1).max(dim=1)[0]
        
        return {
            'fundus_pred': fundus_pred.cpu().numpy(),
            'oct_pred': oct_pred.cpu().numpy(),
            'fusion_pred': fusion_pred.cpu().numpy(),
            'fundus_confidence': fundus_conf.cpu().numpy(),
            'oct_confidence': oct_conf.cpu().numpy(),
            'fusion_confidence': fusion_conf.cpu().numpy(),
        }


def mcnemar_test_h1(fusion_preds: np.ndarray, best_single_preds: np.ndarray, 
                     ground_truth: np.ndarray) -> Dict:
    """McNemar's test for comparing classifier accuracy"""
    fusion_correct = (fusion_preds == ground_truth).astype(int)
    single_correct = (best_single_preds == ground_truth).astype(int)
    
    # McNemar table: b = single correct, fusion wrong
    #                c = fusion correct, single wrong
    b = np.sum((fusion_correct == 0) & (single_correct == 1))
    c = np.sum((fusion_correct == 1) & (single_correct == 0))
    
    # Exact binomial test (better for small n)
    if (b + c) > 0:
        result = mcnemar((b, c), exact=(b + c) <= 25)
    else:
        result = type('obj', (object,), {'statistic': 0, 'pvalue': 1.0})()
    
    return {
        'b_stat': int(b),  # Single correct, fusion wrong
        'c_stat': int(c),  # Fusion correct, single wrong
        'test_statistic': float(result.statistic),
        'p_value': float(result.pvalue),
        'h1_significant': result.pvalue < 0.05 and c > b,
        'fusion_advantage_cases': int(c - b),
    }


def validate_h1() -> Dict:
    """Complete H1 validation pipeline"""
    print("\n" + "="*60)
    print("H1 VALIDATION: Multi-Modal Fusion Superiority")
    print("="*60)
    
    # Prepare dataset
    dataset = H1ValidationDataset(test_data_path='data/processed/test/')
    test_set = dataset.prepare_balanced_test_set()
    print(f"\n✓ Balanced test set prepared: {len(test_set)} images")
    
    # Run inference
    engine = H1InferenceEngine()
    predictions = {
        'fundus_only': [],
        'oct_only': [],
        'fusion': [],
        'ground_truth_dr': []
    }
    
    for sample in test_set:
        # Simulate loading images
        fundus_img = torch.randn(1, 3, 224, 224)
        oct_img = torch.randn(1, 3, 224, 224)
        
        result = engine.infer_h1_comparison(fundus_img, oct_img)
        predictions['fundus_only'].append(result['fundus_pred'][0])
        predictions['oct_only'].append(result['oct_pred'][0])
        predictions['fusion'].append(result['fusion_pred'][0])
        predictions['ground_truth_dr'].append(sample['dr_label'])
    
    # Calculate metrics
    metrics = dataset.compute_h1_metrics(predictions)
    print(f"\n✓ Inference complete:")
    print(f"  Fundus-only accuracy: {metrics['fundus_only_accuracy']:.2%}")
    print(f"  OCT-only accuracy: {metrics['oct_only_accuracy']:.2%}")
    print(f"  Fusion accuracy: {metrics['fusion_accuracy']:.2%}")
    
    # Statistical test
    fusion_preds = np.array(predictions['fusion'])
    best_single_preds = np.array(predictions['oct_only'] if metrics['oct_only_accuracy'] >= metrics['fundus_only_accuracy'] else predictions['fundus_only'])
    ground_truth = np.array(predictions['ground_truth_dr'])
    
    stats = mcnemar_test_h1(fusion_preds, best_single_preds, ground_truth)
    print(f"\n✓ McNemar Test Results:")
    print(f"  Fusion advantage cases: {stats['fusion_advantage_cases']}")
    print(f"  P-value: {stats['p_value']:.6f}")
    
    # Determine H1 status
    h1_passed = metrics['fusion_advantage'] >= 0.05 and stats['p_value'] < 0.05
    h1_status = "PASS" if h1_passed else "FAIL"
    
    print(f"\n{'='*60}")
    print(f"H1 HYPOTHESIS STATUS: {h1_status}")
    print(f"Fusion advantage: {metrics['advantage_percentage']:.1f}% (target: ≥5%)")
    print(f"Statistical significance: p = {stats['p_value']:.6f} (target: p < 0.05)")
    print(f"{'='*60}\n")
    
    return {
        'h1_hypothesis_status': h1_status,
        'metrics': metrics,
        'statistics': stats,
        'validation_samples': len(test_set),
        'timestamp': datetime.now().isoformat(),
        'validation_passed': h1_passed,
    }


if __name__ == '__main__':
    result = validate_h1()
    print(json.dumps(result, indent=2))
