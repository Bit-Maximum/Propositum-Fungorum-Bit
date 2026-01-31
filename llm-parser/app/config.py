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

    SERVICE_NAME: str = os.environ["SERVICE_NAME"]
    SERVICE_ENV: str = os.environ["SERVICE_ENV"]

settings = Settings()