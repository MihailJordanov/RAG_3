import os, uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue
from app.core.config import settings
from app.db.session import get_db
from app.db.models import Job
from app.services.storage import ensure_dirs, project_upload_dir
from app.workers.tasks import ingest_pdf_task

router = APIRouter(prefix="/projects", tags=["ingest"])

redis_conn = Redis.from_url(settings.redis_url)
queue = Queue("default", connection=redis_conn)

@router.post("/{project_id}/ingest/file")
async def ingest_file(project_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    ensure_dirs()

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "For now this endpoint supports PDF only (easy to extend later).")

    job_id = str(uuid.uuid4())
    job = Job(id=job_id, project_id=project_id, type="ingest", status="queued", progress=0)
    db.add(job)
    db.commit()

    upload_dir = project_upload_dir(project_id)
    saved_path = os.path.join(upload_dir, file.filename)
    with open(saved_path, "wb") as f:
        f.write(await file.read())

    rq_job = queue.enqueue(ingest_pdf_task, project_id, saved_path, job_id, job_id=job_id)

    return {"job_id": rq_job.id, "status": "queued", "file": file.filename}


@router.get("/{project_id}/sources")
def list_project_sources(project_id: str):
    ensure_dirs()

    upload_dir = project_upload_dir(project_id)

    if not os.path.exists(upload_dir):
        return []

    files = []
    for name in os.listdir(upload_dir):
        full_path = os.path.join(upload_dir, name)
        if os.path.isfile(full_path):
            files.append(
                {
                    "name": name,
                    "status": "Uploaded",
                }
            )

    files.sort(key=lambda x: x["name"].lower())
    return files