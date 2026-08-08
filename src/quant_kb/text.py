from __future__ import annotations

import re

_ASCII_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*|\d+(?:\.\d+)?")
_CHINESE_RUN = re.compile(r"[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    """Tokenize Chinese prose and SDK identifiers without an external segmenter."""
    normalized = text.lower()
    tokens: list[str] = []
    for token in _ASCII_TOKEN.findall(normalized):
        tokens.append(token)
        tokens.extend(
            part for part in re.split(r"[_.-]", token) if part and part != token
        )
    for run in _CHINESE_RUN.findall(normalized):
        tokens.append(run)
        tokens.extend(run)
        tokens.extend(run[index : index + 2] for index in range(len(run) - 1))
        tokens.extend(run[index : index + 3] for index in range(len(run) - 2))
    return tokens


def lexical_similarity(query: str, text: str) -> float:
    query_tokens = set(tokenize(query))
    text_tokens = set(tokenize(text))
    if not query_tokens or not text_tokens:
        return 0.0
    overlap = len(query_tokens & text_tokens) / len(query_tokens)
    phrase_bonus = 0.2 if query.strip().lower() in text.lower() else 0.0
    return min(1.0, overlap + phrase_bonus)


def make_snippet(text: str, query: str, limit: int = 240) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    tokens = sorted(set(tokenize(query)), key=len, reverse=True)
    positions = [compact.lower().find(token) for token in tokens if len(token) > 1]
    positions = [position for position in positions if position >= 0]
    center = min(positions) if positions else 0
    start = max(0, center - limit // 3)
    end = min(len(compact), start + limit)
    prefix = "…" if start else ""
    suffix = "…" if end < len(compact) else ""
    return f"{prefix}{compact[start:end]}{suffix}"

