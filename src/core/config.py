"""
Configuration management for Minecraft Wiki Bot
"""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation"""

    # Bot configuration
    bot_port: int = 8000
    bot_name: str = "MinecraftBot"
    bot_display_name: str = "Minecraft Helper"

    # Nextcloud configuration
    nextcloud_url: str
    nextcloud_bot_token: str

    # Security
    shared_secret: str | None = None

    # LLM configuration
    ollama_url: str = "http://ollama:11434"
    model_name: str = "phi3:mini"

    # RAG configuration
    top_k_results: int = 5
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Performance settings
    max_workers: int = 2
    batch_size: int = 50

    # Cache configuration (legacy)
    enable_cache: bool = True
    cache_db_path: str = "recipe_cache.db"

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/nextcloud_bot.log"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def log_path(self) -> Path:
        """Get the log file path"""
        return Path(self.log_file)

    def ensure_log_directory(self):
        """Ensure log directory exists"""
        self.log_path.parent.mkdir(exist_ok=True)


# Global settings instance
settings = Settings()
