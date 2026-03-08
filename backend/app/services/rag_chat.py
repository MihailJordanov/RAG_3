import json
import hashlib
from typing import Tuple, List, Dict, Any

from pydantic import BaseModel, Field

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.services.reranker.reranker import rerank_fused_results
from app.services.mmr import retrieve_with_scores_mmr
from app.services.bm25.bm25_index import load_bm25, bm25_search
from app.core.config import settings
from app.services.storage import project_chroma_dir


DEFAULT_K = 10
DEFAULT_MAX_DISTANCE = 0.85
DEFAULT_NUM_QUERY_VARIATIONS = 3
DEFAULT_PER_QUERY_K = 5
RRF_K = 60
DEFAULT_BM25_K = 8
VECTOR_WEIGHT = 0.75
BM25_WEIGHT = 0.25
DEFAULT_RERANK_TOP_N = 6

EMPTY_PROJECT_MESSAGE = "Your workspace is empty. Upload a document from the Tools ✦ panel."


class QueryVariations(BaseModel):
    queries: List[str] = Field(default_factory=list)


def load_project_db(user_id: str, project_id: str) -> Chroma:
    persist_dir = project_chroma_dir(user_id, project_id)
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.openai_api_key)
    return Chroma(persist_directory=persist_dir, embedding_function=embedding_model)


def retrieve_with_scores(db: Chroma, query: str, k: int):
    return db.similarity_search_with_score(query, k=k)


def _doc_raw_text(doc: Document, limit: int = 2000) -> str:
    if "original_content" in doc.metadata:
        original = json.loads(doc.metadata["original_content"])
        raw = original.get("raw_text", "") or ""
        return raw[:limit]
    return (doc.page_content or "")[:limit]


def _doc_dedupe_key(doc: Document) -> str:
    chunk_id = doc.metadata.get("chunk_id")
    if chunk_id:
        return f"chunk:{chunk_id}"

    h = hashlib.sha256()
    h.update((doc.page_content or "").encode("utf-8", errors="ignore"))
    meta = {k: doc.metadata.get(k) for k in sorted(doc.metadata.keys()) if k != "original_content"}
    h.update(json.dumps(meta, sort_keys=True, ensure_ascii=False).encode("utf-8", errors="ignore"))
    return f"hash:{h.hexdigest()}"


def _generate_query_variations(query: str, n: int = DEFAULT_NUM_QUERY_VARIATIONS) -> List[str]:
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

    out = [query.strip()]
    for v in variations:
        if v.lower() != query.strip().lower() and v not in out:
            out.append(v)

    return out[: (1 + n)]


def _rrf_fuse_weighted(
    all_results: List[List[tuple[Document, float, str]]],
    final_k: int,
) -> List[Dict[str, Any]]:
    fused: Dict[str, Dict[str, Any]] = {}

    for result_list in all_results:
        for rank, (doc, s, source_type) in enumerate(result_list, start=1):
            key = _doc_dedupe_key(doc)
            entry = fused.get(key)
            if not entry:
                entry = {
                    "doc": doc,
                    "best_distance": 1.0,
                    "rrf_score": 0.0,
                    "hits": 0,
                    "bm25_hits": 0,
                    "vector_hits": 0,
                }
                fused[key] = entry

            weight = VECTOR_WEIGHT if source_type == "vector" else BM25_WEIGHT
            entry["rrf_score"] += weight * (1.0 / (RRF_K + rank))
            entry["hits"] += 1

            if source_type == "vector":
                entry["vector_hits"] += 1
                dist = float(s)
                if dist < entry["best_distance"]:
                    entry["best_distance"] = dist
            else:
                entry["bm25_hits"] += 1

    ranked = sorted(
        fused.values(),
        key=lambda x: (x["rrf_score"], x["bm25_hits"], x["vector_hits"]),
        reverse=True,
    )
    return ranked[:final_k]


def generate_final_answer(docs: list[Document], query: str) -> str:
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.openai_api_key)

    prompt = """
        You are answering questions using ONLY the provided documents.

        If the answer is clearly present in the documents:
        - provide a concise answer.

        If the documents do NOT contain the answer:
        - respond exactly with:
        "I don't know based on the provided documents."

        Do NOT include both an answer and the fallback sentence.

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
    user_id: str,
    project_id: str,
    query: str,
    k: int = DEFAULT_K,
    max_distance: float = DEFAULT_MAX_DISTANCE,
) -> Tuple[str, list]:
    db = load_project_db(user_id, project_id)

    if not project_has_documents(db):
        return EMPTY_PROJECT_MESSAGE, []

    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.openai_api_key)

    persist_dir = project_chroma_dir(user_id, project_id)
    bm25_index = load_bm25(persist_dir)

    queries = _generate_query_variations(query, n=DEFAULT_NUM_QUERY_VARIATIONS)

    per_query_k = max(DEFAULT_PER_QUERY_K, (k // max(1, len(queries))))
    all_results: List[List[tuple[Document, float, str]]] = []

    for q in queries:
        vec = retrieve_with_scores_mmr(
            db,
            q,
            k=per_query_k,
            fetch_k=max(20, per_query_k * 4),
            lambda_mult=0.5,
            embedding_model=embedding_model,
        ) or []
        if vec:
            all_results.append([(doc, float(dist), "vector") for (doc, dist) in vec])

        if bm25_index:
            bm25_hits = bm25_search(bm25_index, q, k=min(DEFAULT_BM25_K, per_query_k))
            if bm25_hits:
                chunk_ids = [cid for cid, _ in bm25_hits]
                bm_docs = _get_docs_by_chunk_ids(db, chunk_ids)

                if bm_docs:
                    by_id = {d.metadata.get("chunk_id"): d for d in bm_docs}
                    ranked_docs = [by_id[cid] for cid, _ in bm25_hits if cid in by_id]
                    all_results.append([(d, 0.0, "bm25") for d in ranked_docs])

    if not all_results:
        return "I don't know based on the provided documents.", []

    fused = _rrf_fuse_weighted(all_results, final_k=k)

    best_vector_distance = min([x["best_distance"] for x in fused if x["vector_hits"] > 0] or [1.0])
    has_bm25_evidence = any(x["bm25_hits"] > 0 for x in fused)

    if (best_vector_distance > max_distance) and (not has_bm25_evidence):
        sources = [
            {
                "score": float(x["best_distance"]),
                "rrf_score": float(x["rrf_score"]),
                "hits": int(x["hits"]),
                "vector_hits": int(x["vector_hits"]),
                "bm25_hits": int(x["bm25_hits"]),
                "rerank_score": None,
                "preview": _doc_raw_text(x["doc"], limit=160).replace("\n", " "),
            }
            for x in fused
        ]
        return "I don't know based on the provided documents.", sources

    reranked = rerank_fused_results(
        query=query,
        fused=fused,
        top_n=min(DEFAULT_RERANK_TOP_N, len(fused)),
    )

    docs = [x["doc"] for x in reranked]
    answer = generate_final_answer(docs, query)

    sources = [
        {
            "score": float(x["best_distance"]),
            "rrf_score": float(x["rrf_score"]),
            "hits": int(x["hits"]),
            "vector_hits": int(x["vector_hits"]),
            "bm25_hits": int(x["bm25_hits"]),
            "rerank_score": x.get("rerank_score"),
            "rerank_applied": bool(x.get("rerank_applied", False)),
            "preview": _doc_raw_text(x["doc"], limit=160).replace("\n", " "),
        }
        for x in reranked
    ]
    return answer, sources


def _get_docs_by_chunk_ids(db: Chroma, chunk_ids: list[str]) -> list[Document]:
    if not chunk_ids:
        return []

    try:
        res = db._collection.get(
            where={"chunk_id": {"$in": chunk_ids}},
            include=["documents", "metadatas"],
        )
        docs = []
        metas = res.get("metadatas") or []
        texts = res.get("documents") or []
        for t, m in zip(texts, metas):
            docs.append(Document(page_content=t or "", metadata=m or {}))

        by_id = {d.metadata.get("chunk_id"): d for d in docs if d.metadata.get("chunk_id")}
        return [by_id[cid] for cid in chunk_ids if cid in by_id]
    except Exception:
        pass

    try:
        res = db.get(where={"chunk_id": {"$in": chunk_ids}})
        docs = []
        for t, m in zip(res.get("documents", []), res.get("metadatas", [])):
            docs.append(Document(page_content=t or "", metadata=m or {}))
        by_id = {d.metadata.get("chunk_id"): d for d in docs if d.metadata.get("chunk_id")}
        return [by_id[cid] for cid in chunk_ids if cid in by_id]
    except Exception:
        return []


RAG_CONFIG = {
    "DEFAULT_K": DEFAULT_K,
    "DEFAULT_MAX_DISTANCE": DEFAULT_MAX_DISTANCE,
    "DEFAULT_NUM_QUERY_VARIATIONS": DEFAULT_NUM_QUERY_VARIATIONS,
    "DEFAULT_PER_QUERY_K": DEFAULT_PER_QUERY_K,
    "RRF_K": RRF_K,
    "DEFAULT_BM25_K": DEFAULT_BM25_K,
    "VECTOR_WEIGHT": VECTOR_WEIGHT,
    "BM25_WEIGHT": BM25_WEIGHT,
    "DEFAULT_RERANK_TOP_N": DEFAULT_RERANK_TOP_N,
}


def ask_question(
    user_id: str,
    project_id: str,
    question: str,
    k: int = DEFAULT_K,
    max_distance: float = DEFAULT_MAX_DISTANCE,
) -> Dict[str, Any]:
    answer, sources = chat(
        user_id=user_id,
        project_id=project_id,
        query=question,
        k=k,
        max_distance=max_distance,
    )

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "config": RAG_CONFIG,
    }


def project_has_documents(db: Chroma) -> bool:
    try:
        return (db._collection.count() or 0) > 0
    except Exception:
        pass

    try:
        res = db.get(limit=1)
        docs = res.get("documents", []) if res else []
        return len(docs) > 0
    except Exception:
        return False