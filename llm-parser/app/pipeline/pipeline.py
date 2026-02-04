from pathlib import Path
from app.llm.yandex.YandexLlmClient import YandexLlmClient
from app.config import settings
from app.llm.yandex.AsyncYandexLlmClient import AsyncYandexLlmClient
from app.utils.guideline_aggregator import GuidelineAggregator

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

        llm = YandexLlmClient()
        step_1 = llm.extract_guideline(text=text, prompt=step_1_prompt)

        return {
            "step_1": step_1
        }