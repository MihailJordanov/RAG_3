from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Job
from app.services.rag_ingest import ingest_pdf_to_project

def _set_job_status(db: Session, job_id: str, status: str, progress: int | None = None, error: str | None = None):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return
    job.status = status
    if progress is not None:
        job.progress = progress
    job.error = error
    db.commit()

def ingest_pdf_task(project_id: str, pdf_path: str, job_id: str):
    db = SessionLocal()
    try:
        _set_job_status(db, job_id, "running", progress=5)

        result = ingest_pdf_to_project(project_id, pdf_path)

        _set_job_status(db, job_id, "succeeded", progress=100)
        return result

    except Exception as e:
        _set_job_status(db, job_id, "failed", progress=0, error=str(e))
        raise
    finally:
        db.close()