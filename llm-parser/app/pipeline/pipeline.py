import json
from datetime import datetime
from pathlib import Path
from app.llm.yandex.YandexLlmClient import YandexLlmClient
from app.config import settings
from app.llm.yandex.AsyncYandexLlmClient import AsyncYandexLlmClient
from app.utils.guideline_aggregator import GuidelineAggregator
from app.metrics.load_baseline import load_baseline, save_baseline
from app.metrics.evaluator import evaluate
from .prompt_manager import PromptManager


class Pipeline:
    def __init__(self, prompts_dir: Path):
        # self.prompts_dir = prompts_dir
        self.llm_client = AsyncYandexLlmClient(4)
        self.is_parallel = settings.LLM_PARALLEL_TASK_MODE
        self.prompt_manager = PromptManager(prompts_dir)

        self.outputs_dir = (
                Path(__file__).resolve()
                .parents[1]
                / "outputs"
        )
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    async def __aggregate_results(self, prompt: str, chunks: list[str]):
        results = await self.llm_client.extract_guideline_batch(chunks, prompt=prompt)

        aggregator = GuidelineAggregator()
        for result in results:
            aggregator.add(result)

        return aggregator.get()


    def _save_step_results(self, step_results: dict) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for step_name, result in step_results.items():
            file_path = self.outputs_dir / f"{step_name}_{timestamp}.json"

            with file_path.open("w", encoding="utf-8") as fout:
                json.dump(result, fout, ensure_ascii=False, indent=2)


    async def run(self, text: str = "") -> dict:

        step_results = {}

        llm = YandexLlmClient()
        step_1_prompt_path: Path = self.prompt_manager.get_step_prompt(1)
        step_1_prompt: str = step_1_prompt_path.read_text("utf-8")

        step_1 = llm.extract_guideline(text=text, prompt=step_1_prompt)
        step_results["step_1"] = step_1

        # baseline = load_baseline()
        # if baseline is None:
        #     save_baseline(step_1)
        #     return {
        #         "result": step_1,
        #         "metrics": None,
        #         "message": "Baseline created"
        #     }
        # metrics = evaluate(baseline, step_1)

        step_2_prompt_path: Path = self.prompt_manager.get_step_prompt(2)
        step_2_prompt: str = step_2_prompt_path.read_text("utf-8")

        step_2 = llm.extract_guideline(text=json.dumps(step_1, ensure_ascii=False), prompt=step_2_prompt)
        step_results["step_2"] = step_2

        step_3_prompt_path: Path = self.prompt_manager.get_step_prompt(3)
        step_3_prompt: str = step_3_prompt_path.read_text("utf-8")

        step_3 = llm.extract_guideline(text=json.dumps(step_2, ensure_ascii=False), prompt=step_3_prompt)
        step_results["step_3"] = step_3

        step_4_prompt_path: Path = self.prompt_manager.get_step_prompt(4)
        step_4_prompt: str = step_4_prompt_path.read_text("utf-8")

        step_4 = llm.extract_guideline(text=json.dumps(step_3, ensure_ascii=False), prompt=step_4_prompt)
        step_results["step_4"] = step_4

        self._save_step_results(step_results)

        return step_4
