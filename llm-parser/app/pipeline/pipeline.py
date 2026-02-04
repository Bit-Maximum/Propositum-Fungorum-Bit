import asyncio
from pathlib import Path
from app.llm.yandex.YandexLlmClient import YandexLlmClient
from app.config import settings
from app.llm.yandex.AsyncYandexLlmClient import AsyncYandexLlmClient
from app.llm.openai.openai_client import OpenAIAdapter
from app.utils.chunker import TextChunker
from app.utils.guideline_aggregator import GuidelineAggregator


class Pipeline:
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self.llm_client = OpenAIAdapter()
        self.is_parallel = settings.LLM_PARALLEL_TASK_MODE

    async def __aggregate_results(self, prompt:str, chunks: list[str]):
        results = await self.llm_client.extract_guideline_batch(chunks=chunks, user_prompt=prompt, system_prompt=None)

        aggregator = GuidelineAggregator()
        for result in results:
            aggregator.add(result)

        return aggregator.get()

    async def run(self, text: str) -> dict:
        step_1_prompt = (self.prompts_dir / "step_1_structure.md").read_text("utf-8")

        chunker = TextChunker()
        chunks = chunker.split(text)

        first_res, second_res = {}, {}
        if self.is_parallel:
            first_task = asyncio.create_task(self.__aggregate_results(step_1_prompt, chunks))
            second_task = asyncio.create_task(self.__aggregate_results(step_1_prompt, chunks))
            print(f"[INFO]: First task: {first_task}, Second task: {second_task}")
            first_res, second_res = await asyncio.gather(first_task, second_task)
        else:
            first_res = await self.llm_client.extract_guideline_batch(chunks, user_prompt=step_1_prompt, system_prompt=None)

        return {
            "step_1": first_res,
            "step_1_2": second_res
        }