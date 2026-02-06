import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    YANDEX_API_URL: str = os.environ["YANDEX_API_URL"]
    YANDEX_AUTH_TOKEN: str = os.environ["YANDEX_AUTH_TOKEN"]
    YANDEX_MODEL_PACKAGE: str = os.environ["YANDEX_MODEL_PACKAGE"]

    LLM_TEMPERATURE: float = os.environ["LLM_TEMPERATURE"]
    LLM_MAX_TOKENS: int = os.environ["LLM_MAX_TOKENS"]
    LLM_PARALLEL_TASK_MODE: bool = os.environ["LLM_PARALLEL_TASK_MODE"]

    SERVICE_NAME: str = os.environ["SERVICE_NAME"]
    SERVICE_ENV: str = os.environ["SERVICE_ENV"]

    BACKEND_HOST: str = os.environ["BACKEND_HOST"]
    BACKEND_UPLOAD_PATH: str = os.environ["BACKEND_UPLOAD_PATH"]
    BACKEND_DOWNLOAD_PATH: str = os.environ["BACKEND_DOWNLOAD_PATH"]
    BACKEND_METADATA_PATH: str = os.environ["BACKEND_METADATA_PATH"]
    BACKEND_RELOAD_PATH: str = os.environ["BACKEND_RELOAD_PATH"]

    MINIO_APP_ENDPOINT: str = os.getenv("MINIO_APP_ENDPOINT")
    MINIO_APP_USER: str = os.getenv("MINIO_APP_USER")
    MINIO_APP_PASSWORD: str = os.getenv("MINIO_APP_PASSWORD")
    MINIO_APP_BUCKET_NAME: str = os.getenv("MINIO_APP_BUCKET_NAME")

settings = Settings()
