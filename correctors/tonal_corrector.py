import os
import re
from typing import List, Dict
from collections import Counter
from .base_corrector import YorubaSpellingCorrector

class EnhancedYorubaSpellingCorrector(YorubaSpellingCorrector):
    """
    Enhanced corrector with tonal disambiguation and context awareness.
    """

    def __init__(self, lexicon_path: str, corpus_path: str = None):
        super().__init__(lexicon_path)
        self.word_frequencies = self._load_word_frequencies(corpus_path)
        self.tonal_patterns = self._learn_tonal_patterns()
        self.normalized_lexicon = self._create_normalized_lexicon()

    def _create_normalized_lexicon(self) -> Dict[str, List[str]]:
        from collections import defaultdict
        normalized_lexicon = defaultdict(list)
        for word in self.lexicon:
            norm = self.strip_diacritics(word)
            normalized_lexicon[norm].append(word)
        return normalized_lexicon

    def _load_word_frequencies(self, corpus_path: str) -> Dict[str, int]:
        frequencies = {}
        if corpus_path and os.path.exists(corpus_path):
            try:
                with open(corpus_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    words = re.findall(r'\b\w+\b', text.lower())
                    frequencies = Counter(words)
            except FileNotFoundError:
                pass
        return frequencies

    def _learn_tonal_patterns(self) -> Dict[str, List[str]]:
        patterns = {}
        for word in self.lexicon:
            p = self._extract_tonal_pattern(word)
            patterns.setdefault(p, []).append(word)
        return patterns

    def _extract_tonal_pattern(self, word: str) -> str:
        pattern = []
        for ch in word:
            if ch in 'àèìòùÀÈÌÒÙ':
                pattern.append('L')
            elif ch in 'áéíóúÁÉÍÓÚ':
                pattern.append('H')
            elif ch in 'āēīōūĀĒĪŌŪ':
                pattern.append('M')
            else:
                pattern.append('_')
        return ''.join(pattern)

    def _contextual_score(self, word: str, context_words: List[str]) -> float:
        if not self.word_frequencies:
            return 1.0
        freq = self.word_frequencies.get(word.lower(), 0)
        max_freq = max(self.word_frequencies.values()) if self.word_frequencies else 1
        return freq / max_freq if max_freq else 0.5

    def exact_match(self, word: str) -> bool:
        return word in self.lexicon

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def _normalize_word(self, word: str) -> str:
        return self.strip_diacritics(word)

    def find_closest_matches(self, word: str, max_matches: int = 3, max_distance: int = 2) -> List[str]:
        if self.exact_match(word):
            return [word]

        normalized_input = self._normalize_word(word)
        matches = []

        for norm, originals in self.normalized_lexicon.items():
            dist = self._levenshtein_distance(normalized_input, norm)
            if dist <= max_distance:
                for orig in originals:
                    matches.append((orig, dist))

        matches.sort(key=lambda x: x[1])
        return [m[0] for m in matches[:max_matches]]

    def disambiguate_tonal_variants(self, matches: List[str], context: str = "") -> str:
        if len(matches) == 1:
            return matches[0]

        scored = []
        for match in matches:
            score = self._contextual_score(match, context.split())
            scored.append((match, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]

    def correct_text_with_context(self, text: str) -> str:
        """
        Main enhanced correction method.
        Context-aware correction + tonal disambiguation.
        """
        words = text.split()
        corrected = []

        for i, word in enumerate(words):

            if self.exact_match(word):
                corrected.append(word)
                continue

            context_start = max(0, i - 2)
            context_end = min(len(words), i + 3)
            context = ' '.join(words[context_start:context_end])

            matches = self.find_closest_matches(word, max_matches=5)

            if matches:
                best = self.disambiguate_tonal_variants(matches, context)
                corrected.append(best)
            else:
                corrected.append(word)

        return ' '.join(corrected)
