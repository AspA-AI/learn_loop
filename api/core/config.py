from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Learn Loop API"
    DEBUG: bool = True
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None

    # Opik (Comet) tracing / evals
    # Docs: https://www.comet.com/docs/opik/
    OPIK_API_KEY: Optional[str] = None
    OPIK_URL: Optional[str] = None  # Optional: self-hosted instance URL
    OPIK_PROJECT: str = "learn_loop"
    OPIK_ENABLED: bool = True

    # Deployment: optionally serve the built frontend from the backend container
    SERVE_CLIENT: bool = False
    
    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_DB_URL: Optional[str] = None # postgresql://postgres:[password]@db.[id].supabase.co:5432/postgres
    
    # Weaviate
    WEAVIATE_URL: Optional[str] = None
    WEAVIATE_API_KEY: Optional[str] = None
    
    # Authentication
    JWT_SECRET: str = "your-secret-key-change-in-production"  # Change this in production!
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24 * 7  # 7 days
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

