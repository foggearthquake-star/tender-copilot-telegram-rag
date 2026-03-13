from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / '.env'


class Settings(BaseSettings):
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    storage_path: str = Field(default="execution/data/storage.json", alias="STORAGE_PATH")
    upload_dir: str = Field(default="execution/data/uploads", alias="UPLOAD_DIR")
    reports_dir: str = Field(default="execution/data/reports", alias="REPORTS_DIR")
    audit_log_path: str = Field(default="execution/data/pipeline_audit.jsonl", alias="AUDIT_LOG_PATH")
    database_url: str = Field(default="", alias="DATABASE_URL")
    redis_url: str = Field(default="", alias="REDIS_URL")
    enable_ocr: bool = Field(default=True, alias="ENABLE_OCR")
    tesseract_cmd: str = Field(default="", alias="TESSERACT_CMD")
    vector_backend: str = Field(default="local", alias="VECTOR_BACKEND")
    qdrant_url: str = Field(default="", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="tender_chunks", alias="QDRANT_COLLECTION")
    pinecone_api_key: str = Field(default="", alias="PINECONE_API_KEY")
    pinecone_index: str = Field(default="tender-chunks", alias="PINECONE_INDEX")
    llm_mode: str = Field(default="heuristic", alias="LLM_MODE")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://polza.ai/api/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="openai/gpt-4o-mini", alias="OPENAI_MODEL")

    model_config = SettingsConfigDict(env_file=str(ENV_PATH), env_file_encoding="utf-8-sig", populate_by_name=True)

    def ensure_dirs(self) -> None:
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.reports_dir).mkdir(parents=True, exist_ok=True)
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.audit_log_path).parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
