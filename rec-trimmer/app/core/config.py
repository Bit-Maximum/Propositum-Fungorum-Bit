from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel


class AppSettings(BaseModel):
    HOST: str = "0.0.0.0"
    PORT: int = 8000


class Settings(BaseSettings):
    APP: AppSettings

    model_config = SettingsConfigDict(
        env_file='.env',
        env_nested_delimiter='__',
        env_file_encoding='utf-8',
    )


settings: Settings = Settings()
