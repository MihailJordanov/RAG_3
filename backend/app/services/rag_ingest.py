import json
import os
from typing import List

from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage

from app.services.storage import project_chroma_dir

# 1) Ясен poppler bin път (папката, в която са pdfinfo.exe и pdftoppm.exe)
POPPLER_BIN = r"C:\Users\User\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"

def partition_document(file_path: str):
    # (по желание) guard: да не гърми с неясна грешка
    pdfinfo_exe = os.path.join(POPPLER_BIN, "pdfinfo.exe")
    pdftoppm_exe = os.path.join(POPPLER_BIN, "pdftoppm.exe")
    if not (os.path.exists(pdfinfo_exe) and os.path.exists(pdftoppm_exe)):
        raise RuntimeError(
            f"Poppler not found. Expected:\n{pdfinfo_exe}\n{pdftoppm_exe}\n"
            "Fix POPPLER_BIN to point to the folder containing pdfinfo.exe and pdftoppm.exe."
        )

    # 2) Най-важното: подай poppler пътя към pdf2image през unstructured
    try:
        elements = partition_pdf(
            filename=file_path,
            strategy="hi_res",
            infer_table_structure=True,
            extract_image_block_types=["Image"],
            extract_image_block_to_payload=True,
            pdf2image_poppler_path=POPPLER_BIN,  # <-- FIX за Windows
        )
        return elements
    except TypeError as e:
        # Ако твоята версия на unstructured не приема този keyword,
        # ще падне тук. В такъв случай ми пейстни `pip show unstructured`
        # и ще ти дам точния keyword.
        raise

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
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
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
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=persist_directory,
        collection_metadata={"hnsw:space": "cosine"},
    )

def ingest_pdf_to_project(project_id: str, pdf_path: str):
    elements = partition_document(pdf_path)
    chunks = create_chunks_by_title(elements)
    docs = summarise_chunks(chunks)

    persist_dir = project_chroma_dir(project_id)
    db = create_vector_store(docs, persist_directory=persist_dir)
    return {"persist_dir": persist_dir, "chunks": len(docs)}