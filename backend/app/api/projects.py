import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Project, Message, Job

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("")
def create_project(payload: dict, db: Session = Depends(get_db)):
    project_id = str(uuid.uuid4())
    name = payload.get("name", "Untitled")
    p = Project(id=project_id, name=name)
    db.add(p)
    db.commit()
    return {"id": project_id, "name": name}

@router.get("")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [{"id": p.id, "name": p.name, "created_at": p.created_at} for p in projects]


@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # delete related data
    db.query(Message).filter(Message.project_id == project_id).delete()
    db.query(Job).filter(Job.project_id == project_id).delete()

    db.delete(project)
    db.commit()

    return {"status": "deleted"}