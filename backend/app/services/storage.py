import os
import shutil

from app.core.config import settings


def ensure_dirs():
    os.makedirs(settings.data_dir, exist_ok=True)
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.chroma_dir, exist_ok=True)


def user_upload_dir(user_id: str) -> str:
    path = os.path.join(settings.upload_dir, user_id)
    os.makedirs(path, exist_ok=True)
    return path


def user_chroma_dir(user_id: str) -> str:
    path = os.path.join(settings.chroma_dir, user_id)
    os.makedirs(path, exist_ok=True)
    return path


def project_upload_dir(user_id: str, project_id: str) -> str:
    path = os.path.join(user_upload_dir(user_id), project_id)
    os.makedirs(path, exist_ok=True)
    return path


def project_chroma_dir(user_id: str, project_id: str) -> str:
    path = os.path.join(user_chroma_dir(user_id), project_id)
    os.makedirs(path, exist_ok=True)
    return path


def delete_project_uploads(user_id: str, project_id: str) -> None:
    path = os.path.join(settings.upload_dir, user_id, project_id)
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)


def delete_project_chroma(user_id: str, project_id: str) -> None:
    path = os.path.join(settings.chroma_dir, user_id, project_id)
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)


def delete_project_storage(user_id: str, project_id: str) -> None:
    delete_project_uploads(user_id, project_id)
    delete_project_chroma(user_id, project_id)