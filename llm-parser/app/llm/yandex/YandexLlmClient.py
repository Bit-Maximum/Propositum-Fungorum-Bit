import requests
from typing import Dict, Any
from app.config.settings import settings
import json
import re
from .YandexLlmResponseParser import YandexLlmResponseParser


def _safe_json(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        raise ValueError("LLM returned empty response")

    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON:\n{text}")


class YandexLlmClient:

    def __init__(self):
        self.api_url = settings.YANDEX_API_URL
        self.auth_token = settings.YANDEX_AUTH_TOKEN
        self.model_package = settings.YANDEX_MODEL_PACKAGE

    def _call(
        self,
        system_prompt: str,
        user_content: str,
        max_tokens: int = 4096,
        temperature: float = 0.01,
    ) -> str:
        payload = {
            "modelUri": f"gpt://{self.model_package}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": max_tokens
            },
            "messages": [
                {"role": "system", "text": system_prompt},
                {"role": "user", "text": user_content}
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.auth_token}"
        }

        response = requests.post(self.api_url, json=payload, headers=headers)
        response.raise_for_status()

        body = response.json()
        result = YandexLlmResponseParser.parse_response(body)

        return result.get_first_message_text()

    def extract_guideline(self, text: str, prompt: str) -> Dict[str, Any]:
        result = self._call(
            system_prompt="Ты медицинский эксперт.",
            user_content=prompt.replace("{{TEXT}}", text),
            max_tokens=4000
        )
        return _safe_json(result)
