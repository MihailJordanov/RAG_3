import json
from typing import List, Dict, Any

from langchain_core.documents import Document

from app.core.config import settings


def _doc_raw_text(doc: Document, limit: int = 4000) -> str:
    """
    Prefer raw extracted text from metadata if present.
    Fallback to page_content.
    """
    try:
        if "original_content" in doc.metadata:
            original = json.loads(doc.metadata["original_content"])
            raw = original.get("raw_text", "") or ""
            if raw.strip():
                return raw[:limit]
    except Exception:
        pass

    return (doc.page_content or "")[:limit]


def _build_rerank_text(doc: Document, limit: int = 4000) -> str:
    """
    Build the text that will be sent to the reranker.
    Includes raw text + optional table content when available.
    """
    parts: list[str] = []

    raw = _doc_raw_text(doc, limit=limit)
    if raw.strip():
        parts.append(raw)

    try:
        if "original_content" in doc.metadata:
            original = json.loads(doc.metadata["original_content"])
            tables = original.get("tables_html", []) or []
            if tables:
                parts.append("\nTABLES:\n")
                for i, t in enumerate(tables, start=1):
                    parts.append(f"Table {i}:\n{t}\n")
    except Exception:
        pass

    text = "\n".join(parts).strip()
    return text[:limit]


def _normalize_meta_score(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def rerank_fused_results(
    query: str,
    fused: List[Dict[str, Any]],
    top_n: int,
) -> List[Dict[str, Any]]:
    """
    Rerank already-fused results with Cohere if available.

    Input item format (same style as your current fused items):
    {
        "doc": Document,
        "best_distance": float,
        "rrf_score": float,
        "hits": int,
        "vector_hits": int,
        "bm25_hits": int,
    }

    Returns the same structure, reordered, with extra optional fields:
    - rerank_score
    - rerank_applied
    """
    if not fused:
        return []

    # If no Cohere key is configured, skip reranking gracefully
    cohere_api_key = getattr(settings, "cohere_api_key", None)
    if not cohere_api_key:
        out = []
        for item in fused[:top_n]:
            cloned = dict(item)
            cloned["rerank_score"] = None
            cloned["rerank_applied"] = False
            out.append(cloned)
        return out

    # Lazy import so project still works without cohere package installed
    try:
        import cohere
    except Exception:
        out = []
        for item in fused[:top_n]:
            cloned = dict(item)
            cloned["rerank_score"] = None
            cloned["rerank_applied"] = False
            out.append(cloned)
        return out

    model_name = getattr(settings, "cohere_rerank_model", "rerank-v3.5")
    client = cohere.Client(api_key=cohere_api_key)

    docs_for_rerank: list[str] = []
    for item in fused:
        doc = item["doc"]
        docs_for_rerank.append(_build_rerank_text(doc, limit=4000))

    try:
        response = client.rerank(
            model=model_name,
            query=query,
            documents=docs_for_rerank,
            top_n=min(top_n, len(docs_for_rerank)),
        )
    except Exception:
        # Fail open: keep original ranking if reranker fails
        out = []
        for item in fused[:top_n]:
            cloned = dict(item)
            cloned["rerank_score"] = None
            cloned["rerank_applied"] = False
            out.append(cloned)
        return out

    reranked: list[Dict[str, Any]] = []
    used_indexes = set()

    for result in response.results:
        idx = int(result.index)
        used_indexes.add(idx)

        base = dict(fused[idx])
        base["rerank_score"] = _normalize_meta_score(
            getattr(result, "relevance_score", None),
            default=0.0,
        )
        base["rerank_applied"] = True
        reranked.append(base)

    # Safety fallback: if Cohere returns fewer docs than expected
    if len(reranked) < top_n:
        for i, item in enumerate(fused):
            if i in used_indexes:
                continue
            cloned = dict(item)
            cloned["rerank_score"] = None
            cloned["rerank_applied"] = True
            reranked.append(cloned)
            if len(reranked) >= top_n:
                break

    return reranked[:top_n]