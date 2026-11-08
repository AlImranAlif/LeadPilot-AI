from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'sqlite:///./leadpilot.db'
    extraction_provider: str = 'demo'
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-2.0-flash'
    api_key: str = ''
    cors_origins: str = 'http://localhost:8000,http://127.0.0.1:8000'

@lru_cache
def get_settings() -> Settings:
    return Settings()
