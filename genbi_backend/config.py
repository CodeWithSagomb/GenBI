import os
from pydantic import BaseModel, Field

class Settings(BaseModel):
    """
    Configuration de l'application GenBI Backend.
    Gère le chargement des variables d'environnement avec des valeurs par défaut sécurisées.
    """
    # Configuration PostgreSQL Administrative
    DB_HOST: str = Field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    DB_PORT: int = Field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    DB_NAME: str = Field(default_factory=lambda: os.getenv("DB_NAME", "genbi"))
    DB_USER: str = Field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    DB_PASSWORD: str = Field(default_factory=lambda: os.getenv("DB_PASSWORD", "postgres_admin_123"))

    # Configuration PostgreSQL Lecture Seule (Zero-Trust pour l'Agent IA)
    DB_READONLY_USER: str = Field(default_factory=lambda: os.getenv("DB_READONLY_USER", "genbi_readonly"))
    DB_READONLY_PASSWORD: str = Field(default_factory=lambda: os.getenv("DB_READONLY_PASSWORD", "genbi_secure_readonly_123"))

    # Configuration de l'Agent LLM (Ollama)
    OLLAMA_BASE_URL: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"))
    OLLAMA_MODEL: str = Field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"))

    # Couche Sémantique (dbt)
    DBT_MANIFEST_PATH: str = Field(default_factory=lambda: os.getenv("DBT_MANIFEST_PATH", "./dbt_project/target/manifest.json"))

    # Application Settings
    APP_ENV: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "true").lower() in ("true", "1", "yes"))

# Instanciation globale des paramètres de configuration
settings = Settings()
