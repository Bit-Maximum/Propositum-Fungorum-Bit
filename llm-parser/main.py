from pathlib import Path
from fastapi import FastAPI, UploadFile, APIRouter
import uvicorn
from app.api.parse import PDFParser
from app.pipeline.pipeline import Pipeline

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
async def parse_pdf(file: UploadFile):
    tmp_path = Path("/tmp") / file.filename
    tmp_path.write_bytes(file.file.read())

    parser = PDFParser()
    global file_text
    file_text = parser.parse(str(tmp_path))

    return await pipeline.run(file_text)

@router.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
