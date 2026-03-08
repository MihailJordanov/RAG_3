from pydantic import BaseModel


class IngestFileResponse(BaseModel):
    job_id: str
    status: str
    file: str


class ProjectSourceResponse(BaseModel):
    name: str
    status: str
    size_bytes: int


class ProjectLimitsResponse(BaseModel):
    max_files_per_project: int
    max_file_size_mb: int
    max_total_project_size_mb: int
    max_file_size_bytes: int
    max_total_project_size_bytes: int
    current_file_count: int
    current_total_size_bytes: int
    remaining_file_slots: int
    remaining_total_size_bytes: int