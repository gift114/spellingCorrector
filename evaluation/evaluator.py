# evaluation/evaluator.py
import json
import time
import os
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import numpy as np

class YorubaSpellingEvaluator:
    """
    Comprehensive evaluation framework for Yorùbá spelling corrector.
    """
    
    def __init__(self, lexicon_path: str, corpus_path: str = None):
        self.lexicon_path = lexicon_path
        self.corpus_path = corpus_path
        
        # Import correctors
        from correctors.base_corrector import YorubaSpellingCorrector
        from correctors.tonal_corrector import EnhancedYorubaSpellingCorrector
        
        # Initialize correctors
        self.basic_corrector = YorubaSpellingCorrector(lexicon_path)
        self.enhanced_corrector = EnhancedYorubaSpellingCorrector(lexicon_path, corpus_path)
        
        # Test contexts
        self.contexts = ['educational', 'conversational', 'literary']
    
    def load_test_sets(self, test_data_dir: str = "evaluation/test_data") -> Dict[str, List[Tuple[str, str]]]:
        """
        Load test sets from JSON files.
        """
        test_sets = {}
        
        for context in self.contexts:
            test_file = os.path.join(test_data_dir, f"{context}_tests.json")
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                    test_sets[context] = [(item['misspelled'], item['correct']) for item in test_data]
                print(f"✓ Loaded {len(test_sets[context])} test cases for {context} context")
            except FileNotFoundError:
                print(f"⚠ Test file not found: {test_file}")
                test_sets[context] = []
        
        return test_sets
    
    def evaluate_corrector(self, corrector, test_sets: Dict) -> Dict[str, Any]:
        """
        Evaluate a spelling corrector on all test sets.
        """
        results = {}
        
        for context, test_cases in test_sets.items():
            if test_cases:  # Only evaluate if test cases exist
                context_results = self._evaluate_context(corrector, test_cases, context)
                results[context] = context_results
        
        # Calculate overall metrics
        overall_metrics = self._calculate_overall_metrics(results)
        results['overall'] = overall_metrics
        
        return results
    
    def _evaluate_context(self, corrector, test_cases: List[Tuple[str, str]], context: str) -> Dict[str, Any]:
        """
        Evaluate corrector on a specific context.
        """
        total_words = 0
        correct_words = 0
        processing_times = []
        
        y_true = []
        y_pred = []
        
        for misspelled, correct in test_cases:
            start_time = time.time()
            
            # Correct the text
            if hasattr(corrector, 'correct_text_with_context'):
                corrected = corrector.correct_text_with_context(misspelled)
            else:
                corrected = corrector.correct_text(misspelled)
            
            end_time = time.time()
            processing_times.append(end_time - start_time)
            
            # Simple accuracy calculation
            if corrected.strip() == correct.strip():
                correct_words += 1
            
            total_words += 1
        
        # Calculate metrics
        accuracy = correct_words / total_words if total_words > 0 else 0
        
        # For this simplified version, we'll use accuracy as main metric
        precision = accuracy
        recall = accuracy
        f1 = accuracy
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'avg_processing_time': np.mean(processing_times) if processing_times else 0,
            'total_test_cases': len(test_cases),
            'total_words': total_words,
            'corrected_words': correct_words
        }
    
    def _calculate_overall_metrics(self, results: Dict) -> Dict[str, float]:
        """
        Calculate overall metrics across all contexts.
        """
        metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'avg_processing_time']
        overall = {}
        
        for metric in metrics:
            values = [results[ctx][metric] for ctx in self.contexts if ctx in results and results[ctx]['total_test_cases'] > 0]
            overall[metric] = np.mean(values) if values else 0
        
        return overall
    
    def generate_report(self, basic_results: Dict, enhanced_results: Dict) -> str:
        """
        Generate a comprehensive evaluation report.
        """
        report = []
        report.append("=" * 60)
        report.append("YORÙBÁ SPELLING CORRECTOR EVALUATION REPORT")
        report.append("=" * 60)
        
        # Overall comparison
        report.append("\nOVERALL PERFORMANCE COMPARISON:")
        report.append("-" * 40)
        
        metrics = ['accuracy', 'f1_score', 'avg_processing_time']
        for metric in metrics:
            basic_val = basic_results['overall'].get(metric, 0)
            enhanced_val = enhanced_results['overall'].get(metric, 0)
            improvement = enhanced_val - basic_val
            
            if metric == 'avg_processing_time':
                report.append(f"{metric:>20}: {basic_val:.4f}s → {enhanced_val:.4f}s "
                            f"({improvement:+.4f}s)")
            else:
                report.append(f"{metric:>20}: {basic_val:.3f} → {enhanced_val:.3f} "
                            f"({improvement:+.3f})")
        
        # Context-wise performance
        report.append("\nCONTEXT-WISE PERFORMANCE:")
        report.append("-" * 40)
        
        for context in self.contexts:
            if context in basic_results and basic_results[context]['total_test_cases'] > 0:
                report.append(f"\n{context.upper()} CONTEXT:")
                basic_ctx = basic_results[context]
                enhanced_ctx = enhanced_results[context]
                
                report.append(f"  Accuracy:    {basic_ctx['accuracy']:.3f} → {enhanced_ctx['accuracy']:.3f}")
                report.append(f"  Test Cases:  {basic_ctx['total_test_cases']}")
                report.append(f"  Speed:       {basic_ctx['avg_processing_time']:.4f}s per case")
        
        return "\n".join(report)
    
    def run_complete_evaluation(self, test_data_dir: str = "evaluation/test_data") -> Dict[str, Any]:
        """
        Run complete evaluation and return results.
        """
        print("Starting comprehensive evaluation...")
        
        # Load test sets
        test_sets = self.load_test_sets(test_data_dir)
        
        if not any(len(cases) > 0 for cases in test_sets.values()):
            print("❌ No test data found. Please generate test data first.")
            return {}
        
        # Evaluate basic corrector
        print("Evaluating basic corrector...")
        basic_results = self.evaluate_corrector(self.basic_corrector, test_sets)
        
        # Evaluate enhanced corrector
        print("Evaluating enhanced corrector with tonal disambiguation...")
        enhanced_results = self.evaluate_corrector(self.enhanced_corrector, test_sets)
        
        # Generate report
        report = self.generate_report(basic_results, enhanced_results)
        
        return {
            'basic_results': basic_results,
            'enhanced_results': enhanced_results,
            'report': report,
            'test_sets': test_sets
        }