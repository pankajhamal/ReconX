"""Application settings, read from environment variables or the .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql://reconx:reconx@localhost:5432/reconx"
    frontend_url: str = "http://localhost:5173"


settings = Settings() 
