from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class KnowledgeDocument:
    id: str
    title: str
    category: str
    content: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def searchable_text(self) -> str:
        keywords = self.metadata.get("keywords", [])
        if isinstance(keywords, list):
            keyword_text = " ".join(str(item) for item in keywords)
        else:
            keyword_text = str(keywords)
        return f"{self.title}\n{keyword_text}\n{self.content}"

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "source": self.source,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class SearchResult:
    document: KnowledgeDocument
    score: float
    bm25_score: float
    vector_score: float
    rerank_score: float
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.document.id,
            "title": self.document.title,
            "category": self.document.category,
            "source": self.document.source,
            "score": round(self.score, 6),
            "scores": {
                "bm25": round(self.bm25_score, 6),
                "vector": round(self.vector_score, 6),
                "rerank": round(self.rerank_score, 6),
            },
            "snippet": self.snippet,
            "metadata": self.document.metadata,
        }

