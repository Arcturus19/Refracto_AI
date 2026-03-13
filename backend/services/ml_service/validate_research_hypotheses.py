"""
Research Hypothesis Validation Orchestrator (Week 3)
Automatically runs H1, H2, H3 validation pipeline and generates comprehensive report
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict
import traceback

# Import validation modules
from h1_validation import validate_h1
from h2_validation import validate_h2
from h3_validation import validate_h3


class ResearchValidationOrchestrator:
    """Manages complete Week 3 research validation"""
    
    def __init__(self, output_dir: str = 'validation_results'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {}
        self.all_passed = True
    
    def run_all_validations(self) -> Dict:
        """Execute all three hypothesis validations"""
        print("\n" + "="*80)
        print("RESEARCH HYPOTHESIS VALIDATION PIPELINE (WEEK 3)")
        print("="*80)
        
        validations = [
            ('H1', validate_h1, "Multi-Modal Fusion Superiority"),
            ('H2', validate_h2, "Refracto-Link FPR Reduction in High Myopia"),
            ('H3', validate_h3, "Expert Clinical Concordance Rate"),
        ]
        
        for hypothesis_name, validation_func, description in validations:
            print(f"\n\n{'─'*80}")
            print(f"Running {hypothesis_name}: {description}")
            print(f"{'─'*80}")
            
            try:
                result = validation_func()
                self.results[hypothesis_name] = result
                
                # Track overall status
                if result.get('validation_passed') is False:
                    self.all_passed = False
                
                self._save_result(hypothesis_name, result)
            
            except Exception as e:
                print(f"\n❌ ERROR during {hypothesis_name} validation:")
                print(f"   {str(e)}")
                traceback.print_exc()
                
                self.results[hypothesis_name] = {
                    'error': str(e),
                    'hypothesis_status': 'ERROR',
                    'validation_passed': False,
                }
                self.all_passed = False
    
    def _save_result(self, hypothesis: str, result: Dict):
        """Save individual hypothesis result"""
        output_file = self.output_dir / f'{hypothesis}_validation_result.json'
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n✓ Result saved: {output_file}")
    
    def generate_research_report(self) -> Dict:
        """Generate comprehensive research validation report"""
        report = {
            'report_title': 'Refracto AI Week 3 Research Validation Report',
            'report_type': 'Research Hypothesis Validation',
            'generated_date': datetime.now().isoformat(),
            'all_hypotheses_passed': self.all_passed,
            'hypotheses': {},
            'summary': self._generate_summary(),
            'recommendations': self._generate_recommendations(),
        }
        
        # Add individual hypothesis results
        report['hypotheses'] = {
            'H1': {
                'name': 'Multi-Modal Fusion Superiority',
                'target': 'Fusion accuracy ≥5% above baseline',
                'status': self.results['H1'].get('h1_hypothesis_status', 'ERROR'),
                'result': self.results['H1'],
            } if 'H1' in self.results else None,
            'H2': {
                'name': 'Refracto-Link FPR Reduction',
                'target': 'FPR reduction ≥20% in high myopia',
                'status': self.results['H2'].get('h2_hypothesis_status', 'ERROR'),
                'result': self.results['H2'],
            } if 'H2' in self.results else None,
            'H3': {
                'name': 'Expert Clinical Concordance Rate',
                'target': 'Expert CCR ≥85%',
                'status': self.results['H3'].get('h3_hypothesis_status', 'ERROR'),
                'result': self.results['H3'],
            } if 'H3' in self.results else None,
        }
        
        return report
    
    def _generate_summary(self) -> Dict:
        """Generate executive summary"""
        summary = {
            'total_hypotheses': 3,
            'passed': sum(1 for h in self.results.values() if h.get('validation_passed')),
            'failed': sum(1 for h in self.results.values() if h.get('validation_passed') is False),
            'errors': sum(1 for h in self.results.values() if 'error' in h),
            'status': 'ALL PASSED ✓' if self.all_passed else 'SOME FAILED ✗',
        }
        
        # H1 details
        if 'H1' in self.results and 'metrics' in self.results['H1']:
            summary['H1'] = {
                'fusion_advantage': f"{self.results['H1']['metrics']['advantage_percentage']:.1f}%",
                'target': '≥5%',
                'p_value': self.results['H1']['statistics'].get('p_value'),
            }
        
        # H2 details
        if 'H2' in self.results and 'metrics' in self.results['H2']:
            summary['H2'] = {
                'fpr_reduction': f"{self.results['H2']['metrics']['fpr_reduction_percentage']:.1f}%",
                'target': '≥20%',
                'p_value': self.results['H2']['statistics'].get('p_value'),
            }
        
        # H3 details
        if 'H3' in self.results and 'metrics' in self.results['H3']:
            summary['H3'] = {
                'global_ccr': f"{self.results['H3']['metrics']['global_ccr_percentage']:.1f}%",
                'target': '≥85%',
                'confidence_interval': f"[{self.results['H3']['confidence_interval']['lower_bound_percentage']:.1f}%, {self.results['H3']['confidence_interval']['upper_bound_percentage']:.1f}%]",
            }
        
        return summary
    
    def _generate_recommendations(self) -> Dict:
        """Generate recommendations based on results"""
        recommendations = {
            'next_steps': [],
            'production_readiness': '',
            'further_research': [],
        }
        
        # H1 recommendations
        if 'H1' in self.results:
            if self.results['H1'].get('validation_passed'):
                recommendations['next_steps'].append(
                    "H1 PASSED: Multi-modal fusion shows statistical superiority. "
                    "Proceed with fusion model as primary diagnostic tool."
                )
            else:
                recommendations['next_steps'].append(
                    "H1 FAILED: Fusion model not significantly better than baseline. "
                    "Review model architecture and training data."
                )
        
        # H2 recommendations
        if 'H2' in self.results:
            if self.results['H2'].get('validation_passed'):
                recommendations['next_steps'].append(
                    "H2 PASSED: Refracto-link effectively reduces FPR in high myopia. "
                    "Enable correction factor in clinical deployment."
                )
            else:
                recommendations['next_steps'].append(
                    "H2 FAILED: FPR reduction insufficient. Consider recalibrating "
                    "correction factor or expanding myopic cohort for testing."
                )
        
        # H3 recommendations
        if 'H3' in self.results:
            if self.results['H3'].get('validation_passed'):
                recommendations['next_steps'].append(
                    "H3 PASSED: Expert panel shows strong agreement with AI predictions. "
                    "Ready for clinical validation phase."
                )
                recommendations['production_readiness'] = "HIGH - All hypotheses validated"
            else:
                recommendations['next_steps'].append(
                    "H3 FAILED: Expert agreement below target. Collect more expert reviews "
                    "and analyze disagreement patterns."
                )
                recommendations['production_readiness'] = "CONDITIONAL - Resolve H3"
        
        # General recommendations
        if self.all_passed:
            recommendations['further_research'].extend([
                "Conduct prospective clinical trial with independent expert panel",
                "Analyze model performance across demographic subgroups (age, gender, ethnicity)",
                "Compare AI predictions to standard clinical workflow (time, cost, accessibility)",
                "Investigate failure cases for systematic biases",
            ])
        
        return recommendations
    
    def save_report(self, report: Dict):
        """Save comprehensive report to file"""
        report_file = self.output_dir / 'research_validation_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✓ Report saved: {report_file}")
        
        # Also save human-readable version
        text_report = self._format_report_text(report)
        text_file = self.output_dir / 'research_validation_report.txt'
        with open(text_file, 'w') as f:
            f.write(text_report)
        print(f"✓ Text report saved: {text_file}")
    
    def _format_report_text(self, report: Dict) -> str:
        """Format report as human-readable text"""
        lines = [
            "="*80,
            "REFRACTO AI - WEEK 3 RESEARCH VALIDATION REPORT",
            "="*80,
            f"\nGenerated: {report['generated_date']}",
            f"Type: {report['report_type']}",
            f"\nOVERALL STATUS: {report['summary']['status']}",
            f"  Passed: {report['summary']['passed']}/3",
            f"  Failed: {report['summary']['failed']}/3",
            f"  Errors: {report['summary']['errors']}/3",
            "\n" + "-"*80,
            "HYPOTHESIS RESULTS",
            "-"*80,
        ]
        
        # H1
        if report['hypotheses']['H1']:
            h1 = report['hypotheses']['H1']
            lines.extend([
                f"\nH1: {h1['name']}",
                f"  Status: {h1['status']}",
                f"  Target: {h1['target']}",
            ])
            if 'metrics' in h1['result']:
                lines.append(f"  Result: {h1['result']['metrics']['advantage_percentage']:.1f}% fusion advantage")
        
        # H2
        if report['hypotheses']['H2']:
            h2 = report['hypotheses']['H2']
            lines.extend([
                f"\nH2: {h2['name']}",
                f"  Status: {h2['status']}",
                f"  Target: {h2['target']}",
            ])
            if 'metrics' in h2['result']:
                lines.append(f"  Result: {h2['result']['metrics']['fpr_reduction_percentage']:.1f}% FPR reduction")
        
        # H3
        if report['hypotheses']['H3']:
            h3 = report['hypotheses']['H3']
            lines.extend([
                f"\nH3: {h3['name']}",
                f"  Status: {h3['status']}",
                f"  Target: {h3['target']}",
            ])
            if 'metrics' in h3['result']:
                lines.append(f"  Result: {h3['result']['metrics']['global_ccr_percentage']:.1f}% CCR")
        
        # Recommendations
        lines.extend([
            "\n" + "-"*80,
            "RECOMMENDATIONS",
            "-"*80,
            f"\nProduction Readiness: {report['recommendations']['production_readiness']}",
            "\nNext Steps:",
        ])
        for i, step in enumerate(report['recommendations']['next_steps'], 1):
            lines.append(f"  {i}. {step}")
        
        lines.extend([
            "\nFurther Research:",
        ])
        for i, research in enumerate(report['recommendations']['further_research'], 1):
            lines.append(f"  {i}. {research}")
        
        lines.extend([
            "\n" + "="*80,
        ])
        
        return "\n".join(lines)


def main():
    """Main execution"""
    try:
        orchestrator = ResearchValidationOrchestrator(
            output_dir='backend/services/ml_service/validation_results'
        )
        
        # Run all validations
        orchestrator.run_all_validations()
        
        # Generate report
        report = orchestrator.generate_research_report()
        orchestrator.save_report(report)
        
        # Print summary
        print("\n" + "="*80)
        print("WEEK 3 VALIDATION COMPLETE")
        print("="*80)
        print(f"\nOverall Status: {report['summary']['status']}")
        print(f"Passed: {report['summary']['passed']}/3")
        print(f"Failed: {report['summary']['failed']}/3")
        print(f"Errors: {report['summary']['errors']}/3")
        
        # Print text report to console
        print("\n")
        print(orchestrator._format_report_text(report))
        
        # Return exit code based on status
        return 0 if orchestrator.all_passed else 1
    
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
