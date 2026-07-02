from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    gemini_api_key: str
    chroma_persist_dir: str = "./backend/data/chroma"
    uploads_dir: str = "./backend/data/uploads"
    synthetic_data_dir: str = "./backend/data/synthetic"
    embedding_model: str = "all-MiniLM-L6-v2"
    chat_model: str = "gemini-2.5-flash"
    extraction_model: str = "gemini-2.5-flash"
    top_k_retrieval: int = 8
    chunk_size: int = 800
    chunk_overlap: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
