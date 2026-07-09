"""SOP 检索：关键词匹配（默认）+ 可选 embedding 向量检索。"""

from __future__ import annotations

import math
import re
from functools import lru_cache

from sqlalchemy.orm import Session

from ...settings import get_settings
from ..llm import get_llm_client
from .chunks import SopChunk, load_sop_chunks

_TOKEN_RE = re.compile(r"[\u4e00-\u9fff]{2,}|[a-zA-Z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _keyword_score(query: str, chunk: SopChunk) -> float:
    haystack = f"{chunk.station_name} {chunk.station_code} {chunk.product_name} {chunk.text}"
    haystack_l = haystack.lower()
    score = 0.0
    for token in _tokenize(query):
        if token in haystack_l:
            score += 1.0
    if chunk.station_name in query:
        score += 3.0
    if chunk.chunk_type == "safety" and any(k in query for k in ("安全", "注意", "防护", "危险")):
        score += 1.5
    if chunk.chunk_type == "sop" and any(k in query for k in ("步骤", "操作", "流程", "装配", "SOP")):
        score += 1.0
    return score


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class SopRetriever:
    def __init__(self) -> None:
        self._chunks: list[SopChunk] = []
        self._embeddings: list[list[float]] | None = None

    def build_index(self, db: Session) -> int:
        self._chunks = load_sop_chunks(db)
        self._embeddings = None

        settings = get_settings()
        if not settings.embedding_model:
            return len(self._chunks)

        texts = [self._chunk_document(c) for c in self._chunks]
        client = get_llm_client()
        response = client.embeddings.create(model=settings.embedding_model, input=texts)
        ordered = sorted(response.data, key=lambda item: item.index)
        self._embeddings = [item.embedding for item in ordered]
        return len(self._chunks)

    def search(self, query: str, top_k: int = 3, station_name: str | None = None) -> list[dict]:
        if not self._chunks:
            return []

        candidates = self._chunks
        if station_name:
            filtered = [c for c in candidates if station_name in c.station_name]
            if filtered:
                candidates = filtered

        if self._embeddings:
            ranked = self._search_by_embedding(query, candidates, top_k)
        else:
            ranked = self._search_by_keyword(query, candidates, top_k)

        return [
            {
                "station_code": c.station_code,
                "station_name": c.station_name,
                "product_name": c.product_name,
                "type": c.chunk_type,
                "text": c.text,
                "score": round(score, 4),
            }
            for c, score in ranked
        ]

    def _search_by_keyword(
        self, query: str, candidates: list[SopChunk], top_k: int
    ) -> list[tuple[SopChunk, float]]:
        scored = [(c, _keyword_score(query, c)) for c in candidates]
        scored = [(c, s) for c, s in scored if s > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def _search_by_embedding(
        self, query: str, candidates: list[SopChunk], top_k: int
    ) -> list[tuple[SopChunk, float]]:
        settings = get_settings()
        client = get_llm_client()
        q_emb = client.embeddings.create(model=settings.embedding_model, input=[query]).data[0].embedding

        scored: list[tuple[SopChunk, float]] = []
        for chunk in candidates:
            idx = self._chunks.index(chunk)
            sim = _cosine(q_emb, self._embeddings[idx])
            scored.append((chunk, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    @staticmethod
    def _chunk_document(chunk: SopChunk) -> str:
        type_label = "安全注意事项" if chunk.chunk_type == "safety" else "作业步骤"
        return (
            f"产品：{chunk.product_name}\n"
            f"工位：{chunk.station_name}（{chunk.station_code}）\n"
            f"类型：{type_label}\n"
            f"{chunk.text}"
        )


@lru_cache()
def get_sop_retriever() -> SopRetriever:
    return SopRetriever()
