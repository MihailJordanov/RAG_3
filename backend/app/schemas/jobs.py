from pydantic import BaseModel


class JobResponse(BaseModel):
    id: str
    project_id: str
    status: str
    progress: int
    message: str | None = None
    error: str | None = None