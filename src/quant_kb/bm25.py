from __future__ import annotations

import math
from collections import Counter

from .models import KnowledgeDocument
from .text import tokenize


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._documents: dict[str, KnowledgeDocument] = {}
        self._term_frequencies: dict[str, Counter[str]] = {}
        self._document_frequency: Counter[str] = Counter()
        self._average_length = 0.0

    def build(self, documents: list[KnowledgeDocument]) -> None:
        self._documents = {document.id: document for document in documents}
        self._term_frequencies = {}
        self._document_frequency = Counter()
        lengths: list[int] = []
        for document in documents:
            terms = tokenize(document.searchable_text)
            frequency = Counter(terms)
            self._term_frequencies[document.id] = frequency
            self._document_frequency.update(frequency.keys())
            lengths.append(len(terms))
        self._average_length = sum(lengths) / len(lengths) if lengths else 0.0

    def search(
        self, query: str, limit: int, categories: set[str] | None = None
    ) -> list[tuple[str, float]]:
        query_terms = tokenize(query)
        if not query_terms or not self._documents:
            return []
        scores: list[tuple[str, float]] = []
        document_count = len(self._documents)
        for document_id, frequency in self._term_frequencies.items():
            document = self._documents[document_id]
            if categories and document.category not in categories:
                continue
            document_length = sum(frequency.values())
            score = 0.0
            for term in query_terms:
                term_frequency = frequency.get(term, 0)
                if not term_frequency:
                    continue
                df = self._document_frequency[term]
                idf = math.log(1 + (document_count - df + 0.5) / (df + 0.5))
                norm = self.k1 * (
                    1
                    - self.b
                    + self.b * document_length / max(self._average_length, 1.0)
                )
                score += (
                    idf
                    * term_frequency
                    * (self.k1 + 1)
                    / (term_frequency + norm)
                )
            if score > 0:
                scores.append((document_id, score))
        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[:limit]

