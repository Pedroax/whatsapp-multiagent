"""Configurações da aplicação"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configurações do ambiente"""

    # LLM (usando OpenAI GPT-4)
    openai_api_key: str  # Obrigatório
    anthropic_api_key: Optional[str] = None  # Opcional (não usado)

    # WhatsApp Evolution API
    evolution_api_url: str
    evolution_api_key: str
    evolution_instance_name: str

    # Supabase
    supabase_url: str
    supabase_service_key: str

    # LC Baterias APIs
    lc_api_base_url: str
    lc_api_key: str

    # Redis (opcional)
    redis_url: Optional[str] = "redis://localhost:6379"

    # Application
    debug: bool = False
    log_level: str = "INFO"
    debounce_seconds: float = 5.0

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
