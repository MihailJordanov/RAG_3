import os
import pickle
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

from langchain_core.documents import Document

try:
    from rank_bm25 import BM25Okapi
except ImportError as e:
    raise RuntimeError(
        "Missing dependency 'rank_bm25'. Install with: pip install rank_bm25"
    ) from e


_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-я0-9]+", re.UNICODE)


def _tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall((text or "").lower())


@dataclass
class BM25Index:
    chunk_ids: List[str]
    tokenized_corpus: List[List[str]]
    # optional cacheable raw texts / metadata
    # (we actually only need chunk_id -> fetch doc from Chroma)
    bm25: Any  # BM25Okapi


def build_bm25_index(docs: List[Document]) -> BM25Index:
    chunk_ids: List[str] = []
    corpus_tokens: List[List[str]] = []

    for d in docs:
        cid = d.metadata.get("chunk_id")
        if not cid:
            continue

        # За keyword search най-добре работи RAW текстът, ако го имаш.
        # Ако няма original_content, падаме на page_content.
        raw = None
        if "original_content" in d.metadata:
            # metadata["original_content"] е JSON string
            # но тук не парсваме тежко; при ingest го имаш 100%
            pass

        # В ingest ти вече държиш "enhanced" в page_content и RAW в original_content.
        # По-лесно: BM25 върху page_content (enhanced), но ако искаш RAW – виж ingest patch-а по-долу.
        text_for_bm25 = d.page_content or ""
        tokens = _tokenize(text_for_bm25)

        chunk_ids.append(cid)
        corpus_tokens.append(tokens)

    bm25 = BM25Okapi(corpus_tokens) if corpus_tokens else BM25Okapi([["empty"]])
    return BM25Index(chunk_ids=chunk_ids, tokenized_corpus=corpus_tokens, bm25=bm25)


def save_bm25(index: BM25Index, persist_dir: str, filename: str = "bm25.pkl") -> str:
    path = os.path.join(persist_dir, filename)
    with open(path, "wb") as f:
        pickle.dump(
            {"chunk_ids": index.chunk_ids, "tokenized_corpus": index.tokenized_corpus},
            f,
        )
    return path


def load_bm25(persist_dir: str, filename: str = "bm25.pkl") -> BM25Index | None:
    path = os.path.join(persist_dir, filename)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        payload = pickle.load(f)

    chunk_ids = payload["chunk_ids"]
    tokenized_corpus = payload["tokenized_corpus"]
    bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else BM25Okapi([["empty"]])

    return BM25Index(chunk_ids=chunk_ids, tokenized_corpus=tokenized_corpus, bm25=bm25)


def bm25_search(index: BM25Index, query: str, k: int = 10) -> List[Tuple[str, float]]:
    """
    Return list of (chunk_id, bm25_score), sorted desc.
    """
    if not index or not index.chunk_ids:
        return []

    q_tokens = _tokenize(query)
    if not q_tokens:
        return []

    scores = index.bm25.get_scores(q_tokens)  # array-like
    scored = list(zip(index.chunk_ids, scores))
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:k]

    # махаме нулеви резултати (важно за gating)
    return [(cid, float(s)) for cid, s in top if float(s) > 0.0]