from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # === App ===
    app_name: str = "Tech Digest KR"
    debug: bool = False
    
    # === RSS Feeds ===
    rss_fetch_interval_hours: int = 6
    
    # === LLM ===
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    summary_max_tokens: int = 300
    
    # === Embedding ===
    embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-V2"
    similarity_threshold: float = 0.75
    
    # === Storage ===
    db_path: str = str(BASE_DIR / "data" / "digest.db")
    
    # === API ===
    api_host: str = "0.0.0.0"
    api_port: int = 8009
    
    # === Tags ===
    default_interest_tags: list[str] = Field(
        default=[
            "python", "javascript", "fastapi", "react",
            "ai", "mlops", "devops", "backend", "frontend",
            "database", "cloud", "security"
        ]
    )
    
    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()