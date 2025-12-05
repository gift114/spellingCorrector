from typing import List, Dict, Tuple
from collections import defaultdict
import unicodedata
import re
import os
from .base_corrector import YorubaSpellingCorrector
from .ml_components import ContextAwareCorrector

import re
from typing import List, Tuple, Dict
from .base_corrector import YorubaSpellingCorrector
from .ml_components import ContextAwareCorrector

class LexiconIntegratedCorrector:
    """Corrector handling compound words, typos, and optional ML-based diacritics restoration."""

    def __init__(self, lexicon_path: str, corpus_path: str = None, use_transformer: bool = False, load_ml_on_init: bool = False):
        self.lexicon_path = lexicon_path
        self.corpus_path = corpus_path
        self.base = YorubaSpellingCorrector(lexicon_path)
        # Build normalized lexicon map for compound matching
        self.normalized_mapping = {self._normalize_phrase_key(k): k for k in self.base.lexicon}

        self._ml_corrector = None
        self.use_transformer = use_transformer
        self._ml_loaded = False

        if load_ml_on_init:
            self._ensure_ml_corrector()

    # ------------------------- ML initialization -------------------------
    def _ensure_ml_corrector(self):
        if self._ml_loaded:
            return
        try:
            self._ml_corrector = ContextAwareCorrector(
                self.lexicon_path,
                self.corpus_path,
                load_transformer=self.use_transformer
            )
            self._ml_loaded = True
            print("✅ ML corrector initialized")
        except Exception as e:
            print(f"⚠ Failed to initialize ML corrector: {e}")
            self._ml_corrector = None
            self._ml_loaded = False

    # ------------------------- Typo & suggestion -------------------------
    def suggest_corrections(self, word: str, max_suggestions: int = 3) -> List[Tuple[str, str, float]]:
        """Return list of candidate corrections with confidence."""
        if self.base.is_correct(word):
            return [(word, "Exact match", 1.0)]

        normalized = self.base.strip_diacritics(word)
        if normalized in self.normalized_mapping:
            candidates = self.normalized_mapping[normalized]
            return [(c, "Normalized match", 0.9 - i*0.1) for i, c in enumerate(candidates[:max_suggestions])]

        if not self._ml_loaded:
            self._ensure_ml_corrector()
        if self._ml_loaded and self._ml_corrector:
            corrected = self._ml_corrector.restore_sentence_diacritics(word)
            if corrected != word and corrected in self._ml_corrector.lexicon:
                return [(corrected, "ML diacritic restoration", 0.85)]

        base_sugg = self.base.suggest_corrections(word, max_suggestions=max_suggestions)
        return [(s[0], "Base suggestion", float(s[1])/100.0 if isinstance(s[1], (int, float)) else 0.5) for s in base_sugg]

    # ------------------------- Normalization -------------------------
    def _normalize_phrase_key(self, phrase: str) -> str:
        """Normalize phrase: strip diacritics, remove spaces and hyphens for matching."""
        key = self.base.strip_diacritics(phrase)
        key = key.replace(" ", "").replace("-", "")
        return key

    # ------------------------- Compound phrase correction -------------------------
    def _correct_compound_phrases(self, text: str) -> str:
        """Fix multi-word phrases with hyphens, spaces, or combined forms, including typos."""
        words = text.split()
        corrected_text = text
        max_len = min(4, len(words))  # max phrase length

        for n in range(max_len, 0, -1):
            for i in range(len(words) - n + 1):
                phrase_words = words[i:i+n]
                phrase = " ".join(phrase_words)
                # Generate all space/hyphen/combined variants
                variants = [
                    phrase,
                    phrase.replace(" ", "-"),
                    phrase.replace("-", " "),
                    phrase.replace(" ", ""),
                    phrase.replace("-", "")
                ]

                for variant in variants:
                    key = self._normalize_phrase_key(variant)
                    if key in self.normalized_mapping:
                        replacement = self.normalized_mapping[key]
                    else:
                        # Try typo correction
                        sugg = self.base.suggest_corrections(variant, max_suggestions=1)
                        if sugg:
                            replacement = sugg[0][0]
                        else:
                            continue

                    # Regex pattern for matching spaces or hyphens in original text
                    parts = re.split(r'[\s-]+', phrase)
                    pattern = r'[\s-]+'.join(map(re.escape, parts))
                    corrected_text = re.sub(
                        r'\b' + pattern + r'\b',
                        replacement,
                        corrected_text,
                        flags=re.IGNORECASE
                    )
                    break  # stop after first successful replacement

        return corrected_text

    # ------------------------- Main correction -------------------------
    def correct_text(self, text: str, use_ml: bool = True) -> str:
        """Correct text with compound words, typos, and optional ML."""
        # Step 1: handle compound phrases & typos
        text = self._correct_compound_phrases(text)

        # Step 2: ML-based context-aware diacritics
        if use_ml:
            if not self._ml_loaded:
                self._ensure_ml_corrector()
            if self._ml_loaded and self._ml_corrector:
                try:
                    text = self._ml_corrector.correct_text_with_ml(text)
                except Exception as e:
                    print(f"⚠ ML correction failed: {e}")

        # Step 3: fix compound phrases again after ML
        text = self._correct_compound_phrases(text)

        return text

    # ------------------------- Helper methods -------------------------
    def find_closest_matches(self, word: str, max_matches: int = 3) -> List[str]:
        return [s[0] for s in self.suggest_corrections(word, max_suggestions=max_matches)]

    def get_ml_stats(self) -> Dict[str, any]:
        stats = {
            "ml_loaded": self._ml_loaded,
            "base_vocab_size": len(self.base.lexicon)
        }
        if self._ml_loaded and self._ml_corrector:
            stats.update({
                "ngram_vocab": len(self._ml_corrector.ngram_model.vocab),
                "uses_transformer": bool(self._ml_corrector.diacritic_restorer.model)
            })
        return stats
