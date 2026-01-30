import json
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.questionnaire import Questionnaire
from app.s3_client import S3MemoryClient
from app.config import config


class QuestionaryMetadata:

    class QuestionTypee:
        def __init__(self, id, value, display_name, subtitle_name, questionnaire_path):
            self.id = id
            self.value = value
            self.display_name = display_name
            self.subtitle_name = subtitle_name
            self.path = questionnaire_path

        def __hash__(self):
            return hash(self.id)

        def __eq__(self, other):
            return self.id == other.id

    def __init__(self, json_name):
        self.json_name = json_name
        self.s3_config = config
        self.s3_client = S3MemoryClient(
            bucket_name=self.s3_config.bucket_name,
            region_name="us-east-2",
            aws_access_key_id=self.s3_config.minio_user,
            aws_secret_access_key=self.s3_config.minio_password,
            endpoint_url=self.s3_config.minio_endpoint
        )
        self.questionary_map = self._generate_map()

    def _load_metadata(self) -> Dict[str, Any]:
        """Загрузить граф из JSON файла"""
        if not self.s3_client.object_exists(self.json_name):
            raise FileNotFoundError(f"Файл опросника не найден: {self.json_name}")

        file = self.s3_client.download_bytes(self.json_name)
        return json.loads(file)

    def _generate_map(self) -> Dict[QuestionType, Questionnaire]:
        metadata = self._load_metadata()
        result = {}
        for question in metadata:
            question_type = self.QuestionTypee(**question)
            result[question_type.id] = (question_type, Questionnaire(question_type.path))
        return result

    def get_question_type_list(self):
        result = []
        for question_type in self.questionary_map.values():
            result.append(question_type[0])

        return result

    def get_question_type(self, question_type: str):
        if question_type in self.questionary_map:
            return self.questionary_map[question_type][0]
        else:
            raise HTTPException(status_code=404, detail=f'Unknown question type {question_type}')


    def get_by_type(self, question_type: str):
        if question_type in self.questionary_map:
            return self.questionary_map[question_type][1]
        else:
            raise HTTPException(status_code=404, detail=f'Unknown question type {question_type}')

    def get_all_display_questionnaires(self) -> list:
        values = []
        for questionnaire in self.questionary_map.values():
            value = {
                "systemName": questionnaire[0].id,
                "displayName": questionnaire[0].display_name,
            }
            values.append(value)

        return values

if __name__ == '__main__':
    metadata = QuestionaryMetadata("data/metadata.json")
    print(metadata.get_all_display_questionnaires())
