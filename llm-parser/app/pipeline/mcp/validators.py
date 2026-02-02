from __future__ import annotations
from typing import Any, Type
from pydantic import BaseModel, ValidationError
from typing import Dict, Any
import json

def ensure_json_text(raw: Dict[str, Any]) -> str:
    try:
        return json.dumps(raw, ensure_ascii=False)
    except (TypeError, ValueError):
        # На всякий случай — если вдруг прилетело что-то несерилизуемое
        return "{}"


def validate_with_schema(raw_json: str, schema: Type[BaseModel]) -> Any:
    data = json.loads(raw_json)
    try:
        return schema.model_validate(data).model_dump()
    except ValidationError as e:
        raise ValueError(f"Schema validation failed: {e}")