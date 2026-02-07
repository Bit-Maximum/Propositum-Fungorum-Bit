import json
import logging
import warnings
from pathlib import Path

from app.llm.yandex.YandexLlmClient import YandexLlmClient
from app.config import settings
from app.llm.yandex.AsyncYandexLlmClient import AsyncYandexLlmClient
from app.utils.guideline_aggregator import GuidelineAggregator
from app.metrics.load_baseline import load_baseline, save_baseline
from app.metrics.evaluator import evaluate
from app.pipeline.storage.backend_client import BackendClient

from .prompt_manager import PromptManager


logger = logging.getLogger(__name__)

class Pipeline:
    def __init__(self, prompts_dir: Path):
        # self.prompts_dir = prompts_dir
        self.llm_client = AsyncYandexLlmClient(4)
        self.is_parallel = settings.LLM_PARALLEL_TASK_MODE
        self.prompt_manager = PromptManager(prompts_dir)

        self.backend_client = BackendClient("data/")



    async def __aggregate_results(self, prompt: str, chunks: list[str]):
        results = await self.llm_client.extract_guideline_batch(chunks, prompt=prompt)

        aggregator = GuidelineAggregator()
        for result in results:
            aggregator.add(result)

        return aggregator.get()



    async def run(self, text: str = "", filename: str = "file", display_name: str = "default", subtitle_name: str = "default") -> dict:

        step_results = {}

        llm = YandexLlmClient()

        uuid = await self.backend_client.upload_metadata(display_name, subtitle_name)
        await self.backend_client.upload_text_as_file(text, uuid)

        step_1_prompt_path: Path = self.prompt_manager.get_step_prompt(1)
        step_1_prompt: str = step_1_prompt_path.read_text("utf-8")

        logger.info(f"(1/4) 'Этап 1'")
        step_1 = llm.extract_guideline(text=text, prompt=step_1_prompt)
        step_results["step_1"] = step_1

        logger.info(f"(2/4) 'Этап 2'")
        step_2_prompt_path: Path = self.prompt_manager.get_step_prompt(2)
        step_2_prompt: str = step_2_prompt_path.read_text("utf-8")

        step_2 = llm.extract_guideline(text=json.dumps(step_1, ensure_ascii=False), prompt=step_2_prompt)
        step_results["step_2"] = step_2

        logger.info(f"(3/4) 'Этап 3'")
        step_3_prompt_path: Path = self.prompt_manager.get_step_prompt(3)
        step_3_prompt: str = step_3_prompt_path.read_text("utf-8")

        step_3 = llm.extract_guideline(text=json.dumps(step_2, ensure_ascii=False), prompt=step_3_prompt)
        step_results["step_3"] = step_3

        logger.info(f"(4/4) 'Этап 4'")
        step_4_prompt_path: Path = self.prompt_manager.get_step_prompt(4)
        step_4_prompt: str = step_4_prompt_path.read_text("utf-8")

        step_4 = llm.extract_guideline(text=json.dumps(step_3, ensure_ascii=False), prompt=step_4_prompt)
        step_results["step_4"] = step_4

        logger.info(f"(!) 'Пайплайн завершён успешно'")
        await self.backend_client.upload_step_results_to_s3(uuid, step_results)

        await self.backend_client.upload_json_as_file(step_4, uuid, "graph.json")

        await self.backend_client.reload_metadata()

        return step_4

    async def run_metrics_evaluation(self, text: str = "",
                                     filename: str = "file") -> dict:
        llm = YandexLlmClient()

        step_1_prompt_path: Path = self.prompt_manager.get_step_prompt(1)
        step_1_prompt: str = step_1_prompt_path.read_text("utf-8")

        logger.info("Запуск 1 этапа для получения метрик")
        step_1 = llm.extract_guideline(text=text, prompt=step_1_prompt)

        baseline: dict | None = load_baseline()
        processed_baseline = baseline

        if baseline is None:
            processed_baseline = {filename: step_1}
        elif filename not in processed_baseline:
            processed_baseline[filename] = step_1

        save_baseline(processed_baseline)

        metrics: dict = evaluate(processed_baseline[filename], step_1)

        return {
            "base": baseline,
            "result": step_1,
            "metrics": metrics,
            "message": "Baseline created"
        }

    async def run_metrics_evaluation_with_s3(self, uuid: str) -> dict:

        llm = YandexLlmClient()

        # TODO Проверить что набабашил Никита
        # в .storage.backend_client новая функция, чтобы получать ответ в виде:
        """
        {
            'type': 'text',
            'content': ...... тут для ввода в step_1
            'lines_count': ..... много линий
            'size': ..... жирный файл
        }
        """
        text_response = await self.backend_client.download_file("input.txt", uuid)
        step_1_response = await self.backend_client.download_file("step_1.json", uuid)

        step_1 = step_1_response.get("data")
        text = text_response.get('content')

        step_1_prompt_path: Path = self.prompt_manager.get_step_prompt(1)
        step_1_prompt: str = step_1_prompt_path.read_text("utf-8")

        logger.info("Запуск 1 этапа для получения метрик")
        step_1_extracted = llm.extract_guideline(text=text, prompt=step_1_prompt)

        # baseline: dict | None = load_baseline()
        # processed_baseline = baseline
        #
        # if baseline is None:
        #     processed_baseline = {uuid: step_1}
        # elif uuid not in processed_baseline:
        #     processed_baseline[uuid] = step_1
        #
        # save_baseline(processed_baseline)

        metrics: dict = evaluate(step_1, step_1_extracted)

        return {
            "base": step_1,
            "result": step_1_extracted,
            "metrics": metrics,
            "message": "Baseline created"
        }
