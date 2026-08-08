from __future__ import annotations

import argparse
import json

from .config import Settings
from .service import KnowledgeSearchService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="量化平台知识库")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="搜索知识库")
    search.add_argument("query")
    search.add_argument("--category", action="append", dest="categories")
    search.add_argument("--top-k", type=int, default=5)

    subparsers.add_parser("reindex", help="重建索引")

    serve = subparsers.add_parser("serve", help="启动 FastAPI")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "serve":
        try:
            import uvicorn
        except ImportError as exc:
            raise SystemExit(
                '请安装 API 依赖：pip install -e ".[api]"'
            ) from exc
        uvicorn.run(
            "quant_kb.api:app_factory",
            factory=True,
            host=args.host,
            port=args.port,
        )
        return

    service = KnowledgeSearchService(Settings.from_env())
    if args.command == "reindex":
        print(
            json.dumps(
                {"indexed": service.document_count},
                ensure_ascii=False,
            )
        )
        return
    results = service.search(args.query, args.categories, args.top_k)
    print(
        json.dumps(
            [result.to_dict() for result in results],
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
