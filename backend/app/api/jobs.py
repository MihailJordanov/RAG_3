from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Job, User
from app.core.deps import get_current_user
from app.schemas.jobs import JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    j = (
        db.query(Job)
        .filter(Job.id == job_id, Job.user_id == current_user.id)
        .first()
    )

    if not j:
        return JobResponse(
            id=job_id,
            project_id="",
            status="not_found",
            progress=0,
            message=None,
            error=None,
        )

    return JobResponse(
        id=j.id,
        project_id=j.project_id,
        status=j.status,
        progress=j.progress,
        message=j.message,
        error=j.error,
    )