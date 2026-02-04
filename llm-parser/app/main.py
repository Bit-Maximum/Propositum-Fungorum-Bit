from pathlib import Path
from fastapi import FastAPI, UploadFile, Body
import uvicorn
from metrics import (
    extract_entities,
    compare_documents,
    compare_documents_per_label,
)
from api.parse import PDFParser
from pipeline.pipeline import Pipeline

app = FastAPI(title="LLM Clinical Guideline Parser")

BASE_DIR = Path(__file__).parents[1]
PROMPTS_DIR = BASE_DIR / "app" / "pipeline" / "prompts"

pipeline = Pipeline(PROMPTS_DIR)


@app.post("/")
async def parse_pdf(file: UploadFile):
    tmp_path = Path("/tmp") / file.filename
    tmp_path.write_bytes(file.file.read())

    parser = PDFParser()
    text = parser.parse(str(tmp_path))

    return await pipeline.run(text)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)