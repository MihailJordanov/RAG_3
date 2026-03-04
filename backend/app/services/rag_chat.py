import json
from typing import Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import settings
from app.services.storage import project_chroma_dir


DEFAULT_K = 6
# Cosine distance in Chroma often behaves in ~[0..1], lower is better.
DEFAULT_MAX_DISTANCE = 0.70


def load_project_db(project_id: str) -> Chroma:
    persist_dir = project_chroma_dir(project_id)
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

        # Optional: include tables if present
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
    results = retrieve_with_scores(db, query, k=k)

    if not results:
        return "I don't know based on the provided documents.", []

    docs = [doc for doc, _ in results]
    distances = [float(score) for _, score in results]  # lower is better
    best = min(distances)

    # If everything is too far, treat as “no evidence”
    if best > max_distance:
        return "I don't know based on the provided documents.", [{"score": s} for s in distances]

    answer = generate_final_answer(docs, query)

    sources = [
        {"score": s, "preview": _doc_raw_text(d, limit=160).replace("\n", " ")}
        for (d, s) in zip(docs, distances)
    ]
    return answer, sources