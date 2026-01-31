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

results = []


def test(text: str):
    prompt = (PROMPTS_DIR / "step_2_entities.md").read_text("utf-8")

    llm = YandexLlmClient()
    result = llm.extract_guideline(text, prompt)
    results.insert(0, result)
    return results


@app.post("/")
async def root(file: UploadFile):
    tmp_path = Path("/tmp") / file.filename
    tmp_path.write_bytes(file.file.read())
    prompt = (PROMPTS_DIR / "step_2_entities.md").read_text("utf-8")

    parser = PDFParser()
    text = parser.parse(str(tmp_path))

    if not results:
        test(text)
    llm1 = YandexLlmClient()
    result1 = llm1.extract_guideline(text, prompt)
    results.insert(1, result1)

    res = evaluate_step2(results[0], results[1])

    return res


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)