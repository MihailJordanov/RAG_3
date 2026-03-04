from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from app.api.projects import router as projects_router
from app.api.ingest import router as ingest_router
from app.api.chat import router as chat_router
from app.api.jobs import router as jobs_router

app = FastAPI(title="RAG Chat")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.include_router(projects_router)
app.include_router(ingest_router)
app.include_router(chat_router)
app.include_router(jobs_router)

# uvicorn app.main:app --reload
# python -m app.workers.rq_worker 