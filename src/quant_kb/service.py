from __future__ import annotations

from .backends import create_embedder, create_vector_index
from .bm25 import BM25Index
from .config import Settings
from .loaders import load_documents
from .models import KnowledgeDocument, SearchResult
from .rerankers import create_reranker
from .text import make_snippet


class KnowledgeSearchService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.settings.validate()
        self._embedder = create_embedder(
            self.settings.embedding_backend,
            self.settings.embedding_model,
            self.settings.model_device,
        )
        self._vector_index = create_vector_index(
            self.settings.vector_backend,
            self._embedder,
            self.settings.qdrant_url,
            self.settings.qdrant_collection,
        )
        self._reranker = create_reranker(
            self.settings.reranker_backend,
            self.settings.reranker_model,
            self.settings.model_device,
        )
        self._bm25 = BM25Index()
        self._documents: dict[str, KnowledgeDocument] = {}
        self.reindex()

    def reindex(self) -> int:
        documents = load_documents(self.settings.knowledge_dir)
        self._documents = {document.id: document for document in documents}
        self._bm25.build(documents)
        self._vector_index.rebuild(documents)
        return len(documents)

    @property
    def document_count(self) -> int:
        return len(self._documents)

    def search(
        self,
        query: str,
        categories: list[str] | None = None,
        top_k: int = 5,
    ) -> list[SearchResult]:
        query = query.strip()
        if not query:
            raise ValueError("query 不能为空")
        if top_k < 1 or top_k > 20:
            raise ValueError("top_k 必须在 1 到 20 之间")
        category_filter = set(categories) if categories else None
        candidate_limit = max(top_k, self.settings.retrieve_k)
        bm25_raw = dict(
            self._bm25.search(query, candidate_limit, category_filter)
        )
        query_vector = self._embedder.embed([query])[0]
        vector_raw = dict(
            self._vector_index.search(
                query_vector, candidate_limit, category_filter
            )
        )
        bm25_scores = _normalize_positive(bm25_raw)
        vector_scores = _normalize_positive(vector_raw)
        candidate_ids = set(bm25_scores) | set(vector_scores)
        hybrid_scores = {
            document_id: (
                (1 - self.settings.hybrid_alpha)
                * bm25_scores.get(document_id, 0.0)
                + self.settings.hybrid_alpha
                * vector_scores.get(document_id, 0.0)
            )
            for document_id in candidate_ids
        }
        ranked_ids = sorted(
            candidate_ids, key=hybrid_scores.get, reverse=True
        )[:candidate_limit]
        documents = [self._documents[document_id] for document_id in ranked_ids]
        rerank_scores = self._reranker.score(query, documents)
        results = []
        for document, rerank_score in zip(
            documents, rerank_scores, strict=True
        ):
            hybrid = hybrid_scores[document.id]
            final_score = (
                (1 - self.settings.rerank_weight) * hybrid
                + self.settings.rerank_weight * rerank_score
            )
            results.append(
                SearchResult(
                    document=document,
                    score=final_score,
                    bm25_score=bm25_scores.get(document.id, 0.0),
                    vector_score=vector_scores.get(document.id, 0.0),
                    rerank_score=rerank_score,
                    snippet=make_snippet(document.content, query),
                )
            )
        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]


def _normalize_positive(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    floor = min(0.0, min(scores.values()))
    shifted = {
        key: max(0.0, value - floor) for key, value in scores.items()
    }
    maximum = max(shifted.values())
    if maximum <= 0:
        return {key: 0.0 for key in scores}
    return {key: value / maximum for key, value in shifted.items()}
