import json
from pathlib import Path

from app.llm.yandex.YandexLlmClient import YandexLlmClient
from app.api.parse import PDFParser


class Pipeline:
    def __init__(self, prompts_dir: Path):
        self.llm = YandexLlmClient()
        self.prompts_dir = prompts_dir

    def run(self, text: str) -> dict:
        step_1_prompt = (self.prompts_dir / "step_1_structure.md").read_text("utf-8")
        step_2_prompt = (self.prompts_dir / "step_2_entities.md").read_text("utf-8")
        step_3_prompt = (self.prompts_dir / "step_3_conditions.md").read_text("utf-8")

        step_1 = self.llm.extract_guideline(text, step_1_prompt)
        step_2 = self.llm.extract_guideline(text, step_2_prompt)

        step_3_text = step_3_prompt.replace("{{FIRST_STEP}}", json.dumps(step_1, ensure_ascii=False))
        step_3_text = step_3_text.replace("{{SECOND_STEP}}", json.dumps(step_2, ensure_ascii=False))
        step_3 = self.llm.extract_guideline(text, step_3_text)

        # step_3 = step3_link(step_1, step_2)

        return {
            "step_1": step_1,
            "step_2": step_2,
            "step_3": step_3
        }