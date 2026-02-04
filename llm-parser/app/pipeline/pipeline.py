from asyncio import create_task
from pathlib import Path
from app.llm.yandex.YandexLlmClient import YandexLlmClient
from app.config import settings
from app.llm.yandex.AsyncYandexLlmClient import AsyncYandexLlmClient
from .mcp.processor import MCP
from .mcp.context_store import ContextStore
from .mcp.schemas import Step1Model, Step2Model, Step3Model
from .mcp.step3_linking import build_step3_linking
from .mcp.postprocess import dedupe_step1_structure
from app.utils.chunker import TextChunker
from app.utils.guideline_aggregator import GuidelineAggregator
import asyncio

class Pipeline:
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self.llm_client = AsyncYandexLlmClient(4)
        self.is_parallel = settings.LLM_PARALLEL_TASK_MODE

    async def __aggregate_results(self, prompt:str, chunks: list[str]):
        results = await self.llm_client.extract_guideline_batch(chunks, prompt=prompt)

        aggregator = GuidelineAggregator()
        for result in results:
            aggregator.add(result)

        return aggregator.get()

    async def run(self, text: str) -> dict:
        step_1_prompt = (self.prompts_dir / "step_1_structure.md").read_text("utf-8")
        step_2_prompt = (self.prompts_dir / "step_2_entities.md").read_text("utf-8")

        chunker = TextChunker()
        chunks = chunker.split(text)

        first_res, second_res = {}, {}
        if self.is_parallel:
            first_task = asyncio.create_task(self.__aggregate_results(step_1_prompt, chunks))
            second_task = asyncio.create_task(self.__aggregate_results(step_1_prompt, chunks))

            first_res, second_res = await asyncio.gather(first_task, second_task)
        else:
            first_res = await self.llm_client.extract_guideline_batch(chunks, prompt=step_1_prompt)

        # for chunk in chunks:
        #
        #     # 2) Шаг 1 — структура
        #     step_1 = self.mcp.run_step(
        #         ctx,
        #         step_name="step_1",
        #         base_prompt=step_1_prompt,
        #         response_schema=Step1Model,
        #         scope="surgery_only"
        #     )
        # step_1 = dedupe_step1_structure(step_1)
        # 3) Шаг 2 — сущности
        # step_2 = self.mcp.run_step(
        #     ctx,
        #     step_name="step_2",
        #     base_prompt=step_2_prompt,
        #     response_schema=Step2Model,
        #     scope="broad"
        # )
        #
        # # 4) Шаг 3 — детерминированная линковка (без LLM)
        # paragraphs = [{"id": p.id, "text": p.text, "index": p.index} for p in ctx.paragraphs]
        # step_3 = build_step3_linking(paragraphs, step_1, step_2)
        #
        # # 5) Валидация результата шага 3
        # step_3_validated = Step3Model.model_validate(step_3).model_dump()

        return {
            "step_1": first_res,
            "step_1_2": second_res
            # "step_2": step_2,
            # "step_3": step_3_validated
        }