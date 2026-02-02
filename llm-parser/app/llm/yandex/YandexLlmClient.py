import requests
from typing import Dict, Any, Optional
import json
import re
from app.config import settings
from .YandexLlmResponseParser import YandexLlmResponseParser


def _safe_json(text: str) -> Dict[str, Any]:
    if not text or not text.strip():
        raise ValueError("LLM returned empty response")

    s = text.strip()

    # Срезаем код-блоки '''json ... '''
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s)

    # Пробуем как есть
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    # Пытаемся выдернуть первый JSON-объект или массив
    m = re.search(r"(\{.*\}|\[.*\])", s, flags=re.S)
    if m:
        candidate = m.group(1)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Если всё плохо — выбрасываем исходный текст
    raise ValueError(f"LLM returned invalid JSON:\n{s}")


class YandexLlmClient:

    def __init__(self, default_model_name: str = "yandexgpt-lite"):
        self.api_url = settings.YANDEX_API_URL
        self.auth_token = settings.YANDEX_AUTH_TOKEN
        self.model_package = settings.YANDEX_MODEL_PACKAGE
        self.default_model_name = default_model_name

    def _call(
        self,
        system_prompt: str,
        user_content: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        model_name: Optional[str] = None,
        seed: Optional[int] = None
    ) -> str:
        payload = {
            "modelUri": f"gpt://{self.model_package}/{model_name or self.default_model_name}",
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

        # Если API поддерживает randomSeed — добавим детерминизм
        if seed is not None:
            # YandexGPT поддерживает randomSeed в completionOptions (в новых релизах)
            payload["completionOptions"]["randomSeed"] = seed

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.auth_token}"
        }

        response = requests.post(self.api_url, json=payload, headers=headers)
        response.raise_for_status()

        body = response.json()
        result = YandexLlmResponseParser.parse_response(body)

        return result.get_first_message_text()

    # Универсальный генератор (сырой ответ)
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        force_json: bool = False,
        max_tokens: int = 4000,
        temperature: float = 0.0,
        model_name: Optional[str] = None,
        seed: Optional[int] = None
    ) -> str:
        sys_prompt = system_prompt or (
            "Ты — детерминированный формальный парсер. "
            "Возвращай СТРОГО валидный JSON. НИКАКОГО текста вне JSON."
            if force_json else
            "Ты медицинский эксперт."
        )
        return self._call(
            system_prompt=sys_prompt,
            user_content=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_name=model_name,
            seed=seed
        )

    # Универсальный извлекатель JSON (dict)
    def extract_json(
            self,
            prompt: str,
            *,
            system_prompt: Optional[str] = None,
            force_json: bool = True,  # по умолчанию включаем "жёсткий JSON"
            max_tokens: int = 4000,
            temperature: float = 0.0,
            model_name: Optional[str] = None,
            seed: Optional[int] = None
    ) -> Dict[str, Any]:
        text = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            force_json=force_json,
            max_tokens=max_tokens,
            temperature=temperature,
            model_name=model_name,
            seed=seed
        )
        return _safe_json(text)

    # Обратная совместимость: (text, prompt) → JSON
    def extract_guideline(
            self,
            text: str,
            prompt: str,
            *,
            force_json: bool = True,
            max_tokens: int = 4000,
            temperature: float = 0.0,
            model_name: Optional[str] = None,
            seed: Optional[int] = None
    ) -> Dict[str, Any]:
        full_prompt = prompt.replace("{{TEXT}}", text)
        return self.extract_json(
            prompt=full_prompt,
            force_json=force_json,
            max_tokens=max_tokens,
            temperature=temperature,
            model_name=model_name,
            seed=seed
        )

    # Обратная совместимость: уже собранный промпт → JSON
    def extract_guideline_prompt(
            self,
            prompt: str,
            *,
            force_json: bool = True,
            max_tokens: int = 4000,
            temperature: float = 0.0,
            model_name: Optional[str] = None,
            seed: Optional[int] = None
    ) -> Dict[str, Any]:
        return self.extract_json(
            prompt=prompt,
            force_json=force_json,
            max_tokens=max_tokens,
            temperature=temperature,
            model_name=model_name,
            seed=seed
        )