import json
import os
from typing import List

from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage
from app.core.config import settings
from app.services.storage import project_chroma_dir

# 1) Ясен poppler bin път (папката, в която са pdfinfo.exe и pdftoppm.exe)
POPPLER_BIN = r"C:\Users\User\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"

def partition_document(file_path: str):
    # guard за poppler
    pdfinfo_exe = os.path.join(POPPLER_BIN, "pdfinfo.exe")
    pdftoppm_exe = os.path.join(POPPLER_BIN, "pdftoppm.exe")
    if not (os.path.exists(pdfinfo_exe) and os.path.exists(pdftoppm_exe)):
        raise RuntimeError(
            f"Poppler not found. Expected:\n{pdfinfo_exe}\n{pdftoppm_exe}\n"
            "Fix POPPLER_BIN to point to the folder containing pdfinfo.exe and pdftoppm.exe."
        )

    def _extract(strategy: str):
        return partition_pdf(
            filename=file_path,
            strategy=strategy,
            infer_table_structure=True,
            extract_image_block_types=["Image"],
            extract_image_block_to_payload=True,
            pdf2image_poppler_path=POPPLER_BIN,
        )

    print(">>> partition_document: trying FAST")
    elements = _extract("fast")
    fast_text_elems = sum(bool(getattr(e, "text", "").strip()) for e in elements)
    print(">>> FAST elements:", len(elements), "text_elems:", fast_text_elems)

    if not elements or fast_text_elems == 0:
        print(">>> partition_document: FAST empty -> trying HI_RES")
        elements = _extract("hi_res")
        hi_text_elems = sum(bool(getattr(e, "text", "").strip()) for e in elements)
        print(">>> HI_RES elements:", len(elements), "text_elems:", hi_text_elems)

    return elements


def create_chunks_by_title(elements):
    return chunk_by_title(
        elements,
        max_characters=3000,
        new_after_n_chars=2400,
        combine_text_under_n_chars=500,
    )

def separate_content_types(chunk):
    content_data = {"text": chunk.text, "tables": [], "images": [], "types": ["text"]}
    if hasattr(chunk, "metadata") and hasattr(chunk.metadata, "orig_elements"):
        for element in chunk.metadata.orig_elements:
            element_type = type(element).__name__
            if element_type == "Table":
                content_data["types"].append("table")
                table_html = getattr(element.metadata, "text_as_html", element.text)
                content_data["tables"].append(table_html)
            elif element_type == "Image":
                if hasattr(element, "metadata") and hasattr(element.metadata, "image_base64"):
                    content_data["types"].append("image")
                    content_data["images"].append(element.metadata.image_base64)
    content_data["types"] = list(set(content_data["types"]))
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
        message_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
        })

    response = llm.invoke([HumanMessage(content=message_content)])
    return response.content

def summarise_chunks(chunks):
    docs = []
    for chunk in chunks:
        content_data = separate_content_types(chunk)
        if content_data["tables"] or content_data["images"]:
            enhanced = create_ai_enhanced_summary(content_data["text"], content_data["tables"], content_data["images"])
        else:
            enhanced = content_data["text"]

        docs.append(Document(
            page_content=enhanced,
            metadata={
                "original_content": json.dumps({
                    "raw_text": content_data["text"],
                    "tables_html": content_data["tables"],
                    "images_base64": content_data["images"],
                })
            }
        ))
    return docs

def create_vector_store(documents, persist_directory: str):
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.openai_api_key)
    return Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=persist_directory,
        collection_metadata={"hnsw:space": "cosine"},
    )


def ingest_pdf_to_project(project_id: str, pdf_path: str):
    elements = partition_document(pdf_path)

    # Събирай plain text от елементи
    raw_text = "\n\n".join(
        [e.text.strip() for e in elements if getattr(e, "text", None) and e.text.strip()]
    )

    # 1) Опитай chunk_by_title
    chunks = create_chunks_by_title(elements)

    # 2) Ако chunk_by_title не даде нищо, fallback към текстови chunks
    docs = []
    if chunks:
        docs = summarise_chunks(chunks)

    if not docs:
        # fallback: режи raw_text на части
        if not raw_text.strip():
            raise RuntimeError(
                "No text could be extracted from the PDF even after hi_res fallback. "
                "This PDF may be images-only or OCR failed."
            )

        chunk_size = 1500
        overlap = 200
        i = 0
        while i < len(raw_text):
            docs.append(Document(page_content=raw_text[i:i+chunk_size], metadata={}))
            i += max(1, chunk_size - overlap)

    persist_dir = project_chroma_dir(project_id)
    db = create_vector_store(docs, persist_directory=persist_dir)
    return {"persist_dir": persist_dir, "chunks": len(docs)}



def elements_to_text(elements) -> str:
    parts = []
    for el in elements:
        t = getattr(el, "text", None)
        if t and t.strip():
            parts.append(t.strip())
    return "\n\n".join(parts)

def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
    if not text.strip():
        return []
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        chunks.append(text[i:i+chunk_size])
        i += max(1, chunk_size - overlap)
    return chunks


