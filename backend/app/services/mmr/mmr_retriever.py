from __future__ import annotations

from typing import List, Tuple, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.services.mmr.math import cosine_sim


def retrieve_with_scores_mmr(
    db: Chroma,
    query: str,
    k: int,
    *,
    fetch_k: int = 20,
    lambda_mult: float = 0.5,
    embedding_model: Optional[OpenAIEmbeddings] = None,
) -> List[Tuple[Document, float]]:
    """
    Maximum Marginal Relevance (MMR) върху кандидати от similarity_search_with_score.

    Pipeline:
      1) Взима fetch_k кандидати по similarity (cosine distance; lower=better)
      2) Прави MMR greedy selection до k документа (баланс relevance/diversity)
      3) Връща (Document, distance) като distance е оригиналният distance от Chroma,
         за да работи evidence gate-а ти.
    """
    if k <= 0:
        return []

    fetch_k = max(fetch_k, k)

    candidates = db.similarity_search_with_score(query, k=fetch_k) or []
    if not candidates:
        return []

    if embedding_model is None:
        # NOTE: по-добре е embedding_model да се подаде отвън (за да не се инстанцира постоянно)
        embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

    q_emb = embedding_model.embed_query(query)

    docs = [d for (d, _) in candidates]
    doc_texts = [(d.page_content or "") for d in docs]
    doc_embs = embedding_model.embed_documents(doc_texts)

    # relevance = cos_sim(query, doc)
    rel = [cosine_sim(q_emb, e) for e in doc_embs]

    selected: List[int] = []
    remaining = set(range(len(docs)))

    # старт: най-релевантния
    first = max(remaining, key=lambda i: rel[i])
    selected.append(first)
    remaining.remove(first)

    while remaining and len(selected) < k:
        def mmr_score(i: int) -> float:
            # diversity penalty = max cos_sim(doc_i, doc_selected)
            max_sim_to_selected = 0.0
            ei = doc_embs[i]
            for j in selected:
                s = cosine_sim(ei, doc_embs[j])
                if s > max_sim_to_selected:
                    max_sim_to_selected = s
            return lambda_mult * rel[i] - (1.0 - lambda_mult) * max_sim_to_selected

        nxt = max(remaining, key=mmr_score)
        selected.append(nxt)
        remaining.remove(nxt)

    out: List[Tuple[Document, float]] = []
    for i in selected:
        out.append((docs[i], float(candidates[i][1])))
    return out