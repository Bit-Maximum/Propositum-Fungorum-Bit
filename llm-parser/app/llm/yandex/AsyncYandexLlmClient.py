import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from app.config import settings
from .YandexLlmResponseParser import YandexLlmResponseParser
from .YandexLlmClient import _safe_json


class AsyncYandexLlmClient:

    def __init__(self, max_concurrent_requests: int = 5, default_model_name: str = "yandexgpt-lite"):
        self.api_url = settings.YANDEX_API_URL
        self.auth_token = settings.YANDEX_AUTH_TOKEN
        self.model_package = settings.YANDEX_MODEL_PACKAGE

        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.timeout = aiohttp.ClientTimeout(total=300)
        self.default_model_name = default_model_name

    async def _call(
        self,
        session: aiohttp.ClientSession,
        system_prompt: str,
        user_content: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        model_name: Optional[str] = None,
        seed: Optional[int] = None
    ) -> str:
        async with self.semaphore:
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

            if seed is not None:
                payload["completionOptions"]["randomSeed"] = seed

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Api-Key {self.auth_token}"
            }

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

    async def generate(
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
        async with aiohttp.ClientSession() as session:
            return await self._call(
                session=session,
                system_prompt=sys_prompt,
                user_content=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                model_name=model_name,
                seed=seed
            )

    async def extract_json(
            self,
            prompt: str,
            *,
            system_prompt: Optional[str] = None,
            force_json: bool = True,
            max_tokens: int = 4000,
            temperature: float = 0.0,
            model_name: Optional[str] = None,
            seed: Optional[int] = None
    ) -> Dict[str, Any]:
        text = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            force_json=force_json,
            max_tokens=max_tokens,
            temperature=temperature,
            model_name=model_name,
            seed=seed
        )
        return _safe_json(text)

    async def extract_guideline_batch(
            self,
            chunks: List[str],
            prompt: str,
            *,
            force_json: bool = True,
            max_tokens: int = 4000,
            temperature: float = 0.0,
            model_name: Optional[str] = None,
            seed: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._process_chunk(
                    session=session,
                    chunk=chunk,
                    prompt=prompt,
                    force_json=force_json,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model_name=model_name,
                    seed=seed
                )
                for chunk in chunks
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        parsed: List[Dict[str, Any]] = []
        for r in results:
            parsed.append(_safe_json(r) if isinstance(r, str) else {})
        return parsed

    async def _process_chunk(
            self,
            session: aiohttp.ClientSession,
            chunk: str,
            prompt: str,
            *,
            force_json: bool = True,
            max_tokens: int = 3500,
            temperature: float = 0.0,
            model_name: Optional[str] = None,
            seed: Optional[int] = None
    ) -> str:
        sys_prompt = (
            "Ты — детерминированный формальный парсер. "
            "Возвращай СТРОГО валидный JSON. НИКАКОГО текста вне JSON."
            if force_json else
            "Ты медицинский эксперт."
        )
        full_prompt = prompt.replace("{{TEXT}}", chunk)
        return await self._call(
            session=session,
            system_prompt=sys_prompt,
            user_content=full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_name=model_name,
            seed=seed
        )