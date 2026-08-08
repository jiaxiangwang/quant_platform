from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    knowledge_dir: Path
    vector_backend: str = "memory"
    embedding_backend: str = "hashing"
    reranker_backend: str = "lexical"
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_collection: str = "quant_knowledge"
    embedding_model: str = "/models/bge-m3"
    reranker_model: str = "/models/bge-reranker-v2-m3"
    model_device: str = "cpu"
    hybrid_alpha: float = 0.55
    rerank_weight: float = 0.45
    retrieve_k: int = 20

    @classmethod
    def from_env(cls) -> "Settings":
        settings = cls(
            knowledge_dir=Path(os.getenv("KB_KNOWLEDGE_DIR", "knowledge")).resolve(),
            vector_backend=os.getenv("KB_VECTOR_BACKEND", "memory").lower(),
            embedding_backend=os.getenv("KB_EMBEDDING_BACKEND", "hashing").lower(),
            reranker_backend=os.getenv("KB_RERANKER_BACKEND", "lexical").lower(),
            qdrant_url=os.getenv("KB_QDRANT_URL", "http://127.0.0.1:6333"),
            qdrant_collection=os.getenv("KB_QDRANT_COLLECTION", "quant_knowledge"),
            embedding_model=os.getenv("KB_EMBEDDING_MODEL", "/models/bge-m3"),
            reranker_model=os.getenv(
                "KB_RERANKER_MODEL", "/models/bge-reranker-v2-m3"
            ),
            model_device=os.getenv("KB_MODEL_DEVICE", "cpu"),
            hybrid_alpha=float(os.getenv("KB_HYBRID_ALPHA", "0.55")),
            rerank_weight=float(os.getenv("KB_RERANK_WEIGHT", "0.45")),
            retrieve_k=int(os.getenv("KB_RETRIEVE_K", "20")),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.vector_backend not in {"memory", "qdrant"}:
            raise ValueError("KB_VECTOR_BACKEND 仅支持 memory 或 qdrant")
        if self.embedding_backend not in {"hashing", "sentence_transformers"}:
            raise ValueError(
                "KB_EMBEDDING_BACKEND 仅支持 hashing 或 sentence_transformers"
            )
        if self.reranker_backend not in {"lexical", "cross_encoder"}:
            raise ValueError("KB_RERANKER_BACKEND 仅支持 lexical 或 cross_encoder")
        if not 0 <= self.hybrid_alpha <= 1:
            raise ValueError("KB_HYBRID_ALPHA 必须在 0 到 1 之间")
        if not 0 <= self.rerank_weight <= 1:
            raise ValueError("KB_RERANK_WEIGHT 必须在 0 到 1 之间")
        if self.retrieve_k < 1:
            raise ValueError("KB_RETRIEVE_K 必须大于 0")
