import os
from app.core.config import settings

def ensure_dirs():
    os.makedirs(settings.data_dir, exist_ok=True)
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.chroma_dir, exist_ok=True)

def project_upload_dir(project_id: str) -> str:
    p = os.path.join(settings.upload_dir, project_id)
    os.makedirs(p, exist_ok=True)
    return p

def project_chroma_dir(project_id: str) -> str:
    p = os.path.join(settings.chroma_dir, project_id)
    os.makedirs(p, exist_ok=True)
    return p