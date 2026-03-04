from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Message
from app.services.rag_chat import chat as rag_chat

router = APIRouter(prefix="/projects", tags=["chat"])


@router.post("/{project_id}/chat")
def chat(project_id: str, payload: dict, db: Session = Depends(get_db)):
    q = payload.get("message", "").strip()
    if not q:
        return {"answer": "Please enter a message.", "sources": []}

    db.add(Message(project_id=project_id, role="user", content=q))
    db.commit()

    answer, sources = rag_chat(project_id, q)

    db.add(Message(project_id=project_id, role="assistant", content=answer))
    db.commit()

    return {"answer": answer, "sources": sources}


@router.get("/{project_id}/messages")
def list_messages(project_id: str, db: Session = Depends(get_db)):
    msgs = (
        db.query(Message)
        .filter(Message.project_id == project_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )
    return [
        {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at}
        for m in msgs
    ]