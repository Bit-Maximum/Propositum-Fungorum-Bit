from typing import Dict, Any

from .base import BaseLlmClient
from .yandex.YandexLlmClient import YandexLlmClient


class YandexLlmAdapter(BaseLlmClient):
    """
    Адаптер между pipeline и конкретным YandexLlmClient.
    """

    def __init__(self):
        self.client = YandexLlmClient()

    def call_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None
    ) -> Dict[str, Any]:


        return self.client.extract_guideline(
            text="",
            prompt=user_prompt
        )
