from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field


class StorageSettings(BaseModel):
    pass


class LocalStorageSettings(StorageSettings):
    ALLOWED_EXTENSIONS: set[str] = Field(
        default_factory=lambda: {'pdf'},
        description="Разрешенные расширения файлы"
    )
    ROOT: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent,
        description="Корневая директория проекта"
    )

    @property
    def LOCAL_UPLOAD_DIR(self) -> Path:
        return self.ROOT / "uploads"


class AppSettings(BaseModel):
    HOST: str = "0.0.0.0"
    PORT: int = 8000


class Settings(BaseSettings):
    STORAGE: LocalStorageSettings = Field(default_factory=LocalStorageSettings)
    APP: AppSettings = Field(default_factory=AppSettings)

    model_config = SettingsConfigDict(
        env_file='.env',
        env_nested_delimiter='__',
        extra='ignore',
        env_file_encoding='utf-8',
    )


settings: Settings = Settings()
