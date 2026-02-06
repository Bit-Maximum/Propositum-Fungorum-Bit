import json
import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from app.llm.yandex.YandexLlmClient import YandexLlmClient
from app.config import settings
from app.llm.yandex.AsyncYandexLlmClient import AsyncYandexLlmClient
from app.utils.guideline_aggregator import GuidelineAggregator
from app.metrics.load_baseline import load_baseline, save_baseline
from app.metrics.evaluator import evaluate
from fastapi import HTTPException

from .storage.s3_client import S3MemoryClient
from .storage.s3_metadata import Metadata
from .prompt_manager import PromptManager


logger = logging.getLogger(__name__)

class Pipeline:
    def __init__(self, prompts_dir: Path):
        # self.prompts_dir = prompts_dir
        self.llm_client = AsyncYandexLlmClient(4)
        self.is_parallel = settings.LLM_PARALLEL_TASK_MODE
        self.prompt_manager = PromptManager(prompts_dir)

        self.s3_client = S3MemoryClient(settings.MINIO_APP_BUCKET_NAME, aws_access_key_id=settings.MINIO_APP_USER,
                                        aws_secret_access_key=settings.MINIO_APP_PASSWORD, endpoint_url=settings.MINIO_APP_ENDPOINT)

        self.metadata = Metadata("data/metadata.json")


    async def __aggregate_results(self, prompt: str, chunks: list[str]):
        results = await self.llm_client.extract_guideline_batch(chunks, prompt=prompt)

        aggregator = GuidelineAggregator()
        for result in results:
            aggregator.add(result)

        return aggregator.get()


    def _upload_step_results_to_s3(self, step_results: dict) -> dict:
        try:
            logger.info(f"(S3) Начинаем загружать результаты этапов в S3")
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_path = f"llm-pipeline/runs/"

            uploaded_paths = {}

            while self.s3_client.object_exists(f"{base_path}{run_id}.json"):
                run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            logger.info(f"(S3) Путь загрузки: {base_path}{run_id}")
            for step_name, result in step_results.items():
                s3_key = f"{base_path}{run_id}/{step_name}.json"

                logger.info(f"(S3) Загружаем файл {s3_key}")
                byte_io = BytesIO(
                    json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
                )

                self.s3_client.upload_stream(byte_io, f"{base_path}{run_id}/{step_name}.json")

                uploaded_paths[step_name] = s3_key

            logger.info(f"(S3) Загружены файлы: {uploaded_paths}")
            return uploaded_paths

        except Exception as e:
            logger.error(f"Ошибка при загрузке файл в S3: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Fucked by stupid"
            )

    async def run(self, text: str = "") -> dict:

        step_results = {}

        llm = YandexLlmClient()
        step_1_prompt_path: Path = self.prompt_manager.get_step_prompt(1)
        step_1_prompt: str = step_1_prompt_path.read_text("utf-8")

        logger.info(f"(1/4) 'Этап 1'")
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
        self._upload_step_results_to_s3(step_results)

        return step_4
