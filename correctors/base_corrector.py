# correctors/base_corrector.py
from typing import List, Dict, Tuple
from collections import defaultdict
import unicodedata
import re

# rapidfuzz use is optional — keep import local to avoid hard crash if missing
try:
    from rapidfuzz import process, fuzz
    RAPIDFUZZ_AVAILABLE = True
except Exception:
    RAPIDFUZZ_AVAILABLE = False

class YorubaSpellingCorrector:
    def __init__(self, lexicon_path: str):
        self.lexicon = self.load_lexicon(lexicon_path)
        self.index = self.build_index(self.lexicon)
        print(f"✓ Loaded {len(self.lexicon)} words from {lexicon_path}")

    @staticmethod
    def strip_diacritics(word: str) -> str:
        return ''.join(
            c for c in unicodedata.normalize('NFD', word)
            if unicodedata.category(c) != 'Mn'
        ).lower()

    @staticmethod
    def load_lexicon(filepath: str) -> List[str]:
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def build_index(self, words: List[str]) -> Dict[str, List[str]]:
        index = defaultdict(list)
        for word in words:
            normalized = self.strip_diacritics(word)
            index[normalized].append(word)
        return index

    def is_correct(self, word: str) -> bool:
        return word in self.lexicon

    def suggest_corrections(self,
                            input_word: str,
                            max_suggestions: int = 3,
                            similarity_threshold: int = 70) -> List[Tuple[str, float]]:
        if self.is_correct(input_word):
            return [(input_word, 100.0)]

        normalized_input = self.strip_diacritics(input_word)

        if normalized_input in self.index:
            suggestions = [(word, 95.0) for word in self.index[normalized_input]]
            return suggestions[:max_suggestions]

        if RAPIDFUZZ_AVAILABLE:
            candidate_keys = list(self.index.keys())
            matches = process.extract(
                normalized_input,
                candidate_keys,
                scorer=fuzz.WRatio,
                limit=max_suggestions * 2,
                score_cutoff=similarity_threshold
            )
            suggestions = []
            seen = set()
            for candidate_key, score, _ in matches:
                for original_word in self.index[candidate_key]:
                    if original_word not in seen:
                        suggestions.append((original_word, score))
                        seen.add(original_word)
            return sorted(suggestions, key=lambda x: x[1], reverse=True)[:max_suggestions]
        else:
            # Fallback simple edit-distance-like filter (lightweight)
            suggestions = []
            for key, originals in self.index.items():
                if abs(len(key) - len(normalized_input)) > 3:
                    continue
                # cheap substring check
                if normalized_input in key or key in normalized_input or key[:2] == normalized_input[:2]:
                    for o in originals:
                        suggestions.append((o, 50.0))
            return suggestions[:max_suggestions]

    def correct_text(self, text: str) -> str:
        tokens = re.findall(r'\b\w+\b|[^\w\s]', text, re.UNICODE)
        corrected_tokens = []
        for token in tokens:
            if re.match(r'\w', token):
                if not self.is_correct(token):
                    suggestions = self.suggest_corrections(token, max_suggestions=1)
                    if suggestions:
                        corrected_tokens.append(suggestions[0][0])
                        continue
                corrected_tokens.append(token)
            else:
                corrected_tokens.append(token)
        return ''.join(corrected_tokens)

    def get_stats(self) -> Dict[str, int]:
        return {
            "total_words": len(self.lexicon),
            "unique_normalized": len(self.index),
            "average_variants": len(self.lexicon) / len(self.index) if len(self.index) else 0
        }
