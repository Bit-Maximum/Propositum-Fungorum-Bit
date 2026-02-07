from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass
from typing import List, Dict
from .paragraph import Paragraph


@dataclass
class DocumentContext:
    doc_id: str
    paragraphs: List[Paragraph]
    meta: Dict[str, Any]


class ContextStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _doc_dir(self, doc_id: str) -> Path:
        d = self.base_dir / doc_id
        d.mkdir(exist_ok=True)
        return d

    def save_document(self, ctx: DocumentContext):
        d = self._doc_dir(ctx.doc_id)
        paragraphs_payload = [
            {"id": p.id, "text": p.text, "index": p.index} for p in ctx.paragraphs
        ]
        (d / "paragraphs.json").write_text(
            json.dumps(paragraphs_payload, ensure_ascii=False), encoding="utf-8"
        )

    def save_step(self, doc_id: str, step_name: str, data: Any):
        d = self._doc_dir(doc_id)
        (d / f"{step_name}.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

    def load_step(self, doc_id: str, step_name: str) -> Optional[Any]:
        f = self._doc_dir(doc_id) / f"{step_name}.json"
        return json.loads(f.read_text("utf-8")) if f.exists() else None

    def set_cache(self, key: str, data: Any):
        f = self.base_dir / f"cache_{hash(key)}.json"
        f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def get_cache(self, key: str) -> Optional[Any]:
        f = self.base_dir / f"cache_{hash(key)}.json"
        return json.loads(f.read_text("utf-8")) if f.exists() else None

