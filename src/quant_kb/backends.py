from __future__ import annotations

import hashlib
import math
import uuid
from collections.abc import Sequence
from typing import Protocol

from .models import KnowledgeDocument
from .text import tokenize


class Embedder(Protocol):
    @property
    def dimension(self) -> int: ...

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """Deterministic local embedding for tests and smoke deployments."""

    def __init__(self, dimension: int = 384) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        features = tokenize(text)
        compact = "".join(text.lower().split())
        features.extend(
            compact[index : index + 3] for index in range(max(0, len(compact) - 2))
        )
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


class SentenceTransformerEmbedder:
    def __init__(self, model_path: str, device: str = "cpu") -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                '请安装 BGE 依赖：pip install -e ".[bge]"'
            ) from exc
        self._model = SentenceTransformer(
            model_path, device=device, local_files_only=True
        )
        self._dimension = int(self._model.get_sentence_embedding_dimension())

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self._model.encode(
            list(texts), normalize_embeddings=True, show_progress_bar=False
        )
        return vectors.tolist()


class VectorIndex(Protocol):
    def rebuild(self, documents: list[KnowledgeDocument]) -> None: ...

    def search(
        self,
        query_vector: list[float],
        limit: int,
        categories: set[str] | None = None,
    ) -> list[tuple[str, float]]: ...


class MemoryVectorIndex:
    def __init__(self, embedder: Embedder) -> None:
        self._embedder = embedder
        self._documents: dict[str, KnowledgeDocument] = {}
        self._vectors: dict[str, list[float]] = {}

    def rebuild(self, documents: list[KnowledgeDocument]) -> None:
        vectors = self._embedder.embed(
            [document.searchable_text for document in documents]
        )
        self._documents = {document.id: document for document in documents}
        self._vectors = {
            document.id: vector
            for document, vector in zip(documents, vectors, strict=True)
        }

    def search(
        self,
        query_vector: list[float],
        limit: int,
        categories: set[str] | None = None,
    ) -> list[tuple[str, float]]:
        scores = []
        for document_id, vector in self._vectors.items():
            document = self._documents[document_id]
            if categories and document.category not in categories:
                continue
            score = sum(
                left * right
                for left, right in zip(query_vector, vector, strict=True)
            )
            scores.append((document_id, score))
        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[:limit]


class QdrantVectorIndex:
    def __init__(self, embedder: Embedder, url: str, collection: str) -> None:
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise RuntimeError(
                '请安装 Qdrant 依赖：pip install -e ".[qdrant]"'
            ) from exc
        self._embedder = embedder
        self._client = QdrantClient(url=url)
        self._collection = collection

    def rebuild(self, documents: list[KnowledgeDocument]) -> None:
        from qdrant_client import models

        if self._client.collection_exists(self._collection):
            self._client.delete_collection(self._collection)
        self._client.create_collection(
            collection_name=self._collection,
            vectors_config=models.VectorParams(
                size=self._embedder.dimension, distance=models.Distance.COSINE
            ),
        )
        vectors = self._embedder.embed(
            [document.searchable_text for document in documents]
        )
        points = [
            models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, document.id)),
                vector=vector,
                payload=document.to_payload(),
            )
            for document, vector in zip(documents, vectors, strict=True)
        ]
        if points:
            self._client.upsert(
                collection_name=self._collection, points=points, wait=True
            )

    def search(
        self,
        query_vector: list[float],
        limit: int,
        categories: set[str] | None = None,
    ) -> list[tuple[str, float]]:
        from qdrant_client import models

        query_filter = None
        if categories:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="category",
                        match=models.MatchAny(any=sorted(categories)),
                    )
                ]
            )
        result = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        return [
            (str(point.payload["id"]), float(point.score))
            for point in result.points
            if point.payload and point.payload.get("id")
        ]


def create_embedder(backend: str, model_path: str, device: str) -> Embedder:
    if backend == "hashing":
        return HashingEmbedder()
    return SentenceTransformerEmbedder(model_path=model_path, device=device)


def create_vector_index(
    backend: str,
    embedder: Embedder,
    qdrant_url: str,
    qdrant_collection: str,
) -> VectorIndex:
    if backend == "memory":
        return MemoryVectorIndex(embedder)
    return QdrantVectorIndex(embedder, qdrant_url, qdrant_collection)

