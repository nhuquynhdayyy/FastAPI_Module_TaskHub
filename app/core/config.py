from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DATABASE_URL: str
    DEFAULT_USER_ID: int = 1
    DEFAULT_PROJECT_ID: int = 1


settings = Settings()
