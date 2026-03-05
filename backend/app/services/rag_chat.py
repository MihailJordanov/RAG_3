import json
import hashlib
from typing import Tuple, List, Dict, Any

from pydantic import BaseModel, Field

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import settings
from app.services.storage import project_chroma_dir


DEFAULT_K = 10
DEFAULT_MAX_DISTANCE = 0.90

# Multi-query defaults
DEFAULT_NUM_QUERY_VARIATIONS = 3
DEFAULT_PER_QUERY_K = 5  # how many docs to fetch per variation (RRF works better with >1)
RRF_K = 60  # standard constant for RRF: score += 1/(RRF_K + rank)


class QueryVariations(BaseModel):
    queries: List[str] = Field(default_factory=list)


def load_project_db(project_id: str) -> Chroma:
    persist_dir = project_chroma_dir(project_id)
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.openai_api_key)
    return Chroma(persist_directory=persist_dir, embedding_function=embedding_model)


def retrieve_with_scores(db: Chroma, query: str, k: int):
    # Returns List[Tuple[Document, float]] where lower score = better (cosine distance)
    return db.similarity_search_with_score(query, k=k)


def _doc_raw_text(doc: Document, limit: int = 2000) -> str:
    if "original_content" in doc.metadata:
        original = json.loads(doc.metadata["original_content"])
        raw = original.get("raw_text", "") or ""
        return raw[:limit]
    return (doc.page_content or "")[:limit]


def _doc_dedupe_key(doc: Document) -> str:
    """
    Prefer stable chunk_id if present (we add it in ingest).
    Otherwise hash content+metadata to get a deterministic key.
    """
    chunk_id = doc.metadata.get("chunk_id")
    if chunk_id:
        return f"chunk:{chunk_id}"

    h = hashlib.sha256()
    h.update((doc.page_content or "").encode("utf-8", errors="ignore"))
    # metadata can be large; include only stable-ish bits
    meta = {k: doc.metadata.get(k) for k in sorted(doc.metadata.keys()) if k != "original_content"}
    h.update(json.dumps(meta, sort_keys=True, ensure_ascii=False).encode("utf-8", errors="ignore"))
    return f"hash:{h.hexdigest()}"


def _generate_query_variations(query: str, n: int = DEFAULT_NUM_QUERY_VARIATIONS) -> List[str]:
    """
    Generate N alternative Bulgarian query variations to improve recall.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.openai_api_key)
    llm_struct = llm.with_structured_output(QueryVariations)

    prompt = f"""
Generate {n} different variations of this query that would help retrieve relevant documents.

Rules:
- Keep the meaning.
- Use different phrasing / synonyms / angles.
- Keep them short (1 sentence each).
- Return ONLY the variations (no numbering), in Bulgarian.

Original query: {query}
"""
    resp = llm_struct.invoke(prompt)
    variations = [q.strip() for q in (resp.queries or []) if q and q.strip()]

    # Always include the original query first
    out = [query.strip()]
    for v in variations:
        if v.lower() != query.strip().lower() and v not in out:
            out.append(v)

    # Trim to 1 + n
    return out[: (1 + n)]


def _rrf_fuse(all_results: List[List[tuple[Document, float]]], final_k: int) -> List[Dict[str, Any]]:
    """
    all_results: list over queries -> list of (doc, distance) ranked by retriever
    Return: list of dicts sorted by rrf_score desc
    """
    fused: Dict[str, Dict[str, Any]] = {}

    for result_list in all_results:
        for rank, (doc, distance) in enumerate(result_list, start=1):
            key = _doc_dedupe_key(doc)
            entry = fused.get(key)
            if not entry:
                entry = {
                    "doc": doc,
                    "best_distance": float(distance),
                    "rrf_score": 0.0,
                    "hits": 0,
                }
                fused[key] = entry

            # RRF accumulation (rank-based)
            entry["rrf_score"] += 1.0 / (RRF_K + rank)
            entry["hits"] += 1

            # Track best (min) distance across queries
            if float(distance) < entry["best_distance"]:
                entry["best_distance"] = float(distance)

    ranked = sorted(fused.values(), key=lambda x: (x["rrf_score"], -x["hits"]), reverse=True)
    return ranked[:final_k]


def generate_final_answer(docs: list[Document], query: str) -> str:
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.openai_api_key)

    prompt = """Answer the question using ONLY the provided documents.
If the documents do not contain enough information, say exactly:
"I don't know based on the provided documents."

Question: {q}

DOCUMENTS:
""".format(q=query)

    for i, d in enumerate(docs, start=1):
        prompt += f"\n--- Doc {i} ---\n"
        prompt += _doc_raw_text(d, limit=4000) + "\n"

        if "original_content" in d.metadata:
            original = json.loads(d.metadata["original_content"])
            tables = original.get("tables_html", []) or []
            if tables:
                prompt += "\nTABLES:\n"
                for j, t in enumerate(tables, start=1):
                    prompt += f"Table {j}:\n{t}\n"

    msg = HumanMessage(content=[{"type": "text", "text": prompt}])
    return llm.invoke([msg]).content


def chat(
    project_id: str,
    query: str,
    k: int = DEFAULT_K,
    max_distance: float = DEFAULT_MAX_DISTANCE,
) -> Tuple[str, list]:
    db = load_project_db(project_id)

    # 1) Multi-query generation (original + N variations)
    queries = _generate_query_variations(query, n=DEFAULT_NUM_QUERY_VARIATIONS)

    # 2) Retrieve per query
    per_query_k = max(DEFAULT_PER_QUERY_K, (k // max(1, len(queries))))
    all_results: List[List[tuple[Document, float]]] = []
    for q in queries:
        res = retrieve_with_scores(db, q, k=per_query_k)
        if res:
            all_results.append(res)

    if not all_results:
        return "I don't know based on the provided documents.", []

    # 3) Fuse with RRF + dedupe
    fused = _rrf_fuse(all_results, final_k=k)

    docs = [x["doc"] for x in fused]
    best_distances = [float(x["best_distance"]) for x in fused]
    best = min(best_distances) if best_distances else 1.0

    # 4) Evidence gate (if even the best doc is too far -> no evidence)
    if best > max_distance:
        sources = [
            {
                "score": float(x["best_distance"]),
                "rrf_score": float(x["rrf_score"]),
                "hits": int(x["hits"]),
                "preview": _doc_raw_text(x["doc"], limit=160).replace("\n", " "),
            }
            for x in fused
        ]
        return "I don't know based on the provided documents.", sources

    # 5) Final answer (use fused top-k docs)
    answer = generate_final_answer(docs, query)

    sources = [
        {
            "score": float(x["best_distance"]),
            "rrf_score": float(x["rrf_score"]),
            "hits": int(x["hits"]),
            "preview": _doc_raw_text(x["doc"], limit=160).replace("\n", " "),
        }
        for x in fused
    ]
    return answer, sources