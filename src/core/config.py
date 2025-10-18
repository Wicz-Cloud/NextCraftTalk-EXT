"""
Configuration management for Minecraft Wiki Bot

Settings are loaded from .env file and environment variables.
See .env.example for all available options.
"""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation"""

    # Bot configuration
    bot_port: int = 8111  # Port for FastAPI server (BOT_PORT in .env)
    bot_name: str = "MinecraftBot"  # Bot username in Nextcloud
    bot_display_name: str = "Minecraft Helper"  # Bot display name

    # Network configuration (for Docker)
    network_name: str = "nextcloud-aio"  # Docker network name

    # Nextcloud configuration
    nextcloud_url: str | None = None  # Nextcloud instance URL (NEXTCLOUD_URL in .env)
    nextcloud_bot_token: str | None = (
        None  # Bot authentication token (NEXTCLOUD_BOT_TOKEN in .env)
    )

    # Security
    shared_secret: str | None = None  # Webhook signature verification

    # LLM configuration
    xai_api_key: str | None = None  # x.ai API key (XAI_API_KEY in .env)
    xai_url: str = "https://api.x.ai/v1"  # x.ai API URL
    model_name: str = "grok-4-fast-non-reasoning"  # x.ai model name

    # RAG configuration
    top_k_results: int = 2  # Number of documents to retrieve
    embedding_model: str = (
        "sentence-transformers/all-MiniLM-L6-v2"  # Sentence transformer model
    )
    prompt_template_path: str = "prompt_template.txt"  # External prompt template file
    # (PROMPT_TEMPLATE_PATH in .env)

    # Performance settings
    max_workers: int = 2
    batch_size: int = 50

    # Cache configuration (legacy)
    enable_cache: bool = True
    cache_db_path: str = "recipe_cache.db"

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/nextcloud_bot.log"

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "protected_namespaces": ("settings_",),
    }

    @property
    def log_path(self) -> Path:
        """Get the log file path"""
        return Path(self.log_file)

    def ensure_log_directory(self) -> None:
        """Ensure log directory exists"""
        self.log_path.parent.mkdir(exist_ok=True)


# Global settings instance
settings = Settings()
