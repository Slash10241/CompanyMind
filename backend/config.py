from __future__ import annotations
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key_1: str
    gemini_api_key_2: str = ""
    gemini_api_key_3: str = ""
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

    @property
    def gemini_api_keys(self) -> list[str]:
        return [k for k in [self.gemini_api_key_1, self.gemini_api_key_2, self.gemini_api_key_3] if k]


settings = Settings()
