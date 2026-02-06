from __future__ import annotations
import re
from typing import List, Dict, Any, Optional
import hashlib
import json
from .paragraph import Paragraph
from .context_store import ContextStore, DocumentContext
from .validators import ensure_json_text, validate_with_schema


SURGERY_KEYWORDS = [
    "хирургическ", "операци", "эндопротез", "остеосинтез",
    "фиксац", "остеотом", "репозиц", "пластик", "доступ"
]

def normalize_text(t: str) -> str:
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()

def segment_text(t: str) -> List[str]:
    parts = re.split(r"\n\s*\n", t)
    parts = [p.strip() for p in parts if p and p.strip()]
    return parts

def filter_paragraphs(paragraphs: List[Paragraph], *, scope: str) -> List[Paragraph]:
    if scope == "surgery_only":
        return [p for p in paragraphs if any(k in p.text.lower() for k in SURGERY_KEYWORDS)]
    if scope == "broad":
        return paragraphs
    return paragraphs


class MCP:
    def __init__(self, store: ContextStore, llm_client, prompts_dir, *, model_preset: Optional[dict] = None):
        self.store = store
        self.llm = llm_client
        self.prompts_dir = prompts_dir
        self.model_preset = model_preset or dict(temperature=0.0, top_p=1.0, seed=13)

    def start_session(self, raw_text: str) -> DocumentContext:
        norm = normalize_text(raw_text)
        paragraphs: List[Paragraph] = []
        for i, t in enumerate(segment_text(norm)):
            pid = hashlib.md5(t.encode("utf-8")).hexdigest()[:12]
            paragraphs.append(Paragraph(id=pid, text=t, index=i))
        doc_id = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        ctx = DocumentContext(doc_id=doc_id, paragraphs=paragraphs, meta={"version": "v1"})
        self.store.save_document(ctx)
        return ctx

    def build_context_block(self, ctx: DocumentContext, *, scope: str) -> str:
        selected = filter_paragraphs(ctx.paragraphs, scope=scope)
        block = [{"id": p.id, "text": p.text, "index": p.index} for p in selected]
        return json.dumps(block, ensure_ascii=False)

    def run_step(
            self,
            ctx: DocumentContext,
            step_name: str,
            base_prompt: str,
            response_schema,
            *,
            scope: str,
            extra_vars: Optional[Dict[str, Any]] = None
    ):
        # cache_key = f"{ctx.doc_id}:{step_name}:{hashlib.md5(base_prompt.encode()).hexdigest()}"
        # cached = self.store.get_cache(cache_key)
        # if cached:
        #     return cached

        ctx_block = self.build_context_block(ctx, scope=scope)
        prompt_text = base_prompt.replace("{{TEXT}}", ctx_block)
        if extra_vars:
            for k, v in extra_vars.items():
                v_str = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
                prompt_text = prompt_text.replace(f"{{{{{k}}}}}", v_str)

        json_obj = self.llm.extract_json(
            prompt_text,
            force_json=True,
            temperature=0.0,
            seed=self.model_preset.get("seed", 13)
        )
        json_text = json.dumps(json_obj, ensure_ascii=False)
        data = validate_with_schema(json_text, response_schema)
        # self.store.set_cache(cache_key, data)
        self.store.save_step(ctx.doc_id, step_name, data)
        return data
        # raw = self.llm.extract_guideline(text="", prompt=prompt_text, force_json=True, **self.model_preset)
        # print(raw)
        # json_text = ensure_json_text(raw)
        # data = validate_with_schema(json_text, response_schema)
        #
        # # self.store.set_cache(cache_key, data)
        # self.store.save_step(ctx.doc_id, step_name, data)
        # return data