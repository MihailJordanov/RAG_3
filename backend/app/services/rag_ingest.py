import json
import os
import hashlib
from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from unstructured.chunking.title import chunk_by_title
from unstructured.partition.pdf import partition_pdf

from app.services.bm25.bm25_index import build_bm25_index, save_bm25
from app.core.config import settings
from app.services.storage import project_chroma_dir


POPPLER_BIN = r"C:\Users\User\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"

TITLE_MAX_CHARS = 3000
TITLE_NEW_AFTER = 2400
TITLE_COMBINE_UNDER = 500

FALLBACK_CHUNK_SIZE = 1500
FALLBACK_OVERLAP = 200


def _ensure_poppler() -> None:
    pdfinfo_exe = os.path.join(POPPLER_BIN, "pdfinfo.exe")
    pdftoppm_exe = os.path.join(POPPLER_BIN, "pdftoppm.exe")
    if not (os.path.exists(pdfinfo_exe) and os.path.exists(pdftoppm_exe)):
        raise RuntimeError(
            "Poppler not found.\n"
            f"Expected:\n{pdfinfo_exe}\n{pdftoppm_exe}\n"
            "Fix POPPLER_BIN to point to the folder containing pdfinfo.exe and pdftoppm.exe."
        )


def _partition_pdf(file_path: str, strategy: str):
    return partition_pdf(
        filename=file_path,
        strategy=strategy,
        infer_table_structure=True,
        extract_image_block_types=["Image"],
        extract_image_block_to_payload=True,
        pdf2image_poppler_path=POPPLER_BIN,
    )


def partition_document(file_path: str):
    _ensure_poppler()

    print(">>> partition_document: trying FAST")
    elements = _partition_pdf(file_path, "fast")
    fast_text_elems = sum(bool(getattr(e, "text", "").strip()) for e in elements)
    print(">>> FAST elements:", len(elements), "text_elems:", fast_text_elems)

    if not elements or fast_text_elems == 0:
        print(">>> partition_document: FAST empty -> trying HI_RES")
        elements = _partition_pdf(file_path, "hi_res")
        hi_text_elems = sum(bool(getattr(e, "text", "").strip()) for e in elements)
        print(">>> HI_RES elements:", len(elements), "text_elems:", hi_text_elems)

    return elements


def _elements_to_text(elements) -> str:
    parts: list[str] = []
    for el in elements:
        t = getattr(el, "text", None)
        if t and t.strip():
            parts.append(t.strip())
    return "\n\n".join(parts)


def _fallback_chunk_text(text: str) -> list[str]:
    if not text.strip():
        return []
    chunks: list[str] = []
    i = 0
    while i < len(text):
        chunks.append(text[i : i + FALLBACK_CHUNK_SIZE])
        i += max(1, FALLBACK_CHUNK_SIZE - FALLBACK_OVERLAP)
    return chunks


def create_chunks_by_title(elements):
    return chunk_by_title(
        elements,
        max_characters=TITLE_MAX_CHARS,
        new_after_n_chars=TITLE_NEW_AFTER,
        combine_text_under_n_chars=TITLE_COMBINE_UNDER,
    )


def separate_content_types(chunk):
    content_data = {"text": chunk.text, "tables": [], "images": []}

    if hasattr(chunk, "metadata") and hasattr(chunk.metadata, "orig_elements"):
        for element in chunk.metadata.orig_elements:
            element_type = type(element).__name__

            if element_type == "Table":
                table_html = getattr(element.metadata, "text_as_html", element.text)
                content_data["tables"].append(table_html)

            elif element_type == "Image":
                if hasattr(element, "metadata") and hasattr(element.metadata, "image_base64"):
                    content_data["images"].append(element.metadata.image_base64)

    return content_data


def create_ai_enhanced_summary(text: str, tables: List[str], images: List[str]) -> str:
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.openai_api_key)

    prompt_text = f"""You are creating a searchable description for document content retrieval.

TEXT CONTENT:
{text}
"""
    if tables:
        prompt_text += "TABLES:\n"
        for i, t in enumerate(tables):
            prompt_text += f"Table {i+1}:\n{t}\n\n"

    prompt_text += """
YOUR TASK:
Generate a comprehensive, searchable description that covers:
1. Key facts, numbers, and data points from text and tables
2. Main topics and concepts discussed
3. Questions this content could answer
4. Visual content analysis (charts, diagrams, patterns in images)
5. Alternative search terms users might use

SEARCHABLE DESCRIPTION:
"""

    message_content = [{"type": "text", "text": prompt_text}]
    for image_base64 in images:
        message_content.append(
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        )

    response = llm.invoke([HumanMessage(content=message_content)])
    return response.content


def _make_chunk_id(project_id: str, idx: int, raw_text: str) -> str:
    h = hashlib.sha256()
    h.update(project_id.encode("utf-8", errors="ignore"))
    h.update(str(idx).encode("utf-8"))
    h.update((raw_text or "").encode("utf-8", errors="ignore"))
    return h.hexdigest()


def summarise_chunks(project_id: str, chunks) -> list[Document]:
    docs: list[Document] = []

    for idx, chunk in enumerate(chunks):
        content = separate_content_types(chunk)

        if content["tables"] or content["images"]:
            enhanced = create_ai_enhanced_summary(content["text"], content["tables"], content["images"])
        else:
            enhanced = content["text"]

        chunk_id = _make_chunk_id(project_id, idx, content["text"])

        docs.append(
            Document(
                page_content=enhanced,
                metadata={
                    "chunk_id": chunk_id,
                    "chunk_index": idx,
                    "original_content": json.dumps(
                        {
                            "raw_text": content["text"],
                            "tables_html": content["tables"],
                            "images_base64": content["images"],
                        }
                    ),
                },
            )
        )

    return docs


def create_vector_store(documents: list[Document], persist_directory: str) -> Chroma:
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.openai_api_key)
    return Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=persist_directory,
        collection_metadata={"hnsw:space": "cosine"},
    )


def ingest_pdf_to_project(project_id: str, pdf_path: str) -> dict:
    elements = partition_document(pdf_path)
    raw_text = _elements_to_text(elements)

    chunks = create_chunks_by_title(elements)
    docs: list[Document] = summarise_chunks(project_id, chunks) if chunks else []

    if not docs:
        text_chunks = _fallback_chunk_text(raw_text)
        if not text_chunks:
            raise RuntimeError(
                "No text could be extracted from the PDF (even after hi_res fallback). "
                "The PDF may be images-only or OCR failed."
            )

        fallback_docs: list[Document] = []
        for idx, t in enumerate(text_chunks):
            chunk_id = _make_chunk_id(project_id, idx, t)
            fallback_docs.append(
                Document(
                    page_content=t,
                    metadata={"chunk_id": chunk_id, "chunk_index": idx},
                )
            )
        docs = fallback_docs

    persist_dir = project_chroma_dir(project_id)
    _ = create_vector_store(docs, persist_directory=persist_dir)

    bm25_index = build_bm25_index(docs)
    bm25_path = save_bm25(bm25_index, persist_dir=persist_dir)

    return {"persist_dir": persist_dir, "chunks": len(docs)}