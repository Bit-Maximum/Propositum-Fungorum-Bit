import json
from io import BytesIO
from pathlib import Path

import requests
from fastapi import FastAPI, UploadFile, APIRouter, Body, HTTPException
import uvicorn
from app.api.parse import PDFParser
from app.pipeline.pipeline import Pipeline
from app.config import settings

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


def upload_json_as_file(data, filename="data.json", base_url="http://localhost:8000"):
    """
    Формирует файл из переменной с данными и отправляет на эндпоинт

    Args:
        data (dict | list | str): Данные для отправки (dict/list или уже сериализованный JSON)
        filename (str): Имя файла для отправки
        base_url (str): Базовый URL сервиса

    Returns:
        dict: Ответ сервера в формате JSON
    """
    url = f"{base_url}{settings.BACKEND_UPLOAD_PATH}"

    # 1. Преобразуем данные в JSON-строку (если это ещё не строка)
    if isinstance(data, (dict, list)):
        json_str = json.dumps(data, ensure_ascii=False)
    else:
        json_str = str(data)

    # 2. Создаём "файл" в памяти из строки
    file_content = json_str.encode('utf-8')
    file_obj = BytesIO(file_content)

    # 3. Отправляем как файл
    files = {
        'file': (filename, file_obj, 'application/json')
    }

    response = requests.post(
        url,
        files=files,
        timeout=1200  # 20 минут
    )

    response.raise_for_status()
    return response.json()

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

    graph_json = await pipeline.run(file_text, file.filename)

    file_path = upload_json_as_file(
        data=graph_json,
        base_url=settings.BACKEND_HOST,
    )

    try:
        s3_path = file_path["s3_path"]
    except KeyError as e:
        raise HTTPException(
            status_code=400,
        )
    print(s3_path)
    response = requests.post(
        url=f"{settings.BACKEND_HOST}{settings.BACKEND_METADATA_PATH}",
        json={
            "display_name": display_name,
            "subtitle_name": subtitle_name,
            "questionnaire_path": s3_path,
        }
    )
    print(response.json())



    return graph_json

@router.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
