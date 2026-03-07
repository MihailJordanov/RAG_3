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

MAX_FILES_PER_PROJECT = 2
MAX_FILE_SIZE_MB = 2
MAX_TOTAL_PROJECT_SIZE_MB = 25

MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_TOTAL_PROJECT_SIZE_BYTES = MAX_TOTAL_PROJECT_SIZE_MB * 1024 * 1024


@router.post("/{project_id}/ingest/file")
async def ingest_file(project_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    ensure_dirs()

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            400,
            "Only PDF files are supported."
        )

    upload_dir = project_upload_dir(project_id)

    existing_files = [
        name for name in os.listdir(upload_dir)
        if os.path.isfile(os.path.join(upload_dir, name))
    ]

    if len(existing_files) >= MAX_FILES_PER_PROJECT:
        raise HTTPException(
            400,
            f"Project file limit reached. Maximum allowed is {MAX_FILES_PER_PROJECT} files."
        )

    if file.filename in existing_files:
        raise HTTPException(
            400,
            f'A file named "{file.filename}" already exists in this project.'
        )

    file_bytes = await file.read()
    file_size = len(file_bytes)

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            400,
            f'File "{file.filename}" is too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB per file.'
        )

    current_total_size = sum(
        os.path.getsize(os.path.join(upload_dir, name))
        for name in existing_files
    )

    if current_total_size + file_size > MAX_TOTAL_PROJECT_SIZE_BYTES:
        raise HTTPException(
            400,
            f'Project storage limit exceeded. Maximum allowed total size is {MAX_TOTAL_PROJECT_SIZE_MB} MB.'
        )

    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        project_id=project_id,
        type="ingest",
        status="queued",
        progress=0,
        message="Queued for upload...",
    )
    db.add(job)
    db.commit()

    saved_path = os.path.join(upload_dir, file.filename)
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

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
                    "size_bytes": os.path.getsize(full_path),
                }
            )

    files.sort(key=lambda x: x["name"].lower())
    return files


@router.get("/{project_id}/limits")
def get_project_limits(project_id: str):
    ensure_dirs()
    upload_dir = project_upload_dir(project_id)

    existing_files = [
        name for name in os.listdir(upload_dir)
        if os.path.isfile(os.path.join(upload_dir, name))
    ]

    current_total_size = sum(
        os.path.getsize(os.path.join(upload_dir, name))
        for name in existing_files
    )

    return {
        "max_files_per_project": MAX_FILES_PER_PROJECT,
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "max_total_project_size_mb": MAX_TOTAL_PROJECT_SIZE_MB,
        "max_file_size_bytes": MAX_FILE_SIZE_BYTES,
        "max_total_project_size_bytes": MAX_TOTAL_PROJECT_SIZE_BYTES,
        "current_file_count": len(existing_files),
        "current_total_size_bytes": current_total_size,
        "remaining_file_slots": max(MAX_FILES_PER_PROJECT - len(existing_files), 0),
        "remaining_total_size_bytes": max(MAX_TOTAL_PROJECT_SIZE_BYTES - current_total_size, 0),
    }