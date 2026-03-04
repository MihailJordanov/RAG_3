import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Project

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