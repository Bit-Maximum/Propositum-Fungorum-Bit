import asyncio
import json
import re
from typing import Dict, Any, List, Optional

from openai import AsyncOpenAI
from abc import ABC, abstractmethod
import os

class BaseLLMAdapter(ABC):
    """Абстрактный базовый класс для всех LLM адаптеров."""

    @abstractmethod
    async def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Генерирует ответ на заданный промпт."""
        pass


class OpenAIConfig:
    def __init__(self):
        self.LLM_API_KEY = os.getenv("LLM_API_KEY")
        self.LLM_MODEL = os.getenv("LLM_MODEL")
        self.LLM_TEMPERATURE = float(
            os.getenv("LLM_TEMPERATURE", "0.01")
        )

    def check_common(self, logger=None):
        if not self.LLM_API_KEY:
            raise ValueError("LLM_API_KEY не задан")

    def check_specific(self, logger=None):
        if not self.LLM_MODEL:
            raise ValueError("LLM_MODEL не задан")


class OpenAIAdapter(BaseLLMAdapter):
    """Адаптер для взаимодействия с OpenAI API."""

    def __init__(self, config: OpenAIConfig = OpenAIConfig(), logger=None):
        self.config = config
        self.logger = logger

        self.config.check_common(logger)
        self.config.check_specific(logger)

        self.client = AsyncOpenAI(
            api_key=self.config.LLM_API_KEY,
        )

        # Например: "gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"
        self.model = self.config.LLM_MODEL
        self.temperature = self.config.LLM_TEMPERATURE

    async def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        messages = []

        if system_prompt:
            messages.append(
                {"role": "system", "content": system_prompt}
            )

        messages.append(
            {"role": "user", "content": user_prompt}
        )

        response = await self.client.responses.create(
            model=self.model,
            input=messages,
            # temperature=self.temperature,
        )

        if (
            response.error is not None
            or response.status != "completed"
            or not response.output_text
        ):
            error_message = (
                f"Ошибка при получении ответа от OpenAI: {response.error}"
            )
            if self.logger:
                self.logger.error(error_message)
            raise ValueError(error_message)

        return response.output_text

    def _safe_json(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            raise ValueError("LLM returned empty response")

        s = text.strip()

        if s.startswith("```"):
            s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
            s = re.sub(r"\n?```$", "", s)

        try:
            return json.loads(s)
        except json.JSONDecodeError:
            pass

        m = re.search(r"(\{.*\}|\[.*\])", s, flags=re.S)
        if m:
            candidate = m.group(1)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        raise ValueError(f"LLM returned invalid JSON:\n{s}")

    async def _process_chunk(
            self,
            text: str,
            user_prompt: str,
            system_prompt: str,

    ) -> Dict[str, Any]:
        full_prompt = user_prompt.replace("{{TEXT}}", text)

        sys_prompt = (
            "Ты — детерминированный формальный парсер. "
            "Возвращай СТРОГО валидный JSON. НИКАКОГО текста вне JSON."
            if not system_prompt else system_prompt
        )

        result = await self.generate_response(sys_prompt, full_prompt)
        return result

    async def extract_guideline_batch(
            self,
            chunks: List[str],
            user_prompt: str,
            system_prompt: str,
    ) -> List[Dict[str, Any]]:
        tasks = [
            self._process_chunk(
                text=chunk,
                user_prompt=user_prompt,
                system_prompt=system_prompt,

            )
            for chunk in chunks
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # results = []
        # # for chunk in chunks:
        # #     results.append(await self._process_chunk(chunk, user_prompt, system_prompt))

        parsed: List[Dict[str, Any]] = []
        for r in results:
            parsed.append(self._safe_json(r) if isinstance(r, str) else {})


        return parsed