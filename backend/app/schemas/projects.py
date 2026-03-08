from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CreateProjectRequest(BaseModel):
    name: str | None = "Untitled"


class ProjectResponse(BaseModel):
    id: str
    name: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)