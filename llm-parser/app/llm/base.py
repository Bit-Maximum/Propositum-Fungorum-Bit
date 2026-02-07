from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseLlmClient(ABC):
    """
    Абстракция над LLM.
    """

    @abstractmethod
    def call_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None
    ) -> Dict[str, Any]:
        """
        Должен вернуть валидный JSON (dict).
        Любая ошибка парсинга — exception.
        """
        raise NotImplementedError
