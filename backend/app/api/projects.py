import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Project, Message, Job, User
from app.services.storage import delete_project_storage
from app.core.deps import get_current_user
from app.schemas.projects import CreateProjectRequest, ProjectResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
def create_project(
    payload: CreateProjectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_id = str(uuid.uuid4())
    name = (payload.name or "Untitled").strip() or "Untitled"

    p = Project(
        id=project_id,
        user_id=current_user.id,
        name=name,
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    return ProjectResponse(
        id=p.id,
        name=p.name,
        created_at=p.created_at,
    )


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )

    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            created_at=p.created_at,
        )
        for p in projects
    ]


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.query(Message).filter(Message.project_id == project_id).delete()
    db.query(Job).filter(
        Job.project_id == project_id,
        Job.user_id == current_user.id,
    ).delete()

    db.delete(project)
    db.commit()

    delete_project_storage(current_user.id, project_id)

    return {"status": "deleted"}