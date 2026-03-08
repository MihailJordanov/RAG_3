from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Message, User
from app.services.rag_chat import chat as rag_chat
from app.core.deps import get_current_user, get_user_project
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse

router = APIRouter(prefix="/projects", tags=["chat"])


@router.post("/{project_id}/chat", response_model=ChatResponse)
def chat(
    project_id: str,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_user_project(project_id, current_user, db)

    q = payload.message.strip()
    if not q:
        return ChatResponse(answer="Please enter a message.", sources=[])

    db.add(Message(project_id=project_id, role="user", content=q))
    db.commit()

    answer, sources = rag_chat(current_user.id, project_id, q)

    db.add(Message(project_id=project_id, role="assistant", content=answer))
    db.commit()

    return ChatResponse(answer=answer, sources=sources)


@router.get("/{project_id}/messages", response_model=list[MessageResponse])
def list_messages(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_user_project(project_id, current_user, db)

    msgs = (
        db.query(Message)
        .filter(Message.project_id == project_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )

    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
        )
        for m in msgs
    ]