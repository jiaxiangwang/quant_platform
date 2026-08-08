from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import KnowledgeDocument

_SUPPORTED_SUFFIXES = {".md", ".markdown", ".yaml", ".yml"}


def load_documents(root: Path) -> list[KnowledgeDocument]:
    if not root.exists():
        raise FileNotFoundError(f"知识目录不存在：{root}")
    documents: list[KnowledgeDocument] = []
    seen_ids: set[str] = set()
    paths = (
        item
        for item in root.rglob("*")
        if item.is_file() and item.suffix.lower() in _SUPPORTED_SUFFIXES
    )
    for path in sorted(paths):
        document = _load_document(path, root)
        if document.id in seen_ids:
            raise ValueError(f"知识 id 重复：{document.id}（{path}）")
        seen_ids.add(document.id)
        documents.append(document)
    if not documents:
        raise ValueError(f"知识目录中没有 Markdown/YAML 文件：{root}")
    return documents


def _load_document(path: Path, root: Path) -> KnowledgeDocument:
    raw = path.read_text(encoding="utf-8")
    relative = path.relative_to(root).as_posix()
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError(f"YAML 顶层必须是对象：{path}")
        metadata = dict(data)
        content = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    else:
        metadata, content = _parse_front_matter(raw, path)
    required = [
        name for name in ("id", "title", "category") if not metadata.get(name)
    ]
    if required:
        raise ValueError(f"{path} 缺少字段：{', '.join(required)}")
    public_metadata = {
        key: value
        for key, value in metadata.items()
        if key not in {"id", "title", "category"}
    }
    return KnowledgeDocument(
        id=str(metadata["id"]),
        title=str(metadata["title"]),
        category=str(metadata["category"]),
        content=content.strip(),
        source=relative,
        metadata=public_metadata,
    )


def _parse_front_matter(raw: str, path: Path) -> tuple[dict[str, Any], str]:
    if not raw.startswith("---\n"):
        raise ValueError(f"Markdown 必须包含 YAML front matter：{path}")
    marker = raw.find("\n---\n", 4)
    if marker < 0:
        raise ValueError(f"Markdown front matter 未结束：{path}")
    metadata = yaml.safe_load(raw[4:marker]) or {}
    if not isinstance(metadata, dict):
        raise ValueError(f"Markdown front matter 必须是对象：{path}")
    return metadata, raw[marker + 5 :]

