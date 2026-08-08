from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Protocol

from .models import KnowledgeDocument
from .text import lexical_similarity


class Reranker(Protocol):
    def score(
        self, query: str, documents: Sequence[KnowledgeDocument]
    ) -> list[float]: ...


class LexicalReranker:
    def score(
        self, query: str, documents: Sequence[KnowledgeDocument]
    ) -> list[float]:
        scores = []
        for document in documents:
            keywords = document.metadata.get("keywords", [])
            if isinstance(keywords, list):
                keyword_text = " ".join(str(item) for item in keywords)
            else:
                keyword_text = str(keywords)
            header_text = f"{document.title}\n{keyword_text}"
            body_score = lexical_similarity(query, document.searchable_text)
            header_score = lexical_similarity(query, header_text)
            scores.append(min(1.0, 0.35 * body_score + 0.65 * header_score))
        return scores


class CrossEncoderReranker:
    def __init__(self, model_path: str, device: str = "cpu") -> None:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise RuntimeError(
                '请安装 BGE 依赖：pip install -e ".[bge]"'
            ) from exc
        self._model = CrossEncoder(
            model_path, device=device, local_files_only=True
        )

    def score(
        self, query: str, documents: Sequence[KnowledgeDocument]
    ) -> list[float]:
        raw_scores = self._model.predict(
            [(query, document.searchable_text) for document in documents],
            show_progress_bar=False,
        )
        return [1 / (1 + math.exp(-float(score))) for score in raw_scores]


def create_reranker(backend: str, model_path: str, device: str) -> Reranker:
    if backend == "lexical":
        return LexicalReranker()
    return CrossEncoderReranker(model_path=model_path, device=device)
