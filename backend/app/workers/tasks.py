# --- MUST be first: disable unstructured NLTK auto-download (403 workaround) ---
import unstructured.nlp.tokenize as utok

def _no_download() -> None:
    return None

utok.download_nltk_packages = _no_download
utok._download_nltk_packages_if_not_present = _no_download
# ------------------------------------------------------------------------------

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Job
from app.services.rag_ingest import ingest_pdf_to_project


def _set_job_status(
    db: Session,
    job_id: str,
    status: str,
    progress: int | None = None,
    error: str | None = None,
    message: str | None = None,
) -> None:
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return
    job.status = status
    if progress is not None:
        job.progress = progress
    job.error = error
    if message is not None:
        job.message = message
    db.commit()


def ingest_pdf_task(user_id: str, project_id: str, pdf_path: str, job_id: str) -> dict:
    db = SessionLocal()
    try:
        _set_job_status(db, job_id, "running", progress=5, message="Queued for processing...")

        def progress_cb(progress: int, message: str) -> None:
            _set_job_status(db, job_id, "running", progress=progress, message=message)

        result = ingest_pdf_to_project(user_id, project_id, pdf_path, progress_cb=progress_cb)

        _set_job_status(
            db,
            job_id,
            "succeeded",
            progress=100,
            message="File uploaded and indexed successfully.",
        )
        return result
    except Exception as e:
        _set_job_status(
            db,
            job_id,
            "failed",
            progress=0,
            error=str(e),
            message="Document processing failed.",
        )
        raise
    finally:
        db.close()