"""
Configuration management for Minecraft Wiki Bot

Settings are loaded from .env file and environment variables.
See .env.example for all available options.
"""

from pathlib import Path

from pydantic_settings import BaseSettings

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Try to load .env file from current directory
    env_file_path = Path(".env")
    if env_file_path.exists():
        load_dotenv(env_file_path)
        print(f"✓ Loaded environment from {env_file_path.absolute()}")
    else:
        print("⚠ .env file not found, using environment variables only")
except ImportError:
    # dotenv not available, rely on environment variables
    print("⚠ python-dotenv not available, using environment variables only")
    pass


class Settings(BaseSettings):
    """Application settings with validation"""

    # Bot configuration
    bot_port: int = 8111  # Port for FastAPI server (BOT_PORT in .env)
    bot_name: str = "MinecraftBot"  # Bot username in Nextcloud
    bot_display_name: str = "Minecraft Helper"  # Bot display name

    # Network configuration (for Docker)
    network_name: str = "nextcloud-aio"  # Docker network name

    # Nextcloud configuration
    nextcloud_url: str | None = None  # Nextcloud instance URL
    # (NEXTCLOUD_URL in .env)
    nextcloud_bot_token: str | None = (
        None  # Bot authentication token  # (NEXTCLOUD_BOT_TOKEN in .env)
    )

    # Security
    shared_secret: str | None = None  # Webhook signature verification

    # LLM configuration
    xai_api_key: str | None = None  # x.ai API key (XAI_API_KEY in .env)
    xai_url: str = "https://api.x.ai/v1"  # x.ai API URL
    model_name: str = "grok-4-fast-non-reasoning"  # x.ai model name

    prompt_template_path: str = "prompt_template.txt"  # External prompt
    # template file (PROMPT_TEMPLATE_PATH in .env)

    # Performance settings
    max_workers: int = 2
    batch_size: int = 50

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/nextcloud_bot.log"
    verbose_logging: bool = False  # Enable detailed logging of messages and
    # responses

    model_config = {
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
