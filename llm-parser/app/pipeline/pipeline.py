from pathlib import Path
from app.llm.yandex.YandexLlmClient import YandexLlmClient
from .mcp.processor import MCP
from .mcp.context_store import ContextStore
from .mcp.schemas import Step1Model, Step2Model, Step3Model
from .mcp.step3_linking import build_step3_linking


class Pipeline:
    def __init__(self, prompts_dir: Path):
        self.llm = YandexLlmClient()
        self.prompts_dir = prompts_dir
        self.mcp = MCP(
            store=ContextStore(base_dir=prompts_dir.parent / "mcp_store"),
            llm_client=self.llm,
            prompts_dir=prompts_dir,
            model_preset=dict(temperature=0.0, seed=13)
        )

    def run(self, text: str) -> dict:
        step_1_prompt = (self.prompts_dir / "step_1_structure.md").read_text("utf-8")
        step_2_prompt = (self.prompts_dir / "step_2_entities.md").read_text("utf-8")

        # 1) Создаём контекст документа
        ctx = self.mcp.start_session(text)

        # 2) Шаг 1 — структура
        step_1 = self.mcp.run_step(
            ctx,
            step_name="step_1",
            base_prompt=step_1_prompt,
            response_schema=Step1Model,
            scope="surgery_only"
        )

        # 3) Шаг 2 — сущности
        step_2 = self.mcp.run_step(
            ctx,
            step_name="step_2",
            base_prompt=step_2_prompt,
            response_schema=Step2Model,
            scope="broad"
        )

        # 4) Шаг 3 — детерминированная линковка (без LLM)
        paragraphs = [{"id": p.id, "text": p.text, "index": p.index} for p in ctx.paragraphs]
        step_3 = build_step3_linking(paragraphs, step_1, step_2)

        # 5) Валидация результата шага 3
        step_3_validated = Step3Model.model_validate(step_3).model_dump()

        return {"step_1": step_1, "step_2": step_2, "step_3": step_3_validated}