import json
from io import BytesIO
from pathlib import Path

import requests
from fastapi import FastAPI, UploadFile, APIRouter, Body, HTTPException,File
import uvicorn
from app.api.parse import PDFParser
from app.pipeline.pipeline import Pipeline
from app.config import settings
from app.pipeline.storage.backend_client import BackendClient

app = FastAPI(
    title="LLM Parser API",
    description="API for LLM document parsing",
    version="1.0.0",
    openapi_url="/api/parser/openapi.json",  # Доступен по /openapi.json внутри контейнера
    docs_url="/api/parser/docs",              # Swagger UI
    redoc_url="/api/parser/redoc",            # ReDoc
)

BASE_DIR = Path(__file__).parents[0]
PROMPTS_DIR = BASE_DIR / "app" / "pipeline" / "prompts"

pipeline = Pipeline(PROMPTS_DIR)

router: APIRouter = APIRouter(prefix='/api/parser')

file_text: str  # Пока так потом в сессию закинуть можно


@router.post("/")
async def parse_pdf(
        file: UploadFile,
        display_name: str,
        subtitle_name: str,
):

    tmp_path = Path("/tmp") / file.filename
    tmp_path.write_bytes(file.file.read())

    parser = PDFParser()
    global file_text
    file_text = parser.parse(str(tmp_path))

    graph_json = await pipeline.run(file_text, file.filename, display_name, subtitle_name)

    return graph_json

@router.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}


@router.post("/metrics")
async def metrics(file: UploadFile = File(...)):
    tmp_path = Path("/tmp") / file.filename

    content = await file.read()
    tmp_path.write_bytes(content)

    parser = PDFParser()
    text = parser.parse(str(tmp_path))

    metrics_json = await pipeline.run_metrics_evaluation(
        text=text,
        filename=file.filename
    )

    return metrics_json

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
