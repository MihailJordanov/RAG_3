import json
from typing import Tuple
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import HumanMessage
from app.services.storage import project_chroma_dir

def load_project_db(project_id: str) -> Chroma:
    persist_dir = project_chroma_dir(project_id)
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(persist_directory=persist_dir, embedding_function=embedding_model)

def retrieve_with_scores(db: Chroma, query: str, k: int = 4):
    # LangChain/Chroma дава similarity_search_with_score
    return db.similarity_search_with_score(query, k=k)

def generate_final_answer(chunks, query: str) -> str:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    prompt_text = f"""Answer the question using ONLY the provided documents.
If the documents do not contain enough information, say: "I don't know based on the provided documents."

Question: {query}

DOCUMENTS:
"""
    for i, chunk in enumerate(chunks):
        prompt_text += f"\n--- Doc {i+1} ---\n"
        if "original_content" in chunk.metadata:
            original = json.loads(chunk.metadata["original_content"])
            raw = original.get("raw_text", "")
            if raw:
                prompt_text += f"TEXT:\n{raw}\n\n"
            tables = original.get("tables_html", [])
            if tables:
                prompt_text += "TABLES:\n"
                for j, t in enumerate(tables):
                    prompt_text += f"Table {j+1}:\n{t}\n\n"
        else:
            prompt_text += chunk.page_content[:2000]

    message = HumanMessage(content=[{"type":"text","text":prompt_text}])
    response = llm.invoke([message])
    return response.content

def chat(project_id: str, query: str, k: int = 4, score_threshold: float = 0.35) -> Tuple[str, list]:
    db = load_project_db(project_id)
    results = retrieve_with_scores(db, query, k=k)

    if not results:
        return "I don't know based on the provided documents.", []

    # results: list[(Document, score)]  -> при Chroma score е distance (по-малко=по-добре) или similarity според impl.
    # Ще го направим устойчиво: ако score е distance, прагът е обратен.
    docs = []
    scores = []
    for doc, score in results:
        docs.append(doc)
        scores.append(score)

    # Хак за “не знам”: ако всички резултати са “лоши”
    # Ако score изглежда като distance (обикновено 0..2): ниско е добре.
    # Ако е similarity (0..1): високо е добре.
    max_score = max(scores)
    min_score = min(scores)

    looks_like_distance = max_score > 1.0  # груба евристика
    if looks_like_distance:
        # distance: ако най-добрият (min) е прекалено голям -> не знам
        if min_score > 0.9:
            return "I don't know based on the provided documents.", []
    else:
        # similarity: ако най-добрият (max) е под праг -> не знам
        if max_score < score_threshold:
            return "I don't know based on the provided documents.", []

    answer = generate_final_answer(docs, query)

    sources = [{"score": s} for s in scores]
    return answer, sources