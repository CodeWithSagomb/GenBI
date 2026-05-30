from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # PostgreSQL — lecture seule (toutes les routes sauf feedback)
    DB_HOST: str = "postgres"
    DB_PORT: int = 5432
    DB_NAME: str = "genbi"
    DB_READONLY_USER: str = "genbi_readonly"
    DB_READONLY_PASSWORD: str = "genbi_secure_readonly_123"

    # PostgreSQL — écriture limitée (feedback uniquement)
    DB_WRITE_USER: str = "genbi_write"
    DB_WRITE_PASSWORD: str = "genbi_write_456"

    # Ollama (LLM local natif macOS — accès depuis Docker)
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "qwen2.5-coder:7b"
    LLM_SQL_TIMEOUT: int = 30
    LLM_INSIGHT_TIMEOUT: int = 20

    # dbt manifest (chemin dans le conteneur Docker)
    DBT_MANIFEST_PATH: str = "/app/dbt_project/target/manifest.json"

    # Auth — API Keys par pharmacie (override depuis .env en production)
    API_KEY_BOURGUIBA: str = "pk_bourguiba_dev"
    API_KEY_ALMADIES: str = "pk_almadies_dev"
    API_KEY_NATION: str = "pk_nation_dev"

    APP_ENV: str = "development"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
