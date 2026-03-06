from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    database_url: str
    redis_url: str

    cohere_api_key: str | None = None
    cohere_rerank_model: str = "rerank-v3.5"

    data_dir: str = "./data"
    chroma_dir: str = "./data/chroma"
    upload_dir: str = "./data/uploads"

    class Config:
        env_file = ".env"

settings = Settings()