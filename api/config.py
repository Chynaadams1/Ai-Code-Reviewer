"""
api/config.py
All environment variables loaded via pydantic-settings.
Copy .env.example → .env and fill in your values.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # GitHub
    github_token: str = ""               # Personal access token with repo + pull_requests scope
    github_webhook_secret: str = ""      # Secret set when registering the webhook on GitHub

    # OpenAI
    openai_api_key: str = ""             # sk-...
    openai_model: str = "gpt-4o"        # model to use for reviews

    # App
    app_env: str = "development"         # development | production
    max_diff_chars: int = 12_000         # truncate huge diffs before sending to OpenAI

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
