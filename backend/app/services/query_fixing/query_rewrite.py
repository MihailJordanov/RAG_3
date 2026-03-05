from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.core.config import settings

_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=settings.openai_api_key)

def llm_spell_fix_bg(q: str) -> str:
    prompt = f"""
You are a spelling corrector for Bulgarian user questions.
Correct typos and wrong letters ONLY.
Do NOT change the meaning, do NOT paraphrase, do NOT add words.
Return ONLY the corrected question, nothing else.

Question: {q}
"""
    resp = _llm.invoke([HumanMessage(content=prompt)]).content.strip()
    # safety: ако LLM върне празно или прекалено различно, върни оригинала
    return resp if resp else q