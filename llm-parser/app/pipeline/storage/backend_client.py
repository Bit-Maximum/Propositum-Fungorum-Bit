import json
import logging
import mimetypes
from io import BytesIO

import requests
from app.config import settings
from fastapi import HTTPException
from app.utils.file_processor import FileProcessor

class BackendClient:
    """
    Клиент для работы с S3 полностью в памяти (in-memory).
    """

    def __init__(
        self,
        base_path: str,
    ):
        self.base_path = base_path
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.file_processor = FileProcessor()

    async def upload_file(self, file_obj: BytesIO, filename: str, uuid):
        """
        :param file_obj:
        :param filename:
        :param uuid:
        """
        url = self.settings.BACKEND_HOST + self.settings.BACKEND_UPLOAD_PATH

        full_path = self.base_path + uuid + "/" + filename

        content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

        files = {
            'file': (filename, file_obj, content_type)
        }
        data = {
            'path': full_path
        }

        response = requests.post(url, files=files, data=data)
        response.raise_for_status()
        return response.json()

    async def upload_json_as_file(self, data, uuid: str, filename="data.json"):
        """
        Формирует файл из переменной с данными и отправляет на эндпоинт

        Args:
            data (dict | list | str): Данные для отправки (dict/list или уже сериализованный JSON)
            filename (str): Имя файла для отправки
            uuid: uuid
        Returns:
            dict: Ответ сервера в формате JSON
        """

        # 1. Преобразуем данные в JSON-строку (если это ещё не строка)
        if isinstance(data, (dict, list)):
            json_str = json.dumps(data, ensure_ascii=False)
        else:
            json_str = str(data)

        # 2. Создаём "файл" в памяти из строки
        file_content = json_str.encode('utf-8')
        file_obj = BytesIO(file_content)

        return await self.upload_file(file_obj, filename, uuid)

    async def upload_text_as_file(self, text, uuid: str):

        file_content = text.encode('utf-8')
        file_obj = BytesIO(file_content)

        return await self.upload_file(file_obj, "input.txt", uuid)

    async def upload_step_results_to_s3(self, uuid: str, step_results: dict) -> dict:
        try:
            self.logger.info(f"(S3) Начинаем загружать результаты этапов в S3")

            uploaded_paths = {}

            for step_name, result in step_results.items():
                s3_key = f"{step_name}.json"

                self.logger.info(f"(S3) Загружаем файл {s3_key}")
                byte_io = BytesIO(
                    json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
                )

                await self.upload_file(byte_io, s3_key, uuid)

                uploaded_paths[step_name] = s3_key

            self.logger.info(f"(S3) Загружены файлы: {uploaded_paths}")
            return uploaded_paths

        except Exception as e:
            self.logger.error(f"Ошибка при загрузке файл в S3: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Fucked by stupid"
            )

    async def upload_metadata(self, display_name, subtitle_name):
        response = requests.post(
            url=f"{self.settings.BACKEND_HOST}{self.settings.BACKEND_METADATA_PATH}",
            json={
                "display_name": display_name,
                "subtitle_name": subtitle_name,
            }
        )

        response.raise_for_status()
        return response.json()["result"]


    async def reload_metadata(self):
        response = requests.post(
            url=f"{self.settings.BACKEND_HOST}{self.settings.BACKEND_RELOAD_PATH}",
        )
        response.raise_for_status()

        return response.json()


    async def download_file(self, filename, uuid):
        full_path = self.base_path + uuid + "/" + filename
        response = requests.post(
            url=f"{self.settings.BACKEND_HOST}{self.settings.BACKEND_DOWNLOAD_PATH}",
            json={'path': full_path}
        )

        response.raise_for_status()
        file_bytes = response.content
        content_type = response.headers.get('content-type')

        return self.file_processor.process_file_by_type(file_bytes, content_type)
