from __future__ import annotations

from contextlib import asynccontextmanager

from pydantic import BaseModel, Field

from .config import Settings
from .service import KnowledgeSearchService

try:
    from fastapi import FastAPI, HTTPException, Request
except ImportError:
    FastAPI = None
    HTTPException = None
    Request = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    categories: list[str] | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[dict]


def create_app(settings: Settings | None = None):
    if FastAPI is None:
        raise RuntimeError(
            '请安装 API 依赖：pip install -e ".[api]"'
        )

    @asynccontextmanager
    async def lifespan(app):
        app.state.knowledge_service = KnowledgeSearchService(settings)
        yield

    app = FastAPI(
        title="Quant Platform Knowledge API",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    def health(request: Request) -> dict:
        service = request.app.state.knowledge_service
        return {
            "status": "ok",
            "knowledge_dir": str(service.settings.knowledge_dir),
        }

    @app.post("/v1/search", response_model=SearchResponse)
    def search(payload: SearchRequest, request: Request) -> SearchResponse:
        service = request.app.state.knowledge_service
        try:
            results = service.search(
                payload.query, payload.categories, payload.top_k
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return SearchResponse(
            query=payload.query,
            count=len(results),
            results=[result.to_dict() for result in results],
        )

    return app


def app_factory():
    return create_app()
