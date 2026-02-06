import uuid
from app.s3_client import S3MemoryClient
from app.config import config
import json


class Metadata:
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.s3_config = config
        self.s3_client = S3MemoryClient(
            bucket_name=self.s3_config.bucket_name,
            region_name="us-east-2",
            aws_access_key_id=self.s3_config.minio_user,
            aws_secret_access_key=self.s3_config.minio_password,
            endpoint_url=self.s3_config.minio_endpoint
        )


    def add_entry_in_metadata(self, display_name, subtitle_name):
        if not self.s3_client.object_exists(self.json_path):
            raise FileNotFoundError(f"Файл метадаты не найден: {self.json_path}")

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
            'questionnaire_path': f"data/{json_uuid}/graph.json"
        })

        data_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.s3_client.upload_bytes(data=data_bytes, s3_key=self.json_path)

        return json_uuid
