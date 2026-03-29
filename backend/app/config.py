from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # Reddit
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "uchicago-counselor/1.0"

    # Database
    database_url: str = "sqlite:///data/uchicago.db"
    chroma_persist_dir: str = "data/chroma"

    # App
    app_name: str = "UChicago Virtual Counselor"
    debug: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def db_path(self) -> Path:
        return Path(self.database_url.replace("sqlite:///", ""))

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir)


settings = Settings()
