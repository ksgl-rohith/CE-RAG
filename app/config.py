from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    APP_ENV: str = "development"
    APP_NAME: str = "Adaptive Medical RAG"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    GRADIO_PORT: int = 7860
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg://medical_rag:medical_rag@localhost:5432/medical_rag"
    
    # Embedding
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # LLM
    LLM_PROVIDER: str = "google"
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_API_KEY: Optional[str] = None
    LLM_TEMPERATURE: float = 0.0
    
    # RAG Settings
    DENSE_TOP_K: int = 30
    SPARSE_TOP_K: int = 30
    RERANK_TOP_K: int = 12
    MAX_RETRIEVAL_ITERATIONS: int = 3
    MIN_EVIDENCE_AUTHORITY_SCORE: float = 0.80
    MIN_CITATION_SUPPORT_SCORE: float = 0.85
    
    # Source APIs
    PUBMED_API_KEY: Optional[str] = None
    PUBMED_TOOL_NAME: str = "adaptive-medical-rag"
    PUBMED_CONTACT_EMAIL: Optional[str] = None
    
    # Safety and Audit
    ENABLE_AUDIT_LOGS: bool = True
    ENABLE_QUERY_STORAGE: bool = False
    DEIDENTIFY_INPUT: bool = True

settings = Settings()
