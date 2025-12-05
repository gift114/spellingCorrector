# correctors/ml_components.py
import os
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple
import numpy as np

# Try to import heavy ML libs only when available
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False

class TransformerDiacriticRestorer:
    """Transformer-based model for Yorùbá diacritic restoration.
    Loading is optional — the class supports a no-model fallback.
    """
    def __init__(self, model_name="bert-base-multilingual-cased", load_model: bool = False):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = None
        self.diacritic_map = {
            'a': ['a', 'à', 'á', 'ā'],
            'e': ['e', 'è', 'é', 'ē'],
            'i': ['i', 'ì', 'í', 'ī'],
            'o': ['o', 'ò', 'ó', 'ō'],
            'u': ['u', 'ù', 'ú', 'ū'],
            's': ['s', 'ṣ'],
            'E': ['E', 'Ẹ'],
            'O': ['O', 'Ọ']
        }
        self.reverse_diacritic_map = {}
        for base, variants in self.diacritic_map.items():
            for var in variants:
                self.reverse_diacritic_map[var] = base

        if load_model and TORCH_AVAILABLE:
            self._load_model()
        else:
            # no model loaded — safe fallback
            self.model = None
            self.tokenizer = None
            self.device = None

    def _load_model(self):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            self.model.eval()
            print(f"✅ Transformer loaded: {self.model_name} on {self.device}")
        except Exception as e:
            print(f"⚠️ Transformer failed to load ({e}). Continuing without transformer.")
            self.model = None
            self.tokenizer = None
            self.device = None

    def strip_diacritics(self, text: str) -> str:
        """Map diacritic chars to base chars; fallback if model absent."""
        return ''.join(self.reverse_diacritic_map.get(char, char) for char in text)

    def get_contextual_embeddings(self, text: str) -> np.ndarray:
        """Return contextual embeddings if model is loaded; fallback vector otherwise."""
        if not self.model or not self.tokenizer:
            return np.zeros(768)
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs)
        embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        return embeddings[0]

    def restore_diacritics_word(self, word: str, context: str = "") -> str:
        """Try restoring diacritics. If transformer isn't available, use rule-based mapping."""
        if not any(char in self.reverse_diacritic_map for char in word):
            # If word contains no diacritic characters, attempt to map from base -> known patterns.
            # Note: We keep it conservative when no transformer is available.
            base = self.strip_diacritics(word)
        else:
            base = word

        # Small set of common patterns - safe fallback
        common_patterns = {
            'ile': 'ilé',
            'omo': 'ọmọ',
            'ise': 'iṣẹ́',
            'fe': 'fẹ́',
            'ka': 'kà',
            'kawe': 'kàwé',
            'yoruba': 'Yorùbá',
            'baba': 'bàbá',
            'iya': 'ìyá'
        }
        base_norm = base.lower()
        if base_norm in common_patterns:
            return common_patterns[base_norm]

        # If transformer model exists, we could do more advanced restoration; but keep conservative.
        return word
        

class NGramLanguageModel:
    """N-gram language model for lightweight context scoring."""
    def __init__(self, n: int = 3):
        self.n = n
        self.ngrams = defaultdict(Counter)
        self.vocab = set()
        self.total_words = 0

    def train(self, corpus: List[str]):
        for text in corpus:
            words = text.split()
            if not words:
                continue
            self.total_words += len(words)
            self.vocab.update(words)
            for i in range(len(words) - self.n + 1):
                context = tuple(words[i:i + self.n - 1])
                next_word = words[i + self.n - 1]
                self.ngrams[context][next_word] += 1

    def probability(self, word: str, context: List[str]) -> float:
        if len(context) < self.n - 1:
            context = [""] * (self.n - 1 - len(context)) + context
        context_tuple = tuple(context[-(self.n - 1):])
        if context_tuple in self.ngrams and word in self.ngrams[context_tuple]:
            count = self.ngrams[context_tuple][word]
            total = sum(self.ngrams[context_tuple].values())
            return count / total
        # Laplace smoothing
        return 1.0 / (len(self.vocab) + 1) if self.vocab else 1e-6

    def predict_next_word(self, context: List[str], candidates: List[str]) -> str:
        if not candidates:
            return ""
        best_word = candidates[0]
        best_prob = self.probability(best_word, context)
        for candidate in candidates[1:]:
            prob = self.probability(candidate, context)
            if prob > best_prob:
                best_word = candidate
                best_prob = prob
        return best_word

    def score_sentence(self, sentence: str) -> float:
        words = sentence.split()
        if len(words) < self.n:
            return 0.0
        total = 0.0
        for i in range(self.n - 1, len(words)):
            context = words[max(0, i - self.n + 1):i]
            word = words[i]
            prob = self.probability(word, context)
            total += np.log(prob + 1e-10)
        return total


class ContextAwareCorrector:
    """Wrapper that uses the transformer restorer and n-gram model to provide ML-aware corrections."""
    def __init__(self, lexicon_path: str, corpus_path: str = None, load_transformer: bool = False):
        self.lexicon = {}
        self.lexicon_path = lexicon_path
        self._load_lexicon()
        # instantiate diacritic restorer (transformer optional)
        self.diacritic_restorer = TransformerDiacriticRestorer(load_model=load_transformer)
        self.ngram_model = NGramLanguageModel(n=3)
        self._train_ngram_model(corpus_path)

    def _load_lexicon(self):
        try:
            with open(self.lexicon_path, 'r', encoding='utf-8') as f:
                for line in f:
                    w = line.strip()
                    if w and not w.startswith('#'):
                        self.lexicon[w] = True
            print(f"✅ ML: loaded lexicon with {len(self.lexicon)} words")
        except Exception as e:
            print(f"⚠️ ML: failed to load lexicon ({e})")

    def _train_ngram_model(self, corpus_path: str = None):
        default_corpus = [
            "mo fẹ́ kàwé ní ilé ẹ̀kọ́",
            "àwọn ọmọ ilé kàwé lọ sí ilé ẹ̀kọ́",
            "bàbá àti ìyá ràwé fún àwọn ọmọ wọn",
            "owó mi dùn láti rí iṣẹ́ tuntun",
            "ilé náà tóbi jùlọ",
            "ọmọ náà dára púpọ̀",
            "ìwé mi wà ní ilé",
            "báwo ni o ṣe wà lónìí",
            "iṣẹ́ yín dùn o, ẹ jẹ́ kí n rí i",
            "a dúpẹ́ o fún ìrànlọ́wọ́ yín"
        ]
        if corpus_path:
            try:
                with open(corpus_path, 'r', encoding='utf-8') as f:
                    corpus = [line.strip() for line in f if line.strip()]
            except Exception:
                corpus = default_corpus
        else:
            corpus = default_corpus
        self.ngram_model.train(corpus)

    def restore_sentence_diacritics(self, sentence: str) -> str:
        words = sentence.split()
        restored = []
        for i, w in enumerate(words):
            start = max(0, i - 2)
            end = min(len(words), i + 3)
            context = ' '.join(words[start:end])
            restored_word = self.diacritic_restorer.restore_diacritics_word(w, context)
            restored.append(restored_word)
        return ' '.join(restored)

    def correct_text_with_ml(self, text: str) -> str:
        # 1) restore diacritics
        restored = self.restore_sentence_diacritics(text)
        words = restored.split()
        corrected = []
        for i, w in enumerate(words):
            if w in self.lexicon:
                corrected.append(w)
                continue
            # find candidates by normalization check
            normalized = self.diacritic_restorer.strip_diacritics(w).lower()
            candidates = [lex for lex in self.lexicon.keys()
                          if self.diacritic_restorer.strip_diacritics(lex).lower() == normalized]
            if candidates:
                context_start = max(0, i - 2)
                context = words[context_start:i]
                best = self.ngram_model.predict_next_word(context, candidates)
                corrected.append(best or candidates[0])
            else:
                corrected.append(w)
        return ' '.join(corrected)
