import json
from pathlib import Path

import uvicorn
from fastapi import FastAPI, UploadFile
from api import parse, health
from metrics.evaluate_metrcis import evaluate_step2

app = FastAPI(
    title="LLM Clinical Guideline Parser",
    version="0.1.0"
)

BASE_DIR = Path(__file__).parents[1]
PROMPTS_DIR = BASE_DIR / "app" / "pipeline" / "prompts"

# app.include_router(parse.router, prefix="/api")
# app.include_router(health.router, prefix="/api")

from api.parse import PDFParser
from llm.yandex.YandexLlmClient import YandexLlmClient

results = [{}, {}]


def test(text: str):
    prompt = (PROMPTS_DIR / "step_2_entities.md").read_text("utf-8")

    llm = YandexLlmClient()
    result = llm.extract_guideline(text, prompt)
    results[0] = result
    return results


@app.post("/")
async def root(file: UploadFile):
    tmp_path = Path("/tmp") / file.filename
    tmp_path.write_bytes(file.file.read())

    parser = PDFParser()
    text = parser.parse(str(tmp_path))

    llm = YandexLlmClient()
    first_prompt = (PROMPTS_DIR / "step_1_structure.md").read_text("utf-8")
    first_result = llm.extract_guideline(text, first_prompt)

    second_prompt = (PROMPTS_DIR / "step_2_entities.md").read_text("utf-8")
    second_res = llm.extract_guideline(text, second_prompt)

    return {
        "first_step": first_result,
        "second_step": second_res,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)