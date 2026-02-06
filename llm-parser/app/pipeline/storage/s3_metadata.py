import uuid
from .s3_client import S3MemoryClient
from app.config import settings
import json


class Metadata:
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.s3_config = settings
        self.s3_client = S3MemoryClient(
            bucket_name=self.s3_config.MINIO_APP_BUCKET_NAME,
            region_name="us-east-2",
            aws_access_key_id=self.s3_config.MINIO_APP_USER,
            aws_secret_access_key=self.s3_config.MINIO_APP_PASSWORD,
            endpoint_url=self.s3_config.MINIO_APP_ENDPOINT
        )

    def change_metadata(self, display_name, subtitle_name, questionnaire_path):
        if not self.s3_client.object_exists(self.json_path):
            raise FileNotFoundError(f"Файл метадаты не найден: {self.json_path}")

        if not self.s3_client.object_exists(questionnaire_path):
            raise FileNotFoundError(f"Файл опросника не найден: {questionnaire_path}")

        file = self.s3_client.download_bytes(self.json_path)
        data = json.loads(file)

        json_uuid = uuid.uuid4()

        ids = [item['id'] for item in data]

        max_value = -1

        if len(ids) != 0:
            max_value = max(item["value"] for item in data)

        while json_uuid in ids:
            json_uuid = uuid.uuid4()

        data.append({
            'id': str(json_uuid),
            'value': max_value + 1,
            'display_name': display_name,
            'subtitle_name': subtitle_name,
            'questionnaire_path': questionnaire_path
        })

        data_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.s3_client.upload_bytes(data=data_bytes, s3_key=self.json_path)

        return True
