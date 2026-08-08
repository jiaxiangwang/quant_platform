from __future__ import annotations

import json
from collections.abc import Callable

from .service import KnowledgeSearchService


def create_knowledge_search_tool(
    service: KnowledgeSearchService | None = None,
) -> Callable[..., str]:
    """Create a DeepAgents/LangChain-compatible knowledge_search tool."""
    knowledge_service = service or KnowledgeSearchService()

    def knowledge_search(
        query: str,
        categories: list[str] | None = None,
        top_k: int = 5,
    ) -> str:
        """检索固收、指标、量化 SDK、策略案例及平台规范知识。"""
        results = knowledge_service.search(query, categories, top_k)
        payload = {
            "query": query,
            "count": len(results),
            "results": [result.to_dict() for result in results],
        }
        return json.dumps(payload, ensure_ascii=False)

    try:
        from langchain_core.tools import tool
    except ImportError:
        knowledge_search.name = "knowledge_search"  # type: ignore[attr-defined]
        knowledge_search.description = knowledge_search.__doc__  # type: ignore[attr-defined]
        return knowledge_search
    return tool(
        "knowledge_search",
        description=knowledge_search.__doc__,
    )(knowledge_search)

