"""Centralized settings loaded from environment variables. Single source of truth
for API keys, DB URLs, and thresholds (e.g. story-matching similarity cutoffs)."""
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    news_api_key: str = ""
    news_query: str = "artificial intelligence"
    postgres_url: str = ""
    neo4j_uri: str = ""
    chroma_path: str = "./chroma_data"
    duplicate_threshold: float = 0.92
    new_chapter_threshold: float = 0.75
    ambiguous_lower_threshold: float = 0.6

settings = Settings()
