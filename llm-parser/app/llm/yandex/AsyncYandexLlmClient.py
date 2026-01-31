import asyncio
import aiohttp
from typing import List, Dict, Any
from ...config import settings

from .YandexLlmResponseParser import YandexLlmResponseParser
from .YandexLlmClient import _safe_json


class AsyncYandexLlmClient:

    def __init__(self, max_concurrent_requests: int = 5):
        self.api_url = settings.YANDEX_API_URL
        self.auth_token = settings.YANDEX_AUTH_TOKEN
        self.model_package = settings.YANDEX_MODEL_PACKAGE

        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.timeout = aiohttp.ClientTimeout(total=300)

    async def _call(
        self,
        session: aiohttp.ClientSession,
        system_prompt: str,
        user_content: str,
        max_tokens: int = 4096,
        temperature: float = 0.01,
    ) -> str:
        async with self.semaphore:
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

            try:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    response.raise_for_status()
                    body = await response.json()
                    result = YandexLlmResponseParser.parse_response(body)
                    return result.get_first_message_text()

            except Exception as e:
                raise

    async def extract_guideline_batch(
        self,
        chunks: List[str],
        prompt: str
    ) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._process_chunk(session, chunk, prompt)
                for chunk in chunks
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        parsed = []
        for r in results:
            parsed.append(_safe_json(r) if isinstance(r, str) else {})
        return parsed

    async def _process_chunk(
        self,
        session: aiohttp.ClientSession,
        chunk: str,
        prompt: str
    ) -> str:
        return await self._call(
            session=session,
            system_prompt="Ты медицинский эксперт.",
            user_content=prompt.replace("{{TEXT}}", chunk)
        )

