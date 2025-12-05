# evaluation/evaluation_runner.py
import os
import json
from typing import Dict, List
from .evaluator import YorubaSpellingEvaluator
from .test_generator import generate_test_files

def setup_evaluation_environment():
    """Set up the complete evaluation environment."""
    
    # Create necessary directories
    os.makedirs("evaluation/test_data", exist_ok=True)
    os.makedirs("evaluation/results", exist_ok=True)
    
    # Generate test data if it doesn't exist
    test_files_exist = any(
        os.path.exists(f"evaluation/test_data/{context}_tests.json") 
        for context in ['educational', 'conversational', 'literary']
    )
    
    if not test_files_exist:
        print("Generating test data...")
        generate_test_files()
    
    # Create a sample corpus file for enhanced corrector
    sample_corpus = """
    àwọn ọmọ ilé kàwé lọ sí ilé ẹ̀kọ́. bàbá àti ìyá ràwé fún àwọn ọmọ wọn.
    owó mi dùn láti rí iṣẹ́ tuntun. ilé náà tóbi jùlọ.
    mo fẹ́ kàwé ní ilé ẹ̀kọ́ gíga. ọmọ náà dára púpọ̀.
    ìwé mi wà ní ilé. oko bàbá tóbi gan an.
    báwo ni o ṣe wà lónìí? mo wà ní ilé ẹ̀kọ́.
    iṣẹ́ yín dùn o, ẹ jẹ́ kí n rí i. aláàfíà ni o, ẹ kú alé.
    a dúpẹ́ o fún ìrànlọ́wọ́ yín. ìṣẹ́ lo ń ṣe lónìí?
    owó mi wà ní bánkì. ilé yìí dára gan an.
    àkókò yìí lágbára fún ìdàgbàsókè. inú ìgbà àti ìsimi.
    ìtàn àròsọ náà dùn láti kà. àwọn akẹ́kọ̀ọ́ náà kàwé lójú.
    ojí ọjọ́ náà fẹ́ wé ilé. ìgbà owurọ̀ ni a ti lọ.
    orí ire l'a ń wá. inú dídùn ni èmi ó fi hàn.
    """
    
    with open("evaluation/sample_corpus.txt", "w", encoding="utf-8") as f:
        f.write(sample_corpus)
    
    print("✅ Evaluation environment setup complete!")

def run_comprehensive_evaluation():
    """Run the complete evaluation with your lexicon."""
    
    # Setup environment
    setup_evaluation_environment()
    
    # Initialize evaluator with your lexicon
    lexicon_path = "data/yoruba_lexicon.txt"  # Your lexicon file
    corpus_path = "evaluation/sample_corpus.txt"
    
    evaluator = YorubaSpellingEvaluator(lexicon_path, corpus_path)
    
    # Run evaluation
    print("\n" + "="*60)
    print("RUNNING COMPREHENSIVE YORÙBÁ SPELLING CORRECTOR EVALUATION")
    print("="*60)
    
    results = evaluator.run_complete_evaluation()
    
    if results:
        # Print report
        print("\n" + results['report'])
        
        # Save detailed results
        output_file = "evaluation/results/evaluation_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            # Convert sets to lists for JSON serialization
            serializable_results = {
                'basic_results': results['basic_results'],
                'enhanced_results': results['enhanced_results'],
                'test_sets_size': {ctx: len(cases) for ctx, cases in results['test_sets'].items()}
            }
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Detailed results saved to: {output_file}")
        
        # Generate performance summary
        generate_performance_summary(results)
    
    return results

def generate_performance_summary(results: Dict):
    """Generate a concise performance summary."""
    basic = results['basic_results']['overall']
    enhanced = results['enhanced_results']['overall']
    
    print("\n" + "="*50)
    print("PERFORMANCE SUMMARY")
    print("="*50)
    print(f"Overall Accuracy:    {basic['accuracy']:.3f} → {enhanced['accuracy']:.3f}")
    print(f"F1 Score:           {basic['f1_score']:.3f} → {enhanced['f1_score']:.3f}")
    print(f"Processing Time:    {basic['avg_processing_time']:.4f}s → {enhanced['avg_processing_time']:.4f}s")
    
    improvement = enhanced['accuracy'] - basic['accuracy']
    print(f"\nImprovement: {improvement:+.3f} ({improvement*100:+.1f}%)")

if __name__ == "__main__":
    # Run the complete evaluation
    results = run_comprehensive_evaluation()
    
    # Additional analysis if results are available
    if results:
        print("\n🎯 Evaluation complete! Ready for Objective 5 (Application Development)")