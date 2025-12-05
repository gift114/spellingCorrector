# evaluation/test_generator.py
import json
import os
from typing import List, Tuple, Dict

class YorubaTestGenerator:
    """
    Generate test data for different contexts.
    """
    
    def __init__(self):
        self.contexts = ['educational', 'conversational', 'literary']
    
    def generate_educational_tests(self) -> List[Dict[str, str]]:
        """Generate educational context test cases."""
        return [
            {"misspelled": "awa omo ile", "correct": "àwọn ọmọ ilé"},
            {"misspelled": "mo fe ka iwe", "correct": "mo fẹ́ kàwé"},
            {"misspelled": "owo mi dun", "correct": "owó mi dùn"},
            {"misspelled": "ile naa tobi", "correct": "ilé náà tóbi"},
            {"misspelled": "baba ati iya", "correct": "bàbá àti ìyá"},
            {"misspelled": "omo naa dara", "correct": "ọmọ náà dára"},
            {"misspelled": "iwe mi wa", "correct": "ìwé mi wà"},
            {"misspelled": "oko baba", "correct": "oko bàbá"}
        ]
    
    def generate_conversational_tests(self) -> List[Dict[str, str]]:
        """Generate conversational context test cases."""
        return [
            {"misspelled": "bawo ni o se wa", "correct": "báwo ni o ṣe wà"},
            {"misspelled": "mo wa ni ile iwe", "correct": "mo wà ní ilé ẹ̀kọ́"},
            {"misspelled": "ise yin dun o", "correct": "iṣẹ́ yín dùn o"},
            {"misspelled": "alafia ni o", "correct": "aláàfíà ni o"},
            {"misspelled": "a dupe o", "correct": "a dúpẹ́ o"},
            {"misspelled": "ise lo n se", "correct": "ìṣẹ́ lo ń ṣe"},
            {"misspelled": "owo mi wa", "correct": "owó mi wà"},
            {"misspelled": "ile yi dara", "correct": "ilé yìí dára"}
        ]
    
    def generate_literary_tests(self) -> List[Dict[str, str]]:
        """Generate literary context test cases."""
        return [
            {"misspelled": "akoko yi lagbara", "correct": "àkókò yìí lágbára"},
            {"misspelled": "inu igba ati isimi", "correct": "inú ìgbà àti ìsimi"},
            {"misspelled": "itan aroso naa dun", "correct": "ìtàn àròsọ náà dùn"},
            {"misspelled": "awon akekoo naa ka iwe", "correct": "àwọn akẹ́kọ̀ọ́ náà kàwé"},
            {"misspelled": "oju ojo naa fe we ile", "correct": "ojú ọjọ́ náà fẹ́ wé ilé"},
            {"misspelled": "igba owuro ni", "correct": "ìgbà owurọ̀ ni"},
            {"misspelled": "ori ire", "correct": "orí ire"},
            {"misspelled": "inu didun", "correct": "inú dídùn"}
        ]
    
    def generate_all_test_data(self, output_dir: str = "evaluation/test_data"):
        """Generate all test data files."""
        os.makedirs(output_dir, exist_ok=True)
        
        test_generators = {
            'educational': self.generate_educational_tests,
            'conversational': self.generate_conversational_tests,
            'literary': self.generate_literary_tests
        }
        
        for context, generator in test_generators.items():
            test_data = generator()
            output_file = os.path.join(output_dir, f"{context}_tests.json")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Generated {len(test_data)} test cases for {context} context: {output_file}")
        
        print(f"\n✅ All test data generated in: {output_dir}")

def generate_test_files():
    """Convenience function to generate all test files."""
    generator = YorubaTestGenerator()
    generator.generate_all_test_data()

if __name__ == "__main__":
    generate_test_files()