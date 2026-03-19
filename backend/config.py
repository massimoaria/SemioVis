"""Application settings via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """SemioVis configuration. All values can be overridden via environment variables."""

    # App
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    is_desktop: bool = False

    # Async strategy
    use_celery: bool = False
    redis_url: str = "redis://localhost:6379/0"

    # Analysis defaults
    reading_direction: str = "ltr"
    coding_orientation: str = "naturalistic"
    saliency_method: str = "spectral"
    grid_size: str = "3x3"

    # Detection backend: "local" (default), "google", "aws"
    detection_backend: str = "local"

    # LLM interpretation: "auto" (cascade), "openai", "gemini", "mistral", "local"
    interpretation_llm: str = "auto"

    # Depth model
    depth_model_path: str = ""

    # API keys (all optional)
    gemini_api_key: str = ""
    openai_api_key: str = ""
    mistral_api_key: str = ""
    google_vision_key: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
