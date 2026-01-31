from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class YandexUsage:
    completionTokens: str
    inputTextTokens: str
    totalTokens: str
    completionTokensDetails: Optional[Dict[str, Any]] = None

    def to_int_dict(self) -> Dict[str, int]:
        return {
            "completionTokens": int(self.completionTokens),
            "inputTextTokens": int(self.inputTextTokens),
            "totalTokens": int(self.totalTokens)
        }


@dataclass
class YandexLlmRsDto:
    alternatives: List[Dict[str, Any]]
    modelVersion: str
    usage: YandexUsage
    timestamp: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def get_first_message_text(self) -> str:
        return self.alternatives[0]["output"] if self.alternatives else ""
